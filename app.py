"""
AI-Powered Fitness Trainer — Streamlit entry point.

- Live webcam: streamlit-webrtc (real-time overlay + rep count)
- Upload video: frame-by-frame live preview while counting
"""

from __future__ import annotations

import os
import tempfile
import time
from datetime import timedelta
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from dotenv import load_dotenv

from ai_trainer import AITrainer, exercise_from_label
from aichatbot import FitnessChatbot
from AiTrainer.exercises import ExerciseType
from live_processor import (
    LivePoseProcessor,
    get_live_stats,
    request_live_reset,
    set_live_exercise,
)

load_dotenv()

APP_TITLE = "AI-Powered Fitness Trainer"
EXERCISES = [e.value for e in ExerciseType]
SAMPLE_VIDEO = Path(__file__).parent / "skipping.mp4"


def init_session_state() -> None:
    defaults = {
        "trainer": None,
        "last_exercise": None,
        "chat_history": [],
        "chatbot": None,
        "total_reps_session": 0,
        "workout_active": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def get_api_key() -> str:
    try:
        if hasattr(st, "secrets") and st.secrets.get("GOOGLE_API_KEY"):
            return str(st.secrets["GOOGLE_API_KEY"])
    except Exception:
        pass
    return os.getenv("GOOGLE_API_KEY", "").strip()


def get_chatbot() -> FitnessChatbot:
    if st.session_state.chatbot is None:
        st.session_state.chatbot = FitnessChatbot(api_key=get_api_key())
    return st.session_state.chatbot


def ensure_trainer(exercise_label: str) -> AITrainer:
    if (
        st.session_state.trainer is None
        or st.session_state.last_exercise != exercise_label
    ):
        if st.session_state.trainer is not None:
            st.session_state.trainer.close()
        st.session_state.trainer = AITrainer(exercise_from_label(exercise_label))
        st.session_state.last_exercise = exercise_label
    return st.session_state.trainer


def render_header() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🏋️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title(f"🏋️ {APP_TITLE}")
    st.caption(
        "Live pose overlay · Single-arm & multi-angle rep counting · Gemini fitness chat"
    )


def process_bgr_frame(trainer: AITrainer, bgr: np.ndarray):
    rgb_display, stats = trainer.process_bgr_frame(bgr)
    st.session_state.total_reps_session = stats["reps"]
    return rgb_display, stats


def _format_metric(metric: float) -> str:
    if metric and metric > 0:
        return f"{metric:.1f}°"
    return "--"


def process_uploaded_video_live(
    trainer: AITrainer,
    video_bytes: bytes,
    frame_slot,
    metrics_slot,
    live_preview: bool = True,
) -> None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name

    cap = cv2.VideoCapture(tmp_path)
    if not cap.isOpened():
        st.error("Could not open video. Try MP4 (H.264) or MOV format.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    delay = 1.0 / fps if live_preview and fps > 0 else 0
    progress = st.progress(0.0, text="Playing & counting reps…")
    frame_idx = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        rgb_display, stats = process_bgr_frame(trainer, frame)

        if live_preview:
            frame_slot.image(rgb_display, channels="RGB", use_container_width=True)
            metrics_slot.markdown(
                f"**Reps:** {stats['reps']}  ·  **Phase:** {stats['stage']}  ·  "
                f"**Angle:** {_format_metric(stats['metric'])}  ·  {stats['feedback']}"
            )
            if frame_count > 0:
                progress.progress(
                    frame_idx / frame_count,
                    text=f"Frame {frame_idx}/{frame_count} · Reps: {stats['reps']}",
                )
            if delay > 0:
                time.sleep(delay * 0.5)  # slightly faster than real-time

    cap.release()
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    progress.empty()
    st.success(f"Finished — total reps: {st.session_state.total_reps_session}")


def run_live_webcam(exercise: str, frame_slot, metrics_slot) -> None:
    set_live_exercise(exercise)
    try:
        from streamlit_webrtc import webrtc_streamer
    except ImportError:
        st.error("Install streamlit-webrtc: `pip install streamlit-webrtc av`")
        return

    st.markdown("**Live webcam** — allow camera access. Reps update on the video in real time.")

    ctx = webrtc_streamer(
        key="live-workout",
        video_processor_factory=LivePoseProcessor,
        media_stream_constraints={"video": True, "audio": False},
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        async_processing=True,
    )

    @st.fragment(run_every=timedelta(seconds=0.4))
    def _poll_live_metrics() -> None:
        if not ctx.state.playing:
            metrics_slot.caption("Click **Start** on the video player above to begin live tracking.")
            return
        stats = get_live_stats()
        if stats:
            st.session_state.total_reps_session = stats.get("reps", 0)
            metrics_slot.markdown(
                f"**Reps:** {stats.get('reps', 0)}  ·  **Phase:** {stats.get('stage', '—')}  ·  "
                f"**Angle:** {_format_metric(stats.get('metric', 0))}  ·  {stats.get('feedback', '')}"
            )

    _poll_live_metrics()


def trainer_tab() -> None:
    col_cfg, col_view = st.columns([1, 2], gap="large")

    with col_cfg:
        st.subheader("Workout setup")
        exercise = st.selectbox("Workout type", EXERCISES, index=0)
        source = st.radio(
            "Input source",
            [
                "Live webcam (real-time)",
                "Upload video (live playback)",
                "Sample video (skipping.mp4)",
            ],
            index=0,
        )
        uploaded_file = None
        if "Upload" in source:
            uploaded_file = st.file_uploader(
                "Upload workout video",
                type=["mp4", "mov", "avi", "mkv", "webm"],
            )
        live_preview = st.checkbox("Show live video while counting", value=True)
        start = st.button("Let's goo!!!", type="primary", use_container_width=True)
        if st.button("Reset rep counter", use_container_width=True):
            if st.session_state.trainer:
                st.session_state.trainer.reset()
            request_live_reset()
            st.session_state.total_reps_session = 0
            st.rerun()

        st.info(
            "**Single-arm friendly:** only one arm in frame (e.g. left-hand curls) is supported. "
            "Uses the clearest visible arm, not an average of both sides."
        )

    with col_view:
        st.subheader("Live feedback")
        frame_slot = st.empty()
        metrics_slot = st.empty()

    if not start:
        st.warning("Choose settings and click **Let's goo!!!** to start.")
        return

    st.session_state.workout_active = True

    if source.startswith("Live"):
        run_live_webcam(exercise, frame_slot, metrics_slot)
        return

    trainer = ensure_trainer(exercise)

    if "Upload" in source:
        if uploaded_file is None:
            st.error("Upload a video first, then click **Let's goo!!!**")
            return
        process_uploaded_video_live(
            trainer,
            uploaded_file.read(),
            frame_slot,
            metrics_slot,
            live_preview=live_preview,
        )
    else:
        if not SAMPLE_VIDEO.exists():
            st.error("Run `python create_sample_video.py` to create the sample video.")
            return
        with open(SAMPLE_VIDEO, "rb") as f:
            process_uploaded_video_live(
                trainer,
                f.read(),
                frame_slot,
                metrics_slot,
                live_preview=live_preview,
            )


def chatbot_tab() -> None:
    st.subheader("Fitness chatbot (Gemini)")
    bot = get_chatbot()
    st.caption(bot.status_message)

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask about workouts, form, nutrition, recovery…")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        reply = bot.chat(prompt, history=st.session_state.chat_history[:-1])
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)


def sidebar_info() -> None:
    with st.sidebar:
        st.header("Run")
        st.code("streamlit run app.py", language="bash")
        st.markdown(
            """
**Live webcam** uses WebRTC (real-time skeleton + reps).

**Upload video** plays back frame-by-frame with live rep overlay.

**Bicep curls:** works with one arm in frame (left or right only).
            """
        )


def main() -> None:
    init_session_state()
    render_header()
    sidebar_info()
    tab_train, tab_chat = st.tabs(["Workout tracker", "Fitness chatbot"])
    with tab_train:
        trainer_tab()
    with tab_chat:
        chatbot_tab()


if __name__ == "__main__":
    main()
