# -*- coding: utf-8 -*-
"""
voice_agent.py
---------------
Runs continuously in the background:
- Greets you + asks consent on first start
- Idles, listening only for the wake word
- Once woken, has a short active conversation
- Speaks reminders when they're due
- Goes silent automatically when the laptop locks
- Lives as a system tray icon
"""

import json
import queue
import threading
import time
import webbrowser

import pyttsx3
import sounddevice as sd
from vosk import Model, KaldiRecognizer

import config
import database as db
import engine


# ---------------- optional tray imports ----------------

try:
    import pystray
    from PIL import Image, ImageDraw

    TRAY_AVAILABLE = True

except ImportError:
    TRAY_AVAILABLE = False


# ---------------- optional Windows imports ----------------

try:
    import win32gui
    import win32con
    import win32ts
    import win32api

    WIN32_AVAILABLE = True

except ImportError:
    WIN32_AVAILABLE = False


# ---------------- shared state ----------------

class State:
    paused = False
    active_mode = False
    running = True


state = State()


# ---------------- text to speech ----------------

engine_tts = pyttsx3.init()

engine_tts.setProperty(
    "rate",
    175
)

_tts_lock = threading.Lock()


def speak(text):

    if not text:
        return

    print(f"Shiv: {text}")

    with _tts_lock:

        engine_tts.say(text)

        engine_tts.runAndWait()


# ---------------- speech recognition ----------------

def _load_model():

    lang = db.get_preference(
        "stt_language",
        config.DEFAULT_STT_LANGUAGE
    )

    path = (
        config.VOSK_MODEL_PATH_HI
        if lang == "hi"
        else config.VOSK_MODEL_PATH_EN
    )

    print("Loading Vosk model...")

    model = Model(path)

    print("Vosk model loaded.")

    return model


def listen_loop():
    """
    Continuously captures audio from microphone
    and yields recognized text.
    """

    model = _load_model()

    audio_q = queue.Queue()

    def callback(
        indata,
        frames,
        time_info,
        status
    ):

        if status:
            print("Mic status:", status)

        audio_q.put(
            bytes(indata)
        )

    # Device 1 = Microphone Array
    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1,
        device=1,
        callback=callback
    ):

        print("Shiv microphone listening...")

        while state.running:

            if state.paused:

                time.sleep(0.5)

                while not audio_q.empty():

                    audio_q.get()

                continue

            try:

                data = audio_q.get(
                    timeout=1
                )

            except queue.Empty:

                continue

            # Vosk processes audio
            if recognizer.AcceptWaveform(data):

                result = json.loads(
                    recognizer.Result()
                )

                text = result.get(
                    "text",
                    ""
                ).strip()

                if text:

                    yield text


# ---------------- main conversation logic ----------------

def handle_recognized_text(text):

    print(
        f"You said: {text}"
    )

    # Sleep command works anytime
    if engine.is_sleep_command(text):

        speak(
            "Theek hai Rajshree, "
            "main chup ho jaata hoon. "
            "Jab zarurat ho, 'Shiv' bol dena."
        )

        state.active_mode = False

        return

    # ---------------- idle mode ----------------

    if not state.active_mode:

        if engine.is_wake_word(text):

            state.active_mode = True

            speak(
                "Haanji Rajshree, bolo."
            )

        return

    # ---------------- active mode ----------------

    response = engine.process_command(
        text,
        source="voice"
    )

    speak(response)


# ---------------- active mode timeout ----------------

def _idle_timeout_watcher():

    last_active_check = time.time()

    while state.running:

        time.sleep(5)

        # Simple version for now.
        # Timeout can be improved later.


# ---------------- consent ----------------

def greet_and_get_consent():

    user_name = db.get_preference(
        "user_name",
        "Rajshree"
    )

    # ---------------- greeting ----------------

    speak(
        f"Welcome {user_name}. "
        "What would you like to do with me today?"
    )

    speak(
        f"Would you like to work with me right now, "
        f"{user_name}?"
    )

    # ---------------- Vosk ----------------

    model = _load_model()

    recognizer = KaldiRecognizer(
        model,
        16000
    )

    audio_q = queue.Queue()

    def callback(
        indata,
        frames,
        time_info,
        status
    ):

        if status:
            print(
                "Mic status:",
                status
            )

        audio_q.put(
            bytes(indata)
        )

    heard = ""

    print(
        "Listening for consent..."
    )

    # ---------------- microphone ----------------

    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1,
        device=1,
        callback=callback
    ):

        start = time.time()

        while time.time() - start < 8:

            try:

                data = audio_q.get(
                    timeout=1
                )

            except queue.Empty:

                continue

            # Ask Vosk to process audio
            if recognizer.AcceptWaveform(data):

                result = json.loads(
                    recognizer.Result()
                )

                text = result.get(
                    "text",
                    ""
                ).strip()

                if text:

                    heard = text

                    print(
                        f"Consent partial result: '{heard}'"
                    )

                    break

        # ---------------- IMPORTANT ----------------
        # Even if AcceptWaveform did not return True,
        # get the final result from Vosk.

        if not heard:

            final_result = json.loads(
                recognizer.FinalResult()
            )

            heard = final_result.get(
                "text",
                ""
            ).strip()

    # ---------------- result ----------------

    print(
        f"Consent heard: '{heard}'"
    )

    heard_lower = heard.lower()

    # ---------------- consent words ----------------

    consent_words = [
        "yes",
        "yeah",
        "yep",
        "haan",
        "han",
        "ok",
        "okay",
        "sure",
        "of course",
        "i want",
        "i do",
        "let's do",
        "lets do",
        "go ahead",
        "start",
        "continue"
    ]

    consent_given = any(
        word in heard_lower
        for word in consent_words
    )

    # ---------------- accepted ----------------

    if consent_given:

        speak(
            "Great! Bas 'Shiv' bol kar "
            "mujhe bulao jab kaam ho."
        )

        return True

    # ---------------- rejected / not heard ----------------

    else:

        speak(
            "Theek hai, main chup rahunga. "
            "Jab chaho, mujhe phir se start kar dena."
        )

        return False


