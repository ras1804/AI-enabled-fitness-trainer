"""High-level trainer: ties pose estimation to exercise rep counting."""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from AiTrainer.exercises import ExerciseCounter, ExerciseType
from pose_estimator import PoseEstimator
from pose_estimator_module import overlay_stats


class AITrainer:
    def __init__(self, exercise: ExerciseType, max_width: int = 640) -> None:
        self.estimator = PoseEstimator(max_width=max_width)
        self.counter = ExerciseCounter(exercise=exercise)

    def process_bgr_frame(self, bgr_frame: np.ndarray) -> Tuple[np.ndarray, dict]:
        results, annotated_rgb = self.estimator.process_frame(bgr_frame)
        landmarks = self.estimator.get_landmarks(results)
        stats = self.counter.update(landmarks)
        display = overlay_stats(
            annotated_rgb,
            stats["exercise"],
            stats["reps"],
            stats["stage"],
            stats.get("metric", 0.0),
            stats["feedback"],
        )
        return display, stats

    def reset(self) -> None:
        self.counter.reset()

    def close(self) -> None:
        self.estimator.close()


def exercise_from_label(label: str) -> ExerciseType:
    mapping = {
        "bicep curl": ExerciseType.BICEP_CURL,
        "squat": ExerciseType.SQUAT,
        "push-up": ExerciseType.PUSH_UP,
        "push up": ExerciseType.PUSH_UP,
        "pushup": ExerciseType.PUSH_UP,
    }
    key = label.strip().lower()
    if key not in mapping:
        raise ValueError(f"Unknown exercise: {label}")
    return mapping[key]
