"""
functions.py
-------------
Everything that actually DOES something (as opposed to just talking):
time, date, weather, opening YouTube, playing a video, saving notes,
and parsing/setting reminders. No AI, no paid API — only wttr.in
(free, no key) touches the internet, and only for weather.
"""

import re
import webbrowser
import datetime
import requests

import database as db


# ---------------- TIME / DATE ----------------
def get_time_text():
    now = datetime.datetime.now().strftime("%I:%M %p").lstrip("0")
    return f"Abhi time hai {now}."


def get_date_text():
    today = datetime.datetime.now().strftime("%A, %d %B %Y")
    return f"Aaj hai {today}."


# ---------------- WEATHER ----------------
def get_weather_text(city=None):
    if not city:
        city = db.get_preference("default_city", "Jaipur")
    try:
        r = requests.get(f"https://wttr.in/{city}?format=j1", timeout=6)
        r.raise_for_status()
        data = r.json()
        cur = data["current_condition"][0]
        temp_c = cur["temp_C"]
        desc = cur["weatherDesc"][0]["value"]
        return f"{city} mein abhi {temp_c} degree Celsius hai, aur {desc.lower()} chal raha hai."
    except Exception:
        return "Sorry Rajshree, weather fetch nahi ho paya abhi. Internet check kar lo."


# ---------------- YOUTUBE ----------------
def open_youtube():
    webbrowser.open("https://www.youtube.com")
    return "Kholt raha hoon YouTube."


def play_video(query):
    query = query.strip()
    if not query:
        return "Kaunsa video chalaun? Naam batao."
    search_url = "https://www.youtube.com/results?search_query=" + requests.utils.quote(query)
    webbrowser.open(search_url)
    return f"'{query}' search kar raha hoon YouTube pe."


# ---------------- GOOGLE FALLBACK ----------------
def google_search(query):
    lang = "hi" if _looks_hindi(query) else "en"
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}&hl={lang}"
    webbrowser.open(url)
    return "Sorry, I don't have an answer for that. I'm redirecting you to Google."


def _looks_hindi(text):
    return any("\u0900" <= ch <= "\u097F" for ch in text)


# ---------------- NOTES ----------------
def save_note(content):
    content = content.strip()
    if not content:
        return "Kya note karna hai, bolo?"
    db.add_note(content)
    return f"Note ho gaya: \"{content}\"."


def list_notes_text(limit=5):
    notes = db.get_notes(limit=limit)
    if not notes:
        return "Abhi koi notes nahi hain."
    lines = [f"- {n['content']}" for n in notes]
    return "Tumhare recent notes:\n" + "\n".join(lines)


# ---------------- REMINDERS / ALARMS ----------------
_HOUR_WORD_RE = re.compile(
    r"(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm|baje)?", re.IGNORECASE
)
_IN_MINUTES_RE = re.compile(r"(\d+)\s*(minute|minutes|min|mins)", re.IGNORECASE)
_IN_HOURS_RE = re.compile(r"(\d+)\s*(hour|hours|hr|hrs|ghante|ghanta)", re.IGNORECASE)


def parse_reminder_time(text):
    """
    Very lightweight parser for common patterns:
    - "5 baje" / "5pm" / "5:30 pm"
    - "in 20 minutes" / "20 minute baad"
    - "in 2 hours" / "2 ghante baad"
    Returns a datetime, or None if nothing could be parsed.
    """
    text = text.lower()
    now = datetime.datetime.now()

    m = _IN_MINUTES_RE.search(text)
    if m:
        return now + datetime.timedelta(minutes=int(m.group(1)))

    m = _IN_HOURS_RE.search(text)
    if m:
        return now + datetime.timedelta(hours=int(m.group(1)))

    m = _HOUR_WORD_RE.search(text)
    if m and m.group(1):
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        meridiem = (m.group(3) or "").lower()

        if hour > 23:
            return None

        if meridiem == "am":
            hour = hour % 12
        elif meridiem == "pm":
            hour = (hour % 12) + 12
        else:
            # No am/pm given (e.g. plain "5 baje"): assume the next
            # upcoming occurrence of that hour, preferring PM for
            # typical daytime hours 1-7.
            candidate_am = hour % 12
            candidate_pm = (hour % 12) + 12
            today_pm = now.replace(hour=candidate_pm, minute=minute, second=0, microsecond=0)
            if today_pm > now:
                hour = candidate_pm
            else:
                hour = candidate_am

        target = now.replace(hour=hour % 24, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += datetime.timedelta(days=1)
        return target

    return None


def set_reminder(text):
    """text is the full thing the user said, e.g. 'mujhe 5 baje call karna yaad dila dena'."""
    when = parse_reminder_time(text)
    if when is None:
        return ("Time samajh nahi aaya. Try: 'mujhe 5 baje yaad dila dena' "
                "ya 'remind me in 20 minutes'.")

    # strip obvious time phrases out of the content, leave the rest as the reminder text
    content = text
    for pattern in (_IN_MINUTES_RE, _IN_HOURS_RE, _HOUR_WORD_RE):
        content = pattern.sub("", content)
    content = re.sub(r"\b(remind me|yaad dila|yaad dilana|alarm set kar|alarm laga|baje|baad|to|karo|karna|do|kar do|dena)\b",
                      "", content, flags=re.IGNORECASE)
    content = re.sub(r"\s+", " ", content).strip(" ,.-")
    if not content:
        content = "Reminder"

    db.add_reminder(when.isoformat(timespec="seconds"), content)
    when_text = when.strftime("%I:%M %p").lstrip("0")
    return f"Theek hai Rajshree, main tumhe {when_text} par yaad dila dunga: \"{content}\"."


def list_reminders_text(limit=5):
    reminders = db.get_all_reminders(limit=limit)
    pending = [r for r in reminders if not r["done"]]
    if not pending:
        return "Abhi koi reminder set nahi hai."
    lines = []
    for r in pending:
        t = datetime.datetime.fromisoformat(r["remind_at"]).strftime("%I:%M %p").lstrip("0")
        lines.append(f"- {t}: {r['content']}")
    return "Tumhare pending reminders:\n" + "\n".join(lines)
