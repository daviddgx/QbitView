from dataclasses import dataclass

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


class SmokeFireDetector:
    """Detector heurístico simple para humo/fuego."""

    def analyze_frame(self, frame: np.ndarray) -> DetectionResult:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Humo: baja saturación + brillo medio/alto (grisáceo / neblina)
        smoke_mask = cv2.inRange(hsv, (0, 0, 80), (180, 70, 255))
        smoke_ratio = float(np.count_nonzero(smoke_mask)) / smoke_mask.size

        # Fuego: tonos rojo/naranja/amarillo brillantes
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
                message="Fuego detectado - ALERTA CRÍTICA",
            )

        if smoke_ratio > 0.20:
            confidence = min(0.95, smoke_ratio * 1.5)
            return DetectionResult(
                detected=True,
                event_type=EventType.SMOKE,
                severity=Severity.PRE_ALERTA,
                confidence=round(confidence, 4),
                message="Humo detectado - PRE ALERTA",
            )

        return DetectionResult(detected=False)
