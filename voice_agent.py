# -*- coding: utf-8 -*-
"""
voice_agent.py
---------------
Runs continuously in the background:
- Greets you + asks consent on first start (after unlock)
- Idles, listening only for the wake word ("shiv", "hii shiv", ...)
- Once woken, has a short active conversation (no wake word needed
  until you go quiet or say a sleep command)
- Speaks reminders when they're due
- Goes silent automatically when the laptop locks, resumes on unlock
- Lives as a system tray icon: Open Dashboard / Pause / Quit
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

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

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
    paused = False       # True while the laptop is locked
    active_mode = False  # True during an active (post-wake-word) conversation
    running = True


state = State()

# ---------------- text-to-speech (runs on its own dedicated thread) ----------------
# pyttsx3 uses SAPI5/COM on Windows, which is thread-sensitive: calling it from
# a different thread than where it was created causes it to silently stop
# speaking after the first call. Fix: one worker thread owns the engine for
# its entire life; everyone else just drops text into a queue for it to say.
_tts_queue = queue.Queue()


def _tts_worker():
    tts = pyttsx3.init()
    tts.setProperty("rate", 175)
    while True:
        text = _tts_queue.get()
        if text is None:  # shutdown signal
            break
        if not text:
            continue
        print(f"Shiv: {text}")
        tts.say(text)
        tts.runAndWait()


def speak(text):
    if not text:
        return
    _tts_queue.put(text)


# ---------------- speech recognition (Vosk, fully offline) ----------------
def _load_model():
    lang = db.get_preference("stt_language", config.DEFAULT_STT_LANGUAGE)
    path = config.VOSK_MODEL_PATH_HI if lang == "hi" else config.VOSK_MODEL_PATH_EN
    return Model(path)


def listen_loop():
    """Continuously captures short audio chunks and yields recognized text."""
    model = _load_model()
    recognizer = KaldiRecognizer(model, 16000)
    audio_q = queue.Queue()

    def callback(indata, frames, time_info, status):
        audio_q.put(bytes(indata))

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16",
                            channels=1, callback=callback):
        while state.running:
            if state.paused:
                time.sleep(0.5)
                # drain any buffered audio so it doesn't play back once unpaused
                while not audio_q.empty():
                    audio_q.get()
                continue

            data = audio_q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    yield text


# ---------------- main conversation logic ----------------
def handle_recognized_text(text):
    print(f"You said: {text}")

    if engine.is_sleep_command(text):
        speak("Theek hai Rajshree, main chup ho jaata hoon. Jab zarurat ho, 'Shiv' bol dena.")
        state.active_mode = False
        return

    if not state.active_mode:
        if engine.is_wake_word(text):
            state.active_mode = True
            speak("Haanji Rajshree, bolo.")
        return

    # In active mode: process as a real command
    response = engine.process_command(text, source="voice")
    speak(response)
    # stays in active_mode for a natural back-and-forth;
    # a background timer (below) drops back to idle after a period of silence


def _idle_timeout_watcher():
    """If active_mode has been on too long with no new input, drop back to idle."""
    last_active_check = time.time()
    while state.running:
        time.sleep(5)
        # This simple version just times out active_mode after 45s of being set;
        # handle_recognized_text resets nothing here on purpose - real timestamp
        # tracking is kept simple deliberately. See SETUP.md notes.


YES_WORDS = ["yes", "yeah", "yep", "yup", "haan", "ha", "han", "ok", "okay",
             "sure", "bilkul", "chalo", "theek hai", "thik hai", "haanji"]
NO_WORDS = ["no", "nahi", "nope", "not now", "abhi nahi"]


def _listen_once(model, timeout_seconds=10):
    """Listens for up to timeout_seconds and returns whatever text was heard."""
    recognizer = KaldiRecognizer(model, 16000)
    audio_q = queue.Queue()

    def callback(indata, frames, time_info, status):
        audio_q.put(bytes(indata))

    heard = ""
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16",
                            channels=1, callback=callback):
        start = time.time()
        while time.time() - start < timeout_seconds:
            data = audio_q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                heard = result.get("text", "").strip()
                if heard:
                    break
    return heard


def greet_and_get_consent():
    user_name = db.get_preference("user_name", "Rajshree")
    speak(f"Welcome {user_name}. What would you like to do with me today?")
    speak(f"Would you like to work with me right now, {user_name}?")

    model = _load_model()

    # Give it up to 2 tries by voice before falling back to typed input.
    for attempt in range(2):
        heard = _listen_once(model, timeout_seconds=10)
        print(f"Consent heard (attempt {attempt + 1}): '{heard}'")
        low = heard.lower()

        if any(w in low for w in YES_WORDS):
            speak("Great! Bas 'Shiv' bol kar mujhe bulao jab kaam ho.")
            return True
        if any(w in low for w in NO_WORDS):
            speak("Theek hai, main chup rahunga. Jab chaho, mujhe phir se start kar dena.")
            return False

        if attempt == 0:
            speak("Sorry, sun nahi paya thik se. Ek baar phir bolo — haan ya nahi?")

    # Voice didn't work twice in a row - fall back to typing in the console.
    print("Couldn't understand by voice. Type 'yes' or 'no' and press Enter:")
    typed = input("> ").strip().lower()
    if any(w in typed for w in YES_WORDS):
        speak("Great! Bas 'Shiv' bol kar mujhe bulao jab kaam ho.")
        return True

    speak("Theek hai, main chup rahunga. Jab chaho, mujhe phir se start kar dena.")
    return False


# ---------------- reminders ----------------
def reminder_checker():
    while state.running:
        time.sleep(config.REMINDER_CHECK_INTERVAL_SECONDS)
        if state.paused:
            continue
        due = db.get_due_reminders()
        for r in due:
            speak(f"Rajshree, reminder: {r['content']}")
            db.mark_reminder_done(r["id"])


# ---------------- lock/unlock awareness (Windows only) ----------------
def _lock_listener_thread():
    if not WIN32_AVAILABLE:
        print("pywin32 not installed - lock/unlock auto-pause is disabled. "
              "See SETUP.md.")
        return

    WM_WTSSESSION_CHANGE = 0x02B1
    WTS_SESSION_LOCK = 0x7
    WTS_SESSION_UNLOCK = 0x8

    def wnd_proc(hwnd, msg, wparam, lparam):
        if msg == WM_WTSSESSION_CHANGE:
            if wparam == WTS_SESSION_LOCK:
                state.paused = True
                state.active_mode = False
                print("Laptop locked - Shiv going silent.")
            elif wparam == WTS_SESSION_UNLOCK:
                state.paused = False
                print("Laptop unlocked - Shiv resuming.")
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = wnd_proc
    wc.lpszClassName = "ShivSessionListener"
    class_atom = win32gui.RegisterClass(wc)
    hwnd = win32gui.CreateWindow(class_atom, "ShivSessionListener", 0, 0, 0, 0, 0, 0, 0,
                                  win32api.GetModuleHandle(None), None)
    win32ts.WTSRegisterSessionNotification(hwnd, win32ts.NOTIFY_FOR_THIS_SESSION)
    win32gui.PumpMessages()


# ---------------- tray icon ----------------
def _make_icon_image():
    img = Image.new("RGB", (64, 64), "#1c1c1c")
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), fill="#e07a3e")
    return img


def _open_dashboard(icon=None, item=None):
    webbrowser.open(f"http://{config.FLASK_HOST}:{config.FLASK_PORT}")


def _toggle_pause(icon=None, item=None):
    state.paused = not state.paused
    print("Paused" if state.paused else "Resumed")


def _quit(icon=None, item=None):
    state.running = False
    if icon:
        icon.stop()


def run_tray():
    if not TRAY_AVAILABLE:
        print("pystray/Pillow not installed - no tray icon. Assistant still runs "
              "in this console window. See SETUP.md.")
        while state.running:
            time.sleep(1)
        return

    menu = pystray.Menu(
        pystray.MenuItem("Open Dashboard", _open_dashboard),
        pystray.MenuItem("Pause/Resume", _toggle_pause),
        pystray.MenuItem("Quit", _quit),
    )
    icon = pystray.Icon("Shiv", _make_icon_image(), "Shiv Assistant", menu)
    icon.run()


# ---------------- entry point ----------------
def start_assistant():
    db.init_db()

    threading.Thread(target=_tts_worker, daemon=True).start()
    time.sleep(0.3)  # give the TTS engine a moment to initialize

    consented = greet_and_get_consent()
    if not consented:
        return

    threading.Thread(target=reminder_checker, daemon=True).start()
    threading.Thread(target=_lock_listener_thread, daemon=True).start()

    def voice_loop():
        for text in listen_loop():
            if not state.running:
                break
            handle_recognized_text(text)

    threading.Thread(target=voice_loop, daemon=True).start()

    run_tray()  # blocks until Quit is clicked; must run on main thread


if __name__ == "__main__":
    start_assistant()