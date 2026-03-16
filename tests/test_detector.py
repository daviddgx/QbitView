import numpy as np

from app.detector import SmokeFireDetector
from app.models import EventType, Severity


def test_detect_fire_on_red_frame():
    detector = SmokeFireDetector()
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    frame[:, :] = (0, 0, 255)  # rojo en BGR

    result = detector.analyze_frame(frame)

    assert result.detected is True
    assert result.event_type == EventType.FIRE
    assert result.severity == Severity.CRITICA


def test_detect_smoke_on_gray_frame():
    detector = SmokeFireDetector()
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    frame[:, :] = (160, 160, 160)  # gris

    result = detector.analyze_frame(frame)

    assert result.detected is True
    assert result.event_type == EventType.SMOKE
    assert result.severity == Severity.PRE_ALERTA
