import numpy as np

from app.detector import HeuristicSmokeFireDetector, TrainedModelSmokeFireDetector
from app.models import EventType, Severity


def test_detect_fire_on_red_frame_with_heuristic():
    detector = HeuristicSmokeFireDetector()
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    frame[:, :] = (0, 0, 255)

    result = detector.analyze_frame(frame)

    assert result.detected is True
    assert result.event_type == EventType.FIRE
    assert result.severity == Severity.CRITICA


def test_detect_smoke_on_gray_frame_with_heuristic():
    detector = HeuristicSmokeFireDetector()
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    frame[:, :] = (160, 160, 160)

    result = detector.analyze_frame(frame)

    assert result.detected is True
    assert result.event_type == EventType.SMOKE
    assert result.severity == Severity.PRE_ALERTA


def test_model_label_mapping():
    detector = TrainedModelSmokeFireDetector.__new__(TrainedModelSmokeFireDetector)

    assert detector._map_label("fire") == (EventType.FIRE, Severity.CRITICA)
    assert detector._map_label("smoke") == (EventType.SMOKE, Severity.PRE_ALERTA)
    assert detector._map_label("person") is None
