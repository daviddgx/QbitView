from datetime import datetime

import cv2
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.detector import SmokeFireDetector
from app.models import Camera, Event


detector = SmokeFireDetector()


def upsert_camera(db: Session, name: str, stream_url: str, location: str | None, enabled: bool) -> Camera:
    camera = db.execute(select(Camera).where(Camera.name == name)).scalar_one_or_none()
    if camera is None:
        camera = Camera(name=name, stream_url=stream_url, location=location, enabled=enabled)
        db.add(camera)
    else:
        camera.stream_url = stream_url
        camera.location = location
        camera.enabled = enabled
    db.commit()
    db.refresh(camera)
    return camera


def list_cameras(db: Session) -> list[Camera]:
    return list(db.execute(select(Camera).order_by(Camera.id.desc())).scalars())


def list_events(db: Session, camera_id: int | None = None, limit: int = 50) -> list[Event]:
    stmt = select(Event).order_by(Event.created_at.desc()).limit(limit)
    if camera_id:
        stmt = stmt.where(Event.camera_id == camera_id)
    return list(db.execute(stmt).scalars())


def detect_once(db: Session, camera_id: int, sample_frames: int = 15) -> Event | None:
    camera = db.get(Camera, camera_id)
    if not camera or not camera.enabled:
        return None

    cap = cv2.VideoCapture(camera.stream_url)
    if not cap.isOpened():
        return None

    best_detection = None
    best_confidence = 0.0

    try:
        for _ in range(sample_frames):
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            detection = detector.analyze_frame(frame)
            if detection.detected and detection.confidence > best_confidence:
                best_detection = detection
                best_confidence = detection.confidence
    finally:
        cap.release()

    if best_detection is None:
        return None

    event = Event(
        camera_id=camera_id,
        event_type=best_detection.event_type,
        severity=best_detection.severity,
        confidence=best_detection.confidence,
        message=best_detection.message,
        frame_timestamp=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
