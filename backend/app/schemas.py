from datetime import datetime
from pydantic import BaseModel, Field


class SensorCreate(BaseModel):
    name: str
    corridor: str
    latitude: float
    longitude: float


class SensorOut(SensorCreate):
    id: int
    class Config:
        from_attributes = True


class ReadingIn(BaseModel):
    sensor_id: int
    rainfall_mm: float = Field(ge=0, le=500)
    soil_moisture_pct: float = Field(ge=0, le=100)
    displacement_mm: float = Field(ge=0)
    pore_pressure_kpa: float = Field(ge=0, le=200)
    slope_angle_deg: float = Field(ge=0, le=90)


class ReadingOut(BaseModel):
    id: int
    sensor_id: int
    timestamp: datetime
    rainfall_mm: float
    soil_moisture_pct: float
    displacement_mm: float
    pore_pressure_kpa: float
    slope_angle_deg: float
    risk_label: str | None
    risk_probability: float | None
    top_factors: str | None

    class Config:
        from_attributes = True


class AlertIn(BaseModel):
    sensor_id: int | None = None
    level: str
    message_en: str
    message_hi: str | None = None
    message_as: str | None = None
    issued_by: str = "officer"


class AlertOut(AlertIn):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


class SOSIn(BaseModel):
    latitude: float
    longitude: float
    note: str | None = None
    contact: str | None = None


class SOSOut(SOSIn):
    id: int
    status: str
    created_at: datetime
    class Config:
        from_attributes = True
