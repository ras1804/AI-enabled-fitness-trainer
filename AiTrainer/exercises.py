"""View-invariant rep counters driven by joint angles and hysteresis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from AiTrainer.geometry import (
    LANDMARK,
    best_side_angle,
    curl_metric_robust,
)


class ExerciseType(str, Enum):
    BICEP_CURL = "Bicep Curl"
    SQUAT = "Squat"
    PUSH_UP = "Push-Up"


@dataclass
class ExerciseCounter:
    exercise: ExerciseType
    reps: int = 0
    stage: str = "up"
    metric: float = 0.0
    feedback: str = "Ready — start your set!"
    _stable_frames: int = 0
    _pending_stage: Optional[str] = None

    # Bicep curl: wider band for single-arm / partial frame videos
    CURL_UP: float = 140.0
    CURL_DOWN: float = 65.0
    SQUAT_UP: float = 155.0
    SQUAT_DOWN: float = 95.0
    PUSH_UP_UP: float = 155.0
    PUSH_UP_DOWN: float = 95.0
    STABLE_FRAMES: int = 2

    def reset(self) -> None:
        self.reps = 0
        self.stage = "up"
        self.metric = 0.0
        self.feedback = "Counter reset."
        self._stable_frames = 0
        self._pending_stage = None

    def update(self, landmarks) -> dict:
        if self.exercise == ExerciseType.BICEP_CURL:
            metric = self._curl_metric(landmarks)
        elif self.exercise == ExerciseType.SQUAT:
            metric = self._squat_metric(landmarks)
        else:
            metric = self._pushup_metric(landmarks)

        if metric is None:
            if self.exercise == ExerciseType.BICEP_CURL:
                self.feedback = "Show your curling arm (elbow + wrist) in frame."
            else:
                self.feedback = "Move into frame so key joints are visible."
            return self._snapshot()

        self.metric = metric
        self._apply_hysteresis(metric)
        return self._snapshot()

    def _curl_metric(self, landmarks) -> Optional[float]:
        return curl_metric_robust(landmarks)

    def _squat_metric(self, landmarks) -> Optional[float]:
        knee = best_side_angle(
            landmarks,
            (LANDMARK["left_hip"], LANDMARK["left_knee"], LANDMARK["left_ankle"]),
            (LANDMARK["right_hip"], LANDMARK["right_knee"], LANDMARK["right_ankle"]),
            relaxed=True,
        )
        if knee is not None:
            return knee
        return best_side_angle(
            landmarks,
            (LANDMARK["left_shoulder"], LANDMARK["left_hip"], LANDMARK["left_knee"]),
            (LANDMARK["right_shoulder"], LANDMARK["right_hip"], LANDMARK["right_knee"]),
            relaxed=True,
        )

    def _pushup_metric(self, landmarks) -> Optional[float]:
        elbow = best_side_angle(
            landmarks,
            (
                LANDMARK["left_shoulder"],
                LANDMARK["left_elbow"],
                LANDMARK["left_wrist"],
            ),
            (
                LANDMARK["right_shoulder"],
                LANDMARK["right_elbow"],
                LANDMARK["right_wrist"],
            ),
            relaxed=True,
        )
        if elbow is not None:
            return elbow
        return best_side_angle(
            landmarks,
            (LANDMARK["left_shoulder"], LANDMARK["left_hip"], LANDMARK["left_knee"]),
            (LANDMARK["right_shoulder"], LANDMARK["right_hip"], LANDMARK["right_knee"]),
            relaxed=True,
        )

    def _apply_hysteresis(self, metric: float) -> None:
        if self.exercise == ExerciseType.BICEP_CURL:
            down_th, up_th = self.CURL_DOWN, self.CURL_UP
        elif self.exercise == ExerciseType.SQUAT:
            down_th, up_th = self.SQUAT_DOWN, self.SQUAT_UP
        else:
            down_th, up_th = self.PUSH_UP_DOWN, self.PUSH_UP_UP

        if metric <= down_th:
            target = "down"
            self.feedback = "Curl down — good!"
        elif metric >= up_th:
            target = "up"
            self.feedback = "Arms extended — rep completes on the way up."
        else:
            self.feedback = "Keep moving through full range."
            return

        if target == self._pending_stage:
            self._stable_frames += 1
        else:
            self._pending_stage = target
            self._stable_frames = 1

        if self._stable_frames < self.STABLE_FRAMES:
            return

        if target != self.stage:
            if self.stage == "down" and target == "up":
                self.reps += 1
                self.feedback = f"Rep {self.reps} counted!"
            self.stage = target
        self._pending_stage = None
        self._stable_frames = 0

    def _snapshot(self) -> dict:
        return {
            "reps": self.reps,
            "stage": self.stage,
            "metric": self.metric,
            "feedback": self.feedback,
            "exercise": self.exercise.value,
        }
