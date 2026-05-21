"""
Dependency and smoke test — run before deploy:
    python test.py
"""

from __future__ import annotations

import importlib
import sys


def check_import(name: str, pip_name: str | None = None) -> bool:
    pip_name = pip_name or name
    try:
        importlib.import_module(name)
        print(f"[OK] {pip_name}")
        return True
    except ImportError as exc:
        print(f"[FAIL] {pip_name}: {exc}")
        return False


def check_opencv_headless() -> bool:
    try:
        import cv2

        build = cv2.getBuildInformation()
        if "GUI" in build and "NONE" not in build.upper():
            print("[WARN] OpenCV may include GUI; prefer opencv-python-headless on servers.")
        print(f"[OK] OpenCV {cv2.__version__}")
        return True
    except Exception as exc:
        print(f"[FAIL] OpenCV: {exc}")
        return False


def check_mediapipe_pose() -> bool:
    try:
        import mediapipe as mp

        _ = mp.solutions.pose.Pose(static_image_mode=True)
        print(f"[OK] MediaPipe {mp.__version__} (pose solution)")
        return True
    except Exception as exc:
        print(f"[FAIL] MediaPipe pose: {exc}")
        return False


def check_geometry() -> bool:
    try:
        from AiTrainer.geometry import calculate_angle

        class P:
            def __init__(self, x, y):
                self.x, self.y = x, y

        angle = calculate_angle(P(1, 0), P(0, 0), P(0, 1))
        assert 85 < angle < 95, f"expected ~90°, got {angle}"
        print("[OK] Angle math")
        return True
    except Exception as exc:
        print(f"[FAIL] geometry: {exc}")
        return False


def check_trainer_smoke() -> bool:
    try:
        import numpy as np
        from ai_trainer import AITrainer
        from AiTrainer.exercises import ExerciseType

        trainer = AITrainer(ExerciseType.SQUAT)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        trainer.process_bgr_frame(frame)
        trainer.close()
        print("[OK] Trainer smoke (blank frame)")
        return True
    except Exception as exc:
        print(f"[FAIL] trainer smoke: {exc}")
        return False


def check_streamlit_version() -> bool:
    try:
        import streamlit as st

        ver = st.__version__
        major, minor = (int(x) for x in ver.split(".")[:2])
        if major < 1 or (major == 1 and minor < 32):
            print(f"[WARN] Streamlit {ver} — recommend >= 1.32 for camera_input stability")
        else:
            print(f"[OK] Streamlit {ver}")
        return True
    except Exception as exc:
        print(f"[FAIL] Streamlit: {exc}")
        return False


def main() -> int:
    print("AI Fitness Trainer — dependency check\n")
    checks = [
        check_import("numpy"),
        check_import("pandas"),
        check_import("dotenv", "python-dotenv"),
        check_import("google.generativeai", "google-generativeai"),
        check_streamlit_version(),
        check_opencv_headless(),
        check_mediapipe_pose(),
        check_geometry(),
        check_trainer_smoke(),
    ]
    ok = all(checks)
    print("\n" + ("All checks passed." if ok else "Some checks failed."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
