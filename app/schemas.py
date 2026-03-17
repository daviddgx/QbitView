from datetime import datetime

from pydantic import BaseModel, Field

from app.models import EventType, Severity


class CameraCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    stream_url: str = Field(min_length=5)
    location: str | None = None
    enabled: bool = True


class CameraOut(BaseModel):
    id: int
    name: str
    stream_url: str
    location: str | None
    enabled: bool

    class Config:
        from_attributes = True


class EventOut(BaseModel):
    id: int
    camera_id: int
    event_type: EventType
    severity: Severity
    confidence: float
    message: str
    detector_source: str
    snapshot_path: str | None
    snapshot_url: str | None = None
    frame_timestamp: datetime

    class Config:
        from_attributes = True
