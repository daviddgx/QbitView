# Sistema de identificación de Humo y Fuego (Python + MySQL + Cámara IP)

Este proyecto implementa un sistema base para:

- Configurar cámaras IP en MySQL.
- Procesar video RTSP/HTTP desde cámaras IP.
- Detectar **Humo** como **PRE_ALERTA**.
- Detectar **Fuego** como **CRITICA**.
- Guardar todos los eventos detectados en MySQL.
- Exponer API REST para administrar cámaras y consultar eventos.

> ⚠️ El detector incluido es heurístico (visión por color/movimiento) para una base funcional rápida.
> Para producción, se recomienda reemplazar por un modelo entrenado (YOLO/SSD/segmentation) especializado en fire/smoke.

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

## Configurar base de datos

1. Crear base de datos en MySQL (ejemplo `qbitview`).
2. Ejecutar script `db/schema.sql`.
3. Configurar variables de entorno:

```bash
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=tu_password
export MYSQL_DB=qbitview
```

## Ejecutar API

```bash
uvicorn app.api:app --reload --port 8000
```

## Endpoints principales

- `POST /cameras` → registrar o actualizar una cámara.
- `GET /cameras` → listar cámaras.
- `POST /monitor/run-once/{camera_id}` → leer una ventana de frames y registrar evento si detecta humo/fuego.
- `GET /events?camera_id=1&limit=50` → consultar eventos.

## Ejemplo de creación de cámara

```bash
curl -X POST http://localhost:8000/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Camara Planta 1",
    "stream_url": "rtsp://usuario:pass@192.168.1.50:554/stream1",
    "location": "Bodega",
    "enabled": true
  }'
```

## Cómo se guardan las alertas

- Si se detecta **humo**: `event_type = SMOKE`, `severity = PRE_ALERTA`
- Si se detecta **fuego**: `event_type = FIRE`, `severity = CRITICA`

Ambas quedan registradas en tabla `events` con timestamp y puntaje de confianza estimado.

## Siguiente paso recomendado

- Sustituir `app/detector.py` por un detector basado en deep learning y ajustar umbrales por entorno real.
