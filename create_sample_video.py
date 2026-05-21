"""Generate skipping.mp4 sample clip for demo mode. Run: python create_sample_video.py"""

from pathlib import Path

import cv2
import numpy as np

OUTPUT = Path(__file__).parent / "skipping.mp4"
W, H, FPS, SECONDS = 640, 480, 24, 3


def main() -> None:
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(OUTPUT), fourcc, FPS, (W, H))
    total = FPS * SECONDS
    for i in range(total):
        frame = np.zeros((H, W, 3), dtype=np.uint8)
        frame[:] = (30, 30, 40)
        # Simple animated bar (placeholder demo video)
        x = int((i / total) * (W - 80))
        cv2.rectangle(frame, (x, H // 2 - 40), (x + 80, H // 2 + 40), (0, 200, 100), -1)
        cv2.putText(
            frame,
            "AI Fitness Trainer - sample clip",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        writer.write(frame)
    writer.release()
    print(f"Created {OUTPUT} ({total} frames)")


if __name__ == "__main__":
    main()
