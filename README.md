# AI-Powered Fitness Trainer

An AI-powered fitness trainer built with **Streamlit**, **OpenCV (headless)**, and **MediaPipe** for pose estimation. Track **Bicep Curls**, **Squats**, and **Push-Ups** in real time from your webcam or an uploaded video. Includes a **Gemini** chatbot for health and fitness questions.

## Features

- **Live webcam** with real-time skeleton overlay and rep counter (`streamlit-webrtc`)
- **Upload video** with frame-by-frame live playback while counting reps
- Single-arm bicep curls (left or right arm only in frame)
- Automatic rep counting (angle-based, works from many camera angles):
  - Bicep Curls
  - Squats
  - Push-Ups
- Gemini API chatbot for fitness Q&A
- Streamlit UI tuned for local run and **Streamlit Community Cloud** deploy

## Project structure

```
AI-Fitness-Trainer/
├── AiTrainer/                # Core rep-counting & geometry
│   ├── __init__.py
│   ├── exercises.py
│   └── geometry.py
├── ai_trainer.py             # Trainer orchestration
├── aichatbot.py              # Gemini chatbot
├── app.py                    # Main Streamlit app
├── pose_estimator.py         # MediaPipe pose wrapper
├── pose_estimator_module.py  # Drawing & frame helpers
├── requirements.txt
├── packages.txt              # Optional Cloud system libs
├── skipping.mp4              # Sample workout video
├── test.py                   # Dependency test script
├── .env.example
├── .streamlit/config.toml
├── README.md
└── LICENSE
```

## Why this deploys reliably

| Issue | Solution |
|--------|----------|
| OpenCV GUI / `libGL` errors on Linux cloud | `opencv-python-headless` only |
| `cv2.VideoCapture(0)` fails in cloud | `st.camera_input` for webcam |
| Rep counts break at an angle | Joint **angles** + best visible side, not pixel height |
| Huge uploads | `maxUploadSize` in `.streamlit/config.toml` |

## Installation

```bash
git clone https://github.com/your-username/AI-Fitness-Trainer.git
cd AI-Fitness-Trainer
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit .env
```

Add your Google API key:

```env
GOOGLE_API_KEY=your_api_key_here
```

Verify dependencies:

```bash
python test.py
```

## Run locally

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Set **Main file path** to `app.py`.
4. Under **Secrets**, add:

```toml
GOOGLE_API_KEY = "your_api_key_here"
```

5. Deploy. If a rare OpenCV system lib error appears, `packages.txt` already lists `libgl1`.

## How it works

1. Select workout type (Bicep Curl, Squat, Push-Up).
2. Choose **Live webcam**, **Upload video**, or **Sample video**.
3. Click **Let's goo!!!**
4. Watch the **live video** with skeleton overlay and rep count updating in real time.
5. Use the **Fitness chatbot** tab for coaching questions.

## Angle-friendly & single-arm counting

Reps use joint angles (elbow for curls, knee for squats). The tracker uses the **most visible arm or leg only**—it does not average both sides (which broke single-arm curl videos). For partial frames, relaxed visibility and fallback metrics (hip–elbow–wrist, forearm bend) are used.

## Technologies

Python · NumPy · Pandas · OpenCV · MediaPipe · Streamlit · Google Gemini API

## License

MIT — see [LICENSE](LICENSE).
