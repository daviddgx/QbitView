from datetime import datetime
from pathlib import Path

import cv2
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.detector import build_detector
from app.models import Camera, Event


detector = build_detector()
SNAPSHOT_DIR = Path("data/event_snapshots")


def _save_snapshot(frame, camera_id: int, event_type: str) -> str | None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    file_name = f"camera_{camera_id}_{event_type.lower()}_{timestamp}.jpg"
    file_path = SNAPSHOT_DIR / file_name
    ok = cv2.imwrite(str(file_path), frame)
    if not ok:
        return None
    return str(file_path)


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


def get_event(db: Session, event_id: int) -> Event | None:
    return db.get(Event, event_id)


def detect_once(db: Session, camera_id: int, sample_frames: int = 15) -> Event | None:
    camera = db.get(Camera, camera_id)
    if not camera or not camera.enabled:
        return None

    cap = cv2.VideoCapture(camera.stream_url)
    if not cap.isOpened():
        return None

    best_detection = None
    best_frame = None
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
                best_frame = frame.copy()
    finally:
        cap.release()

    if best_detection is None:
        return None

    snapshot_path = None
    if best_frame is not None:
        snapshot_path = _save_snapshot(best_frame, camera_id, best_detection.event_type.value)

    event = Event(
        camera_id=camera_id,
        event_type=best_detection.event_type,
        severity=best_detection.severity,
        confidence=best_detection.confidence,
        message=best_detection.message,
        detector_source=best_detection.source,
        snapshot_path=snapshot_path,
        frame_timestamp=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
