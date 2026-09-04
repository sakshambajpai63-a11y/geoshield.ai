"""
GeoShield AI backend.

Endpoints:
  POST /sensors                 register a sensor node
  GET  /sensors                 list sensor nodes
  POST /readings                ingest one telemetry sample -> scores risk -> broadcasts
  GET  /readings/latest         latest reading per sensor (feeds the live risk map)
  GET  /readings/{sensor_id}    history for one sensor (for trend charts)
  POST /alerts                  officer-issued (or system) broadcast
  GET  /alerts                  recent alerts (citizen feed)
  POST /sos                     citizen SOS with geolocation
  GET  /sos                     open SOS reports (officer console)
  PATCH /sos/{id}                update SOS status
  WS   /ws                      live telemetry / alert / SOS stream

Run: uvicorn app.main:app --reload --port 8000
"""
import json
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

from . import models, schemas
from .database import engine, get_db, Base
from .risk_engine import predict_risk
from .ws_manager import manager

Base.metadata.create_all(bind=engine)

app = FastAPI(title="GeoShield AI API", version="0.1.0")

# In a hackathon demo the frontend origin isn't known ahead of time — lock this
# down to your actual deployed frontend URL before submitting/production use.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow()}


# ---------- Sensors ----------

@app.post("/sensors", response_model=schemas.SensorOut)
def create_sensor(sensor: schemas.SensorCreate, db: Session = Depends(get_db)):
    obj = models.Sensor(**sensor.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/sensors", response_model=list[schemas.SensorOut])
def list_sensors(db: Session = Depends(get_db)):
    return db.query(models.Sensor).all()


# ---------- Readings / risk scoring ----------

@app.post("/readings", response_model=schemas.ReadingOut)
async def ingest_reading(reading: schemas.ReadingIn, db: Session = Depends(get_db)):
    sensor = db.query(models.Sensor).filter(models.Sensor.id == reading.sensor_id).first()
    if not sensor:
        raise HTTPException(404, "Unknown sensor_id — register it via POST /sensors first")

    label, probability, top_factors = predict_risk(
        rainfall_mm=reading.rainfall_mm,
        soil_moisture_pct=reading.soil_moisture_pct,
        displacement_mm=reading.displacement_mm,
        pore_pressure_kpa=reading.pore_pressure_kpa,
        slope_angle_deg=reading.slope_angle_deg,
    )

    obj = models.Reading(
        **reading.model_dump(),
        risk_label=label,
        risk_probability=probability,
        top_factors=json.dumps(top_factors),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)

    # Auto-alert on Warning/Danger so the citizen feed reacts without an officer in the loop
    if label in ("Warning", "Danger"):
        alert = models.Alert(
            sensor_id=sensor.id,
            level=label,
            message_en=f"{label} level risk detected near {sensor.name} ({sensor.corridor}). "
                        f"Avoid the area; check the app for a safe alternate route.",
            issued_by="system",
        )
        db.add(alert)
        db.commit()
        await manager.broadcast("alert", {
            "id": alert.id, "sensor_id": sensor.id, "sensor_name": sensor.name,
            "corridor": sensor.corridor, "level": label, "message_en": alert.message_en,
           "created_at": str(alert.created_at), "issued_by": alert.issued_by,
        })

    await manager.broadcast("reading", {
        "sensor_id": sensor.id,
        "sensor_name": sensor.name,
        "latitude": sensor.latitude,
        "longitude": sensor.longitude,
        "risk_label": label,
        "risk_probability": probability,
        "top_factors": top_factors,
        "timestamp": obj.timestamp,
    })

    return obj


@app.get("/readings/latest")
def latest_readings(db: Session = Depends(get_db)):
    """One row per sensor — the payload the Leaflet map polls/subscribes to."""
    sensors = db.query(models.Sensor).all()
    out = []
    for s in sensors:
        r = (
            db.query(models.Reading)
            .filter(models.Reading.sensor_id == s.id)
            .order_by(desc(models.Reading.timestamp))
            .first()
        )
        out.append({
            "sensor_id": s.id,
            "name": s.name,
            "corridor": s.corridor,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "risk_label": r.risk_label if r else "Unknown",
            "risk_probability": r.risk_probability if r else None,
            "top_factors": json.loads(r.top_factors) if r and r.top_factors else [],
            "last_updated": r.timestamp if r else None,
        })
    return out


@app.get("/readings/{sensor_id}", response_model=list[schemas.ReadingOut])
def sensor_history(sensor_id: int, hours: int = 24, db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(hours=hours)
    return (
        db.query(models.Reading)
        .filter(models.Reading.sensor_id == sensor_id, models.Reading.timestamp >= since)
        .order_by(models.Reading.timestamp)
        .all()
    )


# ---------- Alerts ----------

@app.post("/alerts", response_model=schemas.AlertOut)
async def create_alert(alert: schemas.AlertIn, db: Session = Depends(get_db)):
    obj = models.Alert(**alert.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    await manager.broadcast("alert", schemas.AlertOut.model_validate(obj).model_dump())
    return obj


@app.get("/alerts", response_model=list[schemas.AlertOut])
def list_alerts(limit: int = 20, db: Session = Depends(get_db)):
    return (
        db.query(models.Alert)
        .order_by(desc(models.Alert.created_at))
        .limit(limit)
        .all()
    )


# ---------- SOS ----------

@app.post("/sos", response_model=schemas.SOSOut)
async def create_sos(sos: schemas.SOSIn, db: Session = Depends(get_db)):
    obj = models.SOSReport(**sos.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    await manager.broadcast("sos", schemas.SOSOut.model_validate(obj).model_dump())
    return obj


@app.get("/sos", response_model=list[schemas.SOSOut])
def list_sos(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.SOSReport)
    if status:
        q = q.filter(models.SOSReport.status == status)
    return q.order_by(desc(models.SOSReport.created_at)).all()


@app.patch("/sos/{sos_id}", response_model=schemas.SOSOut)
def update_sos(sos_id: int, status: str, db: Session = Depends(get_db)):
    obj = db.query(models.SOSReport).filter(models.SOSReport.id == sos_id).first()
    if not obj:
        raise HTTPException(404, "SOS report not found")
    obj.status = status
    db.commit()
    db.refresh(obj)
    return obj


# ---------- WebSocket ----------

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # clients don't need to send anything; keeps connection open
    except WebSocketDisconnect:
        manager.disconnect(ws)
