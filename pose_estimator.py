"""MediaPipe pose detection wrapper (deployment-safe, no GUI calls)."""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from pose_estimator_module import bgr_to_rgb, draw_pose_landmarks, resize_frame

try:
    import mediapipe as mp
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "mediapipe is required. Install with: pip install -r requirements.txt"
    ) from exc


class PoseEstimator:
    """
    Stateful pose detector. Uses MediaPipe Pose with model_complexity=1
    for a balance of speed and accuracy on Streamlit Cloud and local runs.
    """

    def __init__(
        self,
        min_detection_confidence: float = 0.4,
        min_tracking_confidence: float = 0.4,
        model_complexity: int = 1,
        max_width: int = 640,
    ) -> None:
        self.max_width = max_width
        self._pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            enable_segmentation=False,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def process_frame(self, bgr_frame: np.ndarray) -> Tuple[Optional[object], np.ndarray]:
        """
        Run pose on a BGR frame. Returns (results, annotated_rgb).
        Safe for Streamlit: no imshow, no VideoCapture here.
        """
        if bgr_frame is None or bgr_frame.size == 0:
            return None, bgr_frame

        resized = resize_frame(bgr_frame, self.max_width)
        rgb = bgr_to_rgb(resized)
        results = self._pose.process(rgb)
        annotated = draw_pose_landmarks(rgb, results)
        return results, annotated

    def get_landmarks(self, results):
        if results and results.pose_landmarks:
            return results.pose_landmarks.landmark
        return None

    def close(self) -> None:
        if self._pose is not None:
            self._pose.close()
            self._pose = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
