<div align="center">

![DigDeep Logo](assets/digdeep-logo.png)

</div>

**DigDeep** is an open-source, AI-powered volleyball video analytics tool designed to simplify game review & analysis for players, coaches, and fans. With planned features like auto-editing, score tracking, player stats, and more, DigDeep aims to provide accessible, cutting-edge analytics for the volleyball community, free, forever.

## Setup 🛠️

**Requirements:** Python 3.11, CUDA 12.x (GPU recommended)

```bash
# 1. Clone the repo
git clone https://github.com/ryan1288/digdeep.git && cd digdeep

# 2. Install dependencies
#    torch must be installed first with the CUDA wheel
pip install torch>=2.0.0 --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

# 3. Run the app
#    Model weights are downloaded automatically from HuggingFace Hub on first launch.
#    Override model paths via environment variables if you have local weights:
#      DIGDEEP_BALL_MODEL, DIGDEEP_PLAYER_MODEL, DIGDEEP_REID_MODEL
python scripts/run_app.py
```

## Planned Features 📋
- **Auto-Editor:** Automatically remove downtime between plays for faster video review.
- **Score Tracking:** Timestamp key moments and keep an accurate score throughout the video.
- **Action-Specific Replays:** Replay only the most relevant portions of the video based on specific actions.
- **Court Usage Analysis:** Understand where the ball is contacted most often during play.
- **Player-Specific Statistics:** Collect and present performance metrics for individual players.

## License 📄
This project is licensed under the [Apache License 2.0](LICENSE).

## Contact ✉️
For questions, feedback, or if you want to join the Discord to collaborate, feel free to reach out:

Email: ryanleerobo@gmail.com - Subject: DigDeep
