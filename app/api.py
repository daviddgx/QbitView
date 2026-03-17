from pathlib import Path

import cv2
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas import CameraCreate, CameraOut, EventOut
from app.service import detect_once, get_event, list_cameras, list_events, upsert_camera

app = FastAPI(title="QbitView Smoke & Fire API", version="1.1.0")

app.mount("/snapshots", StaticFiles(directory="data/event_snapshots"), name="snapshots")
app.mount("/web", StaticFiles(directory="web"), name="web")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _event_to_out(event) -> EventOut:
    snapshot_url = f"/{event.snapshot_path}" if event.snapshot_path else None
    return EventOut(
        id=event.id,
        camera_id=event.camera_id,
        event_type=event.event_type,
        severity=event.severity,
        confidence=float(event.confidence),
        message=event.message,
        detector_source=event.detector_source,
        snapshot_path=event.snapshot_path,
        snapshot_url=snapshot_url,
        frame_timestamp=event.frame_timestamp,
    )


@app.get("/")
def dashboard():
    return FileResponse(Path("web/index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/cameras", response_model=CameraOut)
def create_or_update_camera(payload: CameraCreate, db: Session = Depends(get_db)):
    cam = upsert_camera(
        db,
        name=payload.name,
        stream_url=payload.stream_url,
        location=payload.location,
        enabled=payload.enabled,
    )
    return cam


@app.get("/cameras", response_model=list[CameraOut])
def get_cameras(db: Session = Depends(get_db)):
    return list_cameras(db)


@app.post("/monitor/run-once/{camera_id}", response_model=EventOut)
def run_once(camera_id: int, db: Session = Depends(get_db)):
    event = detect_once(db, camera_id=camera_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Sin detección o cámara no disponible")
    return _event_to_out(event)


@app.get("/monitor/stream/{camera_id}")
def stream_camera(camera_id: int, db: Session = Depends(get_db)):
    camera = next((cam for cam in list_cameras(db) if cam.id == camera_id and cam.enabled), None)
    if camera is None:
        raise HTTPException(status_code=404, detail="Cámara no encontrada o inactiva")

    def generate():
        cap = cv2.VideoCapture(camera.stream_url)
        if not cap.isOpened():
            return
        try:
            while True:
                ok, frame = cap.read()
                if not ok or frame is None:
                    break
                ok_enc, buffer = cv2.imencode('.jpg', frame)
                if not ok_enc:
                    continue
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n'
                )
        finally:
            cap.release()

    return StreamingResponse(generate(), media_type='multipart/x-mixed-replace; boundary=frame')


@app.get("/events", response_model=list[EventOut])
def get_events(
    camera_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    events = list_events(db, camera_id=camera_id, limit=limit)
    return [_event_to_out(event) for event in events]


@app.get("/events/{event_id}", response_model=EventOut)
def get_event_detail(event_id: int, db: Session = Depends(get_db)):
    event = get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return _event_to_out(event)
