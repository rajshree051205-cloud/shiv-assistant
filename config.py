"""
config.py
----------
Edit these values to customize Shiv. No code-reading required for
the common tweaks.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Folder where you extract the downloaded Vosk model (see SETUP.md).
# English (Indian English works well for Hinglish typed phonetically).
VOSK_MODEL_PATH_EN = os.path.join(BASE_DIR, "vosk-model-en")
# Optional: a Hindi Vosk model, if you download one and want to switch to it.
VOSK_MODEL_PATH_HI = os.path.join(BASE_DIR, "vosk-model-hi")

# Which model to load by default: "en" or "hi"
DEFAULT_STT_LANGUAGE = "en"

WAKE_WORDS = ["hii shiv", "shiv", "sun shiv", "shiv yaar", "hello shiv", "namaste shiv"]

FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000

REMINDER_CHECK_INTERVAL_SECONDS = 60
