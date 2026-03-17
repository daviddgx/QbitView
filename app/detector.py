from dataclasses import dataclass
import os
from pathlib import Path

import cv2
import numpy as np

from app.models import EventType, Severity


@dataclass
class DetectionResult:
    detected: bool
    event_type: EventType | None = None
    severity: Severity | None = None
    confidence: float = 0.0
    message: str = "Sin detección"
    source: str = "none"


class SmokeFireDetector:
    def analyze_frame(self, frame: np.ndarray) -> DetectionResult:
        raise NotImplementedError


class HeuristicSmokeFireDetector(SmokeFireDetector):
    """Fallback detector based on HSV heuristics."""

    def analyze_frame(self, frame: np.ndarray) -> DetectionResult:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        smoke_mask = cv2.inRange(hsv, (0, 0, 80), (180, 70, 255))
        smoke_ratio = float(np.count_nonzero(smoke_mask)) / smoke_mask.size

        fire_mask_1 = cv2.inRange(hsv, (0, 120, 120), (25, 255, 255))
        fire_mask_2 = cv2.inRange(hsv, (160, 120, 120), (179, 255, 255))
        fire_mask = cv2.bitwise_or(fire_mask_1, fire_mask_2)
        fire_ratio = float(np.count_nonzero(fire_mask)) / fire_mask.size

        if fire_ratio > 0.04:
            confidence = min(0.99, fire_ratio * 6)
            return DetectionResult(
                detected=True,
                event_type=EventType.FIRE,
                severity=Severity.CRITICA,
                confidence=round(confidence, 4),
                message="Fuego detectado (heurístico) - ALERTA CRÍTICA",
                source="heuristic",
            )

        if smoke_ratio > 0.20:
            confidence = min(0.95, smoke_ratio * 1.5)
            return DetectionResult(
                detected=True,
                event_type=EventType.SMOKE,
                severity=Severity.PRE_ALERTA,
                confidence=round(confidence, 4),
                message="Humo detectado (heurístico) - PRE ALERTA",
                source="heuristic",
            )

        return DetectionResult(detected=False)


class TrainedModelSmokeFireDetector(SmokeFireDetector):
    """Detector basado en modelo entrenado (YOLO via ultralytics)."""

    FIRE_LABELS = {"fire", "flame", "incendio"}
    SMOKE_LABELS = {"smoke", "humo", "fume"}

    def __init__(self, model_path: str, confidence_threshold: float = 0.35):
        try:
            from ultralytics import YOLO
        except Exception as exc:  # pragma: no cover - depende del entorno
            raise RuntimeError("ultralytics no está instalado") from exc

        model_file = Path(model_path)
        if not model_file.exists():
            raise RuntimeError(f"No se encontró el modelo entrenado en: {model_path}")

        self.model = YOLO(str(model_file))
        self.confidence_threshold = confidence_threshold

    @staticmethod
    def _normalize_label(label: str) -> str:
        return label.strip().lower().replace(" ", "_")

    def _map_label(self, label: str) -> tuple[EventType, Severity] | None:
        normalized = self._normalize_label(label)
        if normalized in self.FIRE_LABELS:
            return EventType.FIRE, Severity.CRITICA
        if normalized in self.SMOKE_LABELS:
            return EventType.SMOKE, Severity.PRE_ALERTA
        return None

    def analyze_frame(self, frame: np.ndarray) -> DetectionResult:
        predictions = self.model.predict(frame, conf=self.confidence_threshold, verbose=False)
        if not predictions:
            return DetectionResult(detected=False)

        best: DetectionResult | None = None
        prediction = predictions[0]
        names = prediction.names if hasattr(prediction, "names") else {}

        for box in prediction.boxes:
            conf = float(box.conf.item())
            cls_idx = int(box.cls.item())
            label = str(names.get(cls_idx, cls_idx))
            mapped = self._map_label(label)
            if mapped is None:
                continue

            event_type, severity = mapped
            candidate = DetectionResult(
                detected=True,
                event_type=event_type,
                severity=severity,
                confidence=round(conf, 4),
                message=f"{label.upper()} detectado (modelo entrenado)",
                source="trained_model",
            )

            if best is None or candidate.confidence > best.confidence:
                best = candidate

        return best if best else DetectionResult(detected=False)


def build_detector() -> SmokeFireDetector:
    model_path = os.getenv("DETECTION_MODEL_PATH", "models/fire_smoke.pt")
    confidence = float(os.getenv("DETECTION_CONFIDENCE", "0.35"))
    allow_fallback = os.getenv("DETECTION_ALLOW_HEURISTIC_FALLBACK", "true").lower() == "true"

    try:
        return TrainedModelSmokeFireDetector(model_path=model_path, confidence_threshold=confidence)
    except RuntimeError:
        if allow_fallback:
            return HeuristicSmokeFireDetector()
        raise
