# Sistema de identificación de Humo y Fuego (Python + MySQL + Cámara IP)

Sistema completo para:

- Configurar cámaras IP en MySQL.
- Detectar **Humo** como **PRE_ALERTA** y **Fuego** como **CRITICA**.
- Guardar eventos detectados con foto (`snapshot`) en MySQL.
- Visualizar en una interfaz web el stream de cámara, eventos y detalle de evento con imagen.

## Motor de detección

La detección principal usa un **modelo entrenado YOLO** (Ultralytics).

- `DETECTION_MODEL_PATH` (default `models/fire_smoke.pt`)
- `DETECTION_CONFIDENCE` (default `0.35`)
- `DETECTION_ALLOW_HEURISTIC_FALLBACK=true|false`

Si no hay modelo y el fallback está en `true`, se usa detector heurístico.

## Requisitos

- Python 3.10+
- MySQL 8+
- FFmpeg/OpenCV con soporte para RTSP

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Base de datos

1. Crear DB (ej. `qbitview`).
2. Ejecutar `db/schema.sql`.
3. Variables:

```bash
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=tu_password
export MYSQL_DB=qbitview
```

## Modelo entrenado

```bash
export DETECTION_MODEL_PATH=models/fire_smoke.pt
export DETECTION_CONFIDENCE=0.35
export DETECTION_ALLOW_HEURISTIC_FALLBACK=true
```

## Ejecutar API + Dashboard

```bash
uvicorn app.api:app --reload --port 8000
```

Abrir en navegador: `http://localhost:8000/`

## API principal

- `POST /cameras`
- `GET /cameras`
- `POST /monitor/run-once/{camera_id}`
- `GET /monitor/stream/{camera_id}` (stream MJPEG)
- `GET /events`
- `GET /events/{event_id}`

## Guardado de alertas

- Humo: `event_type = SMOKE`, `severity = PRE_ALERTA`
- Fuego: `event_type = FIRE`, `severity = CRITICA`

Cada evento guarda:
- confianza
- fuente de detector (`trained_model` o `heuristic`)
- `snapshot_path` (foto del evento)
