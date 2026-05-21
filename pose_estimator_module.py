"""Low-level pose drawing and frame conversion helpers."""

from __future__ import annotations

import cv2
import mediapipe as mp
import numpy as np

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Consistent styling across exercises
LANDMARK_STYLE = mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
CONNECTION_STYLE = mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=2)


def bgr_to_rgb(frame: np.ndarray) -> np.ndarray:
    if frame is None or frame.size == 0:
        return frame
    if len(frame.shape) == 2:
        return cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def rgb_to_bgr(frame: np.ndarray) -> np.ndarray:
    if frame is None or frame.size == 0:
        return frame
    if len(frame.shape) == 2:
        return frame
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)


def resize_frame(frame: np.ndarray, max_width: int = 640) -> np.ndarray:
    """Downscale for faster inference; aspect ratio preserved."""
    if frame is None or frame.size == 0:
        return frame
    h, w = frame.shape[:2]
    if w <= max_width:
        return frame
    scale = max_width / float(w)
    new_size = (max_width, int(h * scale))
    return cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)


def draw_pose_landmarks(
    rgb_frame: np.ndarray,
    results,
) -> np.ndarray:
    """Draw skeleton on a copy of the RGB frame."""
    annotated = rgb_frame.copy()
    if results and results.pose_landmarks:
        mp_drawing.draw_landmarks(
            annotated,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            LANDMARK_STYLE,
            CONNECTION_STYLE,
        )
    return annotated


def overlay_stats(
    frame: np.ndarray,
    exercise: str,
    reps: int,
    stage: str,
    metric: float,
    feedback: str,
) -> np.ndarray:
    """Burn in rep stats for video export and clearer live preview."""
    out = frame.copy()
    lines = [
        f"Exercise: {exercise}",
        f"Reps: {reps}",
        f"Phase: {stage}",
        f"Angle: {metric:.1f}" if metric and metric > 0 else "Angle: --",
        feedback[:60],
    ]
    y = 30
    for line in lines:
        cv2.putText(
            out,
            line,
            (12, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
        y += 28
    return out
