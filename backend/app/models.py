"""
Core data model:
- Sensor: a geotechnical monitoring node (real or simulated) with a fixed location.
- Reading: one telemetry sample from a sensor (rainfall, soil moisture, displacement,
  pore pressure, slope angle) plus the ML risk score computed for it.
- Alert: a broadcast (auto or officer-issued) tied to a risk event.
- SOSReport: a citizen-triggered emergency signal with location.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    corridor = Column(String, nullable=False)  # e.g. "NH-10 Sikkim"
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    installed_at = Column(DateTime, default=datetime.utcnow)

    readings = relationship("Reading", back_populates="sensor")


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    rainfall_mm = Column(Float, nullable=False)
    soil_moisture_pct = Column(Float, nullable=False)
    displacement_mm = Column(Float, nullable=False)
    pore_pressure_kpa = Column(Float, nullable=False)
    slope_angle_deg = Column(Float, nullable=False)

    risk_label = Column(String, nullable=True)     # Safe / Watch / Warning / Danger
    risk_probability = Column(Float, nullable=True)
    top_factors = Column(Text, nullable=True)       # JSON string of SHAP top factors

    sensor = relationship("Sensor", back_populates="readings")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=True)
    level = Column(String, nullable=False)          # Watch / Warning / Danger
    message_en = Column(Text, nullable=False)
    message_hi = Column(Text, nullable=True)
    message_as = Column(Text, nullable=True)
    issued_by = Column(String, default="system")     # "system" or officer username
    created_at = Column(DateTime, default=datetime.utcnow)


class SOSReport(Base):
    __tablename__ = "sos_reports"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    note = Column(Text, nullable=True)
    contact = Column(String, nullable=True)
    status = Column(String, default="open")          # open / acknowledged / resolved
    created_at = Column(DateTime, default=datetime.utcnow)
