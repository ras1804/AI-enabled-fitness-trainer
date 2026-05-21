"""Real-time webcam processing via streamlit-webrtc."""

from __future__ import annotations

import threading
from typing import Optional

import av
import cv2
from streamlit_webrtc import VideoProcessorBase

from ai_trainer import AITrainer, exercise_from_label

# Shared state between Streamlit main thread and WebRTC worker thread
_live_lock = threading.Lock()
_live_config: dict = {
    "exercise": "Bicep Curl",
    "reset": False,
}


def set_live_exercise(exercise_label: str) -> None:
    with _live_lock:
        _live_config["exercise"] = exercise_label
        _live_config.pop("stats", None)


def request_live_reset() -> None:
    with _live_lock:
        _live_config["reset"] = True


def get_live_stats() -> dict:
    with _live_lock:
        return dict(_live_config.get("stats") or {})


class LivePoseProcessor(VideoProcessorBase):
    """Processes each webcam frame and draws pose + rep overlay."""

    def __init__(self) -> None:
        self._trainer: Optional[AITrainer] = None
        self._last_exercise: Optional[str] = None

    def _get_trainer(self) -> AITrainer:
        with _live_lock:
            exercise = _live_config.get("exercise", "Bicep Curl")
            if _live_config.get("reset"):
                if self._trainer is not None:
                    self._trainer.reset()
                _live_config["reset"] = False
        if self._trainer is None or self._last_exercise != exercise:
            if self._trainer is not None:
                self._trainer.close()
            self._trainer = AITrainer(exercise_from_label(exercise))
            self._last_exercise = exercise
        return self._trainer

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        trainer = self._get_trainer()
        rgb_out, stats = trainer.process_bgr_frame(img)
        bgr_out = cv2.cvtColor(rgb_out, cv2.COLOR_RGB2BGR)
        with _live_lock:
            _live_config["stats"] = stats
        return av.VideoFrame.from_ndarray(bgr_out, format="bgr24")
