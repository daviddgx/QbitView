from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas import CameraCreate, CameraOut, EventOut
from app.service import detect_once, list_cameras, list_events, upsert_camera

app = FastAPI(title="QbitView Smoke & Fire API", version="1.0.0")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


@app.post("/monitor/run-once/{camera_id}", response_model=EventOut | None)
def run_once(camera_id: int, db: Session = Depends(get_db)):
    event = detect_once(db, camera_id=camera_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Sin detección o cámara no disponible")
    return event


@app.get("/events", response_model=list[EventOut])
def get_events(
    camera_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_events(db, camera_id=camera_id, limit=limit)
