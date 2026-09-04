# -*- coding: utf-8 -*-
"""
launcher.py
------------
This is the single file Task Scheduler should launch. It starts the
web dashboard in the background, then starts the voice agent
(which owns the tray icon and blocks until you Quit from the tray).
"""

import threading

from web_app import run_web_app
from voice_agent import start_assistant

if __name__ == "__main__":
    threading.Thread(target=run_web_app, daemon=True).start()
    start_assistant()
