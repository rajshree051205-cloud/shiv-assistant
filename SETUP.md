# Setting up Shiv (Windows)

This is a from-scratch checklist. Follow it in order.

## 1. Install Python
Download from https://python.org (check "Add Python to PATH" during install)
if you don't already have it.

## 2. Install the dependencies
Open Command Prompt in this folder and run:

```
pip install -r requirements.txt
```

**If `pywin32` needs a post-install step**, run this once after installing:
```
python -m pywin32_postinstall -install
```
(If that command isn't found, skip it — recent pywin32 versions usually don't need it.)

**If `sounddevice` complains about PortAudio**, reinstall with:
```
pip install sounddevice --force-reinstall
```

## 3. Download the offline speech recognition model (Vosk)
This is what lets Shiv understand your voice completely offline, with no
limits and no cost.

1. Go to https://alphacephei.com/vosk/models
2. Download a small English model — `vosk-model-small-en-in-0.4` (Indian
   English) is a good pick for Hinglish speech, around 40MB.
3. Unzip it, and rename the extracted folder to `vosk-model-en`.
4. Move that folder into this project folder, next to `main.py`/`config.py`,
   so you end up with: `shiv-assistant/vosk-model-en/...`

**Optional — Hindi model:** if you want to switch Shiv's ear to Hindi instead
of English, download a Hindi model from the same page, rename its folder to
`vosk-model-hi`, place it here too, and set `DEFAULT_STT_LANGUAGE = "hi"` in
`config.py`. Note: Vosk listens in *one* language at a time — it can't
natively recognize mixed Hindi+English audio, so for genuine Hinglish speech
the Indian-English model is usually the better default, since it captures
Hindi words typed/spoken with English letters reasonably well.

## 4. Add a Hindi voice for text-to-speech (optional, but nice to have)
Shiv speaks using whatever voices Windows already has installed.
For a Hindi-sounding voice:
1. **Settings → Time & Language → Language & region**
2. **Add a language** → Hindi → install it, and make sure to check
   "Speech" under its optional features.
3. Restart the app — `pyttsx3` will now be able to pick the Hindi voice
   automatically when Shiv replies in Hindi.

If you skip this, Shiv still works — it'll just speak Hindi words using
the default English voice's pronunciation, which sounds a bit off but is
completely functional.

## 5. Allow microphone access
**Settings → Privacy & security → Microphone** → make sure "Let apps access
your microphone" and "Let desktop apps access your microphone" are both on.

## 6. Test it manually first
```
python launcher.py
```
This should:
- Print startup messages in the console
- Speak the welcome greeting and ask for consent
- Say "yes" out loud (or type in the console — voice fallback isn't wired
  into this consent step by default, so speak clearly)
- Once confirmed, say **"Shiv"** to wake it, then give a command like
  "what's the time" or "tell me a joke"

Also open **http://127.0.0.1:5000** in your browser — you should see the
dashboard, and be able to type commands there too.

Press the tray icon (bottom-right of your taskbar) to see **Open Dashboard /
Pause / Quit**.

## 7. Make it launch automatically on unlock
1. Open **Task Scheduler** (search Start menu).
2. **Create Task...** (not "Basic Task").
3. **General tab:** name it "Shiv Assistant". Check "Run only when user is
   logged on". **Important:** open the **Settings tab** and set "If the task
   is already running" to **"Do not start a new instance"** — this stops
   duplicate copies stacking up every time you unlock during the same day.
4. **Triggers tab → New...** → "Begin the task": **"On workstation unlock"**,
   specific user = your account.
5. **Actions tab → New...** → "Start a program":
   - Program/script: path to `pythonw.exe` (e.g.
     `C:\Users\<you>\AppData\Local\Programs\Python\Python3x\pythonw.exe`) —
     `pythonw.exe` instead of `python.exe` avoids a console window.
   - Add arguments: `launcher.py`
   - Start in: this project folder's full path.
6. Click OK, leave other tabs default.

Now Shiv starts the first time you unlock each day, stays running quietly
(tray icon only) through lock/unlock cycles, and only fully stops if you
click **Quit** in the tray menu.

## 8. Try these commands once it's running
- "Shiv" → wakes it → "what's the time" / "what's the weather" / "tell me a joke"
- "note this: buy milk" → saves a note
- "remind me at 5pm to call mom" / "mujhe 5 baje yaad dila dena"
- "play lofi hip hop" → opens & plays on YouTube
- "open youtube"
- "tell me about black holes" (or anything not in the answer bank) →
  opens a Google search for it
- "stop listening" / "chup ho ja" → goes quiet until you say "Shiv" again

## Customizing
Open `config.py` to change wake words, model paths, or the Flask port.
Open `database.py`'s `init_db()` defaults, or just edit preferences later
from the web dashboard, to change your name or default city.
Open `answer_bank.py` to edit, add, or remove any of the ~120 Hinglish
answers.

## Known limitations (please read)
- **Consent step is voice-only right now** — if it mishears your "yes", it
  won't start. You can also just re-run `python launcher.py` again.
- **Vosk accuracy** is good but not perfect, especially for fast or heavily
  mixed Hinglish speech — if it keeps mishearing a specific command, try
  saying it a bit more slowly and clearly.
- **Lock/unlock auto‑pause** relies on Windows session notifications via
  `pywin32`. This is the most OS-specific part of the whole project — if it
  doesn't reliably detect lock/unlock on your machine, the assistant will
  keep listening even when locked (a minor privacy point to know about,
  not a security hole, since Windows itself is still locked).
- Nothing here uses a paid or rate-limited API — Vosk, pyttsx3, wttr.in, and
  Google's plain search page are all free with no meaningful usage caps for
  personal use.
