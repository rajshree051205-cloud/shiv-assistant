
# -*- coding: utf-8 -*-
"""
engine.py
----------
The "brain" of Shiv. Takes a piece of text (from voice or web),
figures out what to do, and returns a response. Both the voice agent
and the web dashboard call process_command() so behaviour is identical
no matter how you talk to Shiv.

Matching order:
  1. Control commands (sleep/stop listening)
  2. Dynamic intents (time, date, weather, notes, reminders)
  3. Static answer bank (~120 Hinglish Q&A)
  4. Fallback - open a Google search for whatever was asked.
"""

import re
import difflib

import database as db
import functions as fn
from answer_bank import INTENTS


FUZZY_THRESHOLD = 0.55


# ---------------- sleep commands ----------------

SLEEP_PATTERNS = [
    "stop listening",
    "go to sleep",
    "chup ho ja",
    "chup rehna",
    "so ja shiv",
    "band ho ja",
    "quiet ho ja",
]


# ---------------- wake word patterns ----------------

# Vosk sometimes hears "Shiv" incorrectly as
# "shoe", "shoo", "shove", etc.
#
# "tell me" is also accepted as a trigger.
#
# IMPORTANT:
# "hi" and "hello" alone are NOT triggers.

WAKE_BACK_PATTERNS = [
    # Shiv and common Vosk misrecognitions
    "shiv",
    "shoe",
    "shoo",
    "shove",
    "shev",

    # Shiv variations
    "shiv yaar",
    "shoe yaar",
    "shoo yaar",
    "shove yaar",

    # Common phrases containing Shiv
    "hii shiv",
    "hi shiv",
    "hey shiv",
    "hello shiv",
    "sun shiv",
    "namaste shiv",

    # Alternative trigger
    "tell me",
]


# ---------------- text normalization ----------------

def _normalize(text):
    text = text.lower().strip()

    text = re.sub(
        r"[?!.,]",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# ---------------- sleep detection ----------------

def is_sleep_command(text):
    t = _normalize(text)

    return any(
        p in t
        for p in SLEEP_PATTERNS
    )


# ---------------- wake word detection ----------------

def is_wake_word(text):
    """
    Detects Shiv's wake word.

    Accepted wake words / phrases:

        shiv
        shoe
        shoo
        shove
        shev

        shiv yaar
        hii shiv
        hi shiv
        hey shiv
        hello shiv
        sun shiv
        namaste shiv

        tell me

    Random words such as:

        yes
        oh
        hi
        hello
        shame

    will NOT wake Shiv.
    """

    t = _normalize(text)

    for pattern in WAKE_BACK_PATTERNS:

        # Exact match
        if t == pattern:
            return True

        # Allow extra words after the wake phrase
        #
        # Example:
        # "tell me what is the time"
        # "shiv what is the weather"
        #
        if t.startswith(pattern + " "):
            return True

    return False


# ---------------- dynamic intent detection ----------------

def _try_dynamic(text):
    """
    Returns (response, intent_name) if a dynamic
    function-backed intent matched, else None.
    """

    t = _normalize(text)

    # Time
    if re.search(
        r"\b(what'?s the )?time\b|time kya hui|kitne baje",
        t
    ):
        return fn.get_time_text(), "time"


    # Date
    if re.search(
        r"\bdate\b|aaj kya (date|din) hai|what'?s the date",
        t
    ):
        return fn.get_date_text(), "date"


    # Weather
    if "weather" in t or "mausam" in t:

        city_match = re.search(
            r"weather (?:in|for) (\w+)",
            t
        )

        city = (
            city_match.group(1)
            if city_match
            else None
        )

        return fn.get_weather_text(city), "weather"


    # Open YouTube
    if re.search(
        r"\bopen youtube\b|youtube khol",
        t
    ) and "video" not in t and "play" not in t:

        return fn.open_youtube(), "open_youtube"


    # Play video
    if re.search(
        r"\bplay\b|\bvideo\b|chalao",
        t
    ) and "reminder" not in t:

        query = t

        for w in [
            "shiv",
            "shoe",
            "shoo",
            "shove",
            "shev",
            "play",
            "open",
            "video",
            "on youtube",
            "chalao",
            "chala do"
        ]:
            query = query.replace(
                w,
                ""
            )

        return fn.play_video(
            query.strip()
        ), "play_video"


    # Notes
    if re.search(
        r"\bnote (this|down)?\b|yaad rakhna|note kar lo|ye note kar",
        t
    ):

        content = re.sub(
            r"\b(shiv|shoe|shoo|shove|shev|note this|note down|note|yaad rakhna|note kar lo|ye note kar)\b",
            "",
            t
        ).strip(
            " :,-"
        )

        return fn.save_note(
            content
        ), "add_note"


    # List notes
    if re.search(
        r"\b(my )?notes\b|tasks (kya|list)|mere notes",
        t
    ):
        return fn.list_notes_text(), "list_notes"


    # Add reminder
    if re.search(
        r"remind me|yaad dila|alarm set|alarm laga|reminder set",
        t
    ):
        return fn.set_reminder(
            text
        ), "add_reminder"


    # List reminders
    if re.search(
        r"\breminders\b|pending reminders|mere reminders|schedule.*today|what'?s on my schedule",
        t
    ):
        return fn.list_reminders_text(), "list_reminders"


    return None


# ---------------- static bank matching ----------------

def _try_static(text):

    t = _normalize(text)

    best_score = 0.0
    best_response = None

    for examples, response in INTENTS:

        for example in examples:

            score = difflib.SequenceMatcher(
                None,
                t,
                _normalize(example)
            ).ratio()

            if score > best_score:

                best_score = score
                best_response = response

    if best_score >= FUZZY_THRESHOLD:

        return (
            best_response,
            "static_bank"
        )

    return None


# ---------------- public entry point ----------------

def process_command(
    text,
    source="voice"
):
    """
    text: what the user said/typed
    source: 'voice' or 'web'

    Returns the response text.
    """

    if not text or not text.strip():
        return ""


    # Dynamic intents
    dynamic = _try_dynamic(text)

    if dynamic:

        response, intent = dynamic

        db.log_command(
            source,
            text,
            response,
            intent
        )

        return response


    # Static answer bank
    static = _try_static(text)

    if static:

        response, intent = static

        db.log_command(
            source,
            text,
            response,
            intent
        )

        return response


    # Google fallback
    response = fn.google_search(text)

    db.log_command(
        source,
        text,
        response,
        "unknown_google_fallback"
    )

    return response