# ---------------- reminders ----------------

def reminder_checker():

    while state.running:

        time.sleep(
            config.REMINDER_CHECK_INTERVAL_SECONDS
        )

        if state.paused:
            continue

        due = db.get_due_reminders()

        for r in due:

            speak(
                f"Rajshree, reminder: "
                f"{r['content']}"
            )

            db.mark_reminder_done(
                r["id"]
            )


# ---------------- lock / unlock awareness ----------------

def _lock_listener_thread():

    if not WIN32_AVAILABLE:

        print(
            "pywin32 not installed - "
            "lock/unlock auto-pause is disabled."
        )

        return

    WM_WTSSESSION_CHANGE = 0x02B1

    WTS_SESSION_LOCK = 0x7
    WTS_SESSION_UNLOCK = 0x8

    def wnd_proc(
        hwnd,
        msg,
        wparam,
        lparam
    ):

        if msg == WM_WTSSESSION_CHANGE:

            if wparam == WTS_SESSION_LOCK:

                state.paused = True
                state.active_mode = False

                print(
                    "Laptop locked - "
                    "Shiv going silent."
                )

            elif wparam == WTS_SESSION_UNLOCK:

                state.paused = False

                print(
                    "Laptop unlocked - "
                    "Shiv resuming."
                )

        return win32gui.DefWindowProc(
            hwnd,
            msg,
            wparam,
            lparam
        )

    wc = win32gui.WNDCLASS()

    wc.lpfnWndProc = wnd_proc

    wc.lpszClassName = (
        "ShivSessionListener"
    )

    class_atom = (
        win32gui.RegisterClass(wc)
    )

    hwnd = win32gui.CreateWindow(
        class_atom,
        "ShivSessionListener",
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        win32api.GetModuleHandle(None),
        None
    )

    win32ts.WTSRegisterSessionNotification(
        hwnd,
        win32ts.NOTIFY_FOR_THIS_SESSION
    )

    win32gui.PumpMessages()


# ---------------- tray icon ----------------

def _make_icon_image():

    img = Image.new(
        "RGB",
        (64, 64),
        "#1c1c1c"
    )

    draw = ImageDraw.Draw(img)

    draw.ellipse(
        (8, 8, 56, 56),
        fill="#e07a3e"
    )

    return img


def _open_dashboard(
    icon=None,
    item=None
):

    webbrowser.open(
        f"http://{config.FLASK_HOST}:"
        f"{config.FLASK_PORT}"
    )


def _toggle_pause(
    icon=None,
    item=None
):

    state.paused = not state.paused

    print(
        "Paused"
        if state.paused
        else "Resumed"
    )


def _quit(
    icon=None,
    item=None
):

    state.running = False

    if icon:

        icon.stop()


def run_tray():

    if not TRAY_AVAILABLE:

        print(
            "pystray/Pillow not installed - "
            "no tray icon."
        )

        while state.running:

            time.sleep(1)

        return

    menu = pystray.Menu(

        pystray.MenuItem(
            "Open Dashboard",
            _open_dashboard
        ),

        pystray.MenuItem(
            "Pause/Resume",
            _toggle_pause
        ),

        pystray.MenuItem(
            "Quit",
            _quit
        )
    )

    icon = pystray.Icon(
        "Shiv",
        _make_icon_image(),
        "Shiv Assistant",
        menu
    )

    icon.run()


# ---------------- entry point ----------------

def start_assistant():

    db.init_db()

    consented = (
        greet_and_get_consent()
    )

    if not consented:

        return

    # ---------------- reminders ----------------

    threading.Thread(
        target=reminder_checker,
        daemon=True
    ).start()

    # ---------------- lock listener ----------------

    threading.Thread(
        target=_lock_listener_thread,
        daemon=True
    ).start()

    # ---------------- voice loop ----------------

    def voice_loop():

        for text in listen_loop():

            if not state.running:

                break

            handle_recognized_text(
                text
            )

    threading.Thread(
        target=voice_loop,
        daemon=True
    ).start()

    # ---------------- tray ----------------

    run_tray()


# ---------------- run ----------------

if __name__ == "__main__":

    start_assistant()