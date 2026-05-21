"""Angle and visibility helpers for view-invariant rep counting."""

from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

import numpy as np

LANDMARK = {
    "nose": 0,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
}

MIN_VISIBILITY = 0.5
RELAXED_VISIBILITY = 0.25
ARM_CORE_VISIBILITY = 0.35


def _to_xy(landmark) -> np.ndarray:
    return np.array([landmark.x, landmark.y], dtype=np.float64)


def _visibility(landmark) -> float:
    vis = getattr(landmark, "visibility", None)
    return 1.0 if vis is None else float(vis)


def calculate_angle(a, b, c) -> float:
    ba = _to_xy(a) - _to_xy(b)
    bc = _to_xy(c) - _to_xy(b)
    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)
    if norm_ba < 1e-6 or norm_bc < 1e-6:
        return float("nan")
    cosine = np.clip(np.dot(ba, bc) / (norm_ba * norm_bc), -1.0, 1.0)
    return float(math.degrees(math.acos(cosine)))


def landmark_visible(landmark, min_visibility: float = MIN_VISIBILITY) -> bool:
    return _visibility(landmark) >= min_visibility


def angle_if_visible(
    landmarks,
    i_a: int,
    i_b: int,
    i_c: int,
    min_vis: float = MIN_VISIBILITY,
) -> Optional[float]:
    if not landmarks or len(landmarks) <= max(i_a, i_b, i_c):
        return None
    a, b, c = landmarks[i_a], landmarks[i_b], landmarks[i_c]
    if not all(landmark_visible(x, min_vis) for x in (a, b, c)):
        return None
    angle = calculate_angle(a, b, c)
    return None if math.isnan(angle) else angle


def angle_if_visible_relaxed(
    landmarks,
    i_a: int,
    i_b: int,
    i_c: int,
) -> Optional[float]:
    """
    Elbow (b) and wrist (c) must be fairly visible; shoulder (a) can be weak.
    For clips showing only one arm in frame.
    """
    if not landmarks or len(landmarks) <= max(i_a, i_b, i_c):
        return None
    a, b, c = landmarks[i_a], landmarks[i_b], landmarks[i_c]
    if not landmark_visible(b, ARM_CORE_VISIBILITY) or not landmark_visible(c, ARM_CORE_VISIBILITY):
        return None
    if not landmark_visible(a, RELAXED_VISIBILITY):
        return elbow_flexion_vs_vertical(landmarks, i_b, i_c)
    angle = calculate_angle(a, b, c)
    return None if math.isnan(angle) else angle


def elbow_flexion_vs_vertical(landmarks, elbow_idx: int, wrist_idx: int) -> Optional[float]:
    """Fallback when shoulder is off-screen: measure bend at elbow vs image-up."""
    if not landmarks or len(landmarks) <= max(elbow_idx, wrist_idx):
        return None
    elbow, wrist = landmarks[elbow_idx], landmarks[wrist_idx]
    if not landmark_visible(elbow, ARM_CORE_VISIBILITY) or not landmark_visible(wrist, ARM_CORE_VISIBILITY):
        return None
    forearm = _to_xy(wrist) - _to_xy(elbow)
    if np.linalg.norm(forearm) < 1e-6:
        return None
    # Image y grows downward; "up" is negative y
    up = np.array([0.0, -1.0])
    cosine = np.clip(np.dot(forearm, up) / np.linalg.norm(forearm), -1.0, 1.0)
    # Map to same scale as elbow joint angle (~extended 160, flexed 40)
    return float(90 + math.degrees(math.acos(cosine)))


def arm_span_ratio_metric(landmarks, shoulder_idx: int, elbow_idx: int, wrist_idx: int) -> Optional[float]:
    """
    Distance-ratio metric for partial arm visibility.
    Mapped into degrees so the same hysteresis logic applies.
    """
    if not landmarks or len(landmarks) <= max(shoulder_idx, elbow_idx, wrist_idx):
        return None
    s, e, w = landmarks[shoulder_idx], landmarks[elbow_idx], landmarks[wrist_idx]
    if not landmark_visible(e, ARM_CORE_VISIBILITY) or not landmark_visible(w, ARM_CORE_VISIBILITY):
        return None
    upper = np.linalg.norm(_to_xy(e) - _to_xy(s)) if landmark_visible(s, RELAXED_VISIBILITY) else 0.08
    forearm = np.linalg.norm(_to_xy(w) - _to_xy(e))
    if upper < 1e-4 and landmark_visible(landmarks[LANDMARK["left_hip"]], RELAXED_VISIBILITY):
        hip = landmarks[LANDMARK["left_hip"] if elbow_idx == LANDMARK["left_elbow"] else LANDMARK["right_hip"]]
        upper = np.linalg.norm(_to_xy(e) - _to_xy(hip))
    total = upper + forearm
    if total < 1e-6:
        return None
    ratio = forearm / total
    # Extended arm ~ higher ratio; curled ~ lower -> map to angle range
    return float(40 + (1.0 - ratio) * 140)


def chain_visibility_score(landmarks, i_a: int, i_b: int, i_c: int) -> float:
    if not landmarks or len(landmarks) <= max(i_a, i_b, i_c):
        return 0.0
    return min(_visibility(landmarks[i_a]), _visibility(landmarks[i_b]), _visibility(landmarks[i_c]))


def best_side_angle(
    landmarks,
    left_triple: Sequence[int],
    right_triple: Sequence[int],
    relaxed: bool = False,
) -> Optional[float]:
    """
    Use the side with the strongest landmark visibility (not an average).
    Averaging breaks when only one arm is in frame (e.g. left-hand curl video).
    """
    fn = angle_if_visible_relaxed if relaxed else angle_if_visible
    scored: List[Tuple[float, float]] = []
    left = fn(landmarks, *left_triple) if relaxed else angle_if_visible(landmarks, *left_triple)
    right = fn(landmarks, *right_triple) if relaxed else angle_if_visible(landmarks, *right_triple)
    if left is not None:
        scored.append((chain_visibility_score(landmarks, *left_triple), left))
    if right is not None:
        scored.append((chain_visibility_score(landmarks, *right_triple), right))
    if not scored:
        return None
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def curl_metric_robust(landmarks) -> Optional[float]:
    """Multiple metrics for bicep curls; pick the strongest signal."""
    if not landmarks:
        return None

    candidates: List[Tuple[float, float]] = []

    for side, (sh, el, wr) in (
        ("left", (LANDMARK["left_shoulder"], LANDMARK["left_elbow"], LANDMARK["left_wrist"])),
        ("right", (LANDMARK["right_shoulder"], LANDMARK["right_elbow"], LANDMARK["right_wrist"])),
    ):
        hip = LANDMARK["left_hip"] if side == "left" else LANDMARK["right_hip"]
        metrics = [
            angle_if_visible_relaxed(landmarks, sh, el, wr),
            angle_if_visible(landmarks, sh, el, wr, MIN_VISIBILITY),
            angle_if_visible_relaxed(landmarks, hip, el, wr),
            arm_span_ratio_metric(landmarks, sh, el, wr),
            elbow_flexion_vs_vertical(landmarks, el, wr),
        ]
        arm_score = _visibility(landmarks[el]) + _visibility(landmarks[wr])
        for val in metrics:
            if val is not None:
                score = max(chain_visibility_score(landmarks, sh, el, wr), arm_score)
                candidates.append((score, val))

    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def hip_midpoint_y(landmarks) -> Optional[float]:
    if not landmarks or len(landmarks) <= LANDMARK["right_hip"]:
        return None
    lh, rh = landmarks[LANDMARK["left_hip"]], landmarks[LANDMARK["right_hip"]]
    if landmark_visible(lh, RELAXED_VISIBILITY) and landmark_visible(rh, RELAXED_VISIBILITY):
        return (lh.y + rh.y) / 2.0
    if landmark_visible(lh, RELAXED_VISIBILITY):
        return lh.y
    if landmark_visible(rh, RELAXED_VISIBILITY):
        return rh.y
    return None


def shoulder_midpoint_y(landmarks) -> Optional[float]:
    if not landmarks or len(landmarks) <= LANDMARK["right_shoulder"]:
        return None
    ls, rs = landmarks[LANDMARK["left_shoulder"]], landmarks[LANDMARK["right_shoulder"]]
    if landmark_visible(ls, RELAXED_VISIBILITY) and landmark_visible(rs, RELAXED_VISIBILITY):
        return (ls.y + rs.y) / 2.0
    if landmark_visible(ls, RELAXED_VISIBILITY):
        return ls.y
    if landmark_visible(rs, RELAXED_VISIBILITY):
        return rs.y
    return None
