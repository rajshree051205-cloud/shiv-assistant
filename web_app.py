# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, render_template
import json
import queue
import os
import tempfile

import config
import database as db
import engine

from vosk import Model, KaldiRecognizer
from scipy.io import wavfile


app = Flask(__name__)


# ============================================================
# VOSK MODEL
# ============================================================

vosk_model = None


def get_vosk_model():
    global vosk_model

    if vosk_model is None:
        print("Loading Vosk model...")
        vosk_model = Model(config.VOSK_MODEL_PATH_EN)
        print("Vosk model loaded.")

    return vosk_model


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def dashboard():
    return render_template("index.html")


# ============================================================
# TEXT COMMAND
# ============================================================

@app.route("/api/command", methods=["POST"])
def api_command():

    data = request.get_json(force=True)

    text = (data or {}).get("text", "").strip()

    if not text:
        return jsonify({
            "response": "Please say or type something."
        })

    response = engine.process_command(
        text,
        source="web"
    )

    return jsonify({
        "response": response
    })


# ============================================================
# VOICE COMMAND
# ============================================================

@app.route("/api/voice", methods=["POST"])
def api_voice():

    if "audio" not in request.files:
        return jsonify({
            "error": "No audio received."
        }), 400

    audio_file = request.files["audio"]

    temp_path = None

    try:

        # Save uploaded audio temporarily
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        ) as temp:

            audio_file.save(temp.name)
            temp_path = temp.name

        # Read WAV file
        sample_rate, audio_data = wavfile.read(
            temp_path
        )

        # Vosk expects 16 kHz audio
        if sample_rate != 16000:

            return jsonify({
                "error": f"Expected 16000 Hz audio, got {sample_rate} Hz."
            }), 400

        # Convert audio to bytes
        audio_bytes = audio_data.tobytes()

        model = get_vosk_model()

        recognizer = KaldiRecognizer(
            model,
            16000
        )

        recognizer.AcceptWaveform(
            audio_bytes
        )

        result = json.loads(
            recognizer.FinalResult()
        )

        text = result.get(
            "text",
            ""
        ).strip()

        print(f"Browser voice: {text}")

        if not text:

            return jsonify({
                "text": "",
                "response": "I couldn't understand that. Please try again."
            })

        # Send recognized text to the SAME engine
        response = engine.process_command(
            text,
            source="web"
        )

        return jsonify({
            "text": text,
            "response": response
        })

    except Exception as e:

        print("Voice processing error:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if temp_path and os.path.exists(temp_path):

            os.remove(temp_path)


# ============================================================
# HISTORY
# ============================================================

@app.route("/api/history")
def api_history():

    return jsonify(
        db.get_history(limit=100)
    )


# ============================================================
# NOTES
# ============================================================

@app.route("/api/notes", methods=["GET", "POST"])
def api_notes():

    if request.method == "POST":

        data = request.get_json(force=True)

        content = (
            (data or {})
            .get("content", "")
            .strip()
        )

        if content:
            db.add_note(content)

        return jsonify({
            "ok": True
        })

    return jsonify(
        db.get_notes(limit=100)
    )


@app.route(
    "/api/notes/<int:note_id>",
    methods=["DELETE"]
)
def api_delete_note(note_id):

    db.delete_note(note_id)

    return jsonify({
        "ok": True
    })


# ============================================================
# REMINDERS
# ============================================================

@app.route(
    "/api/reminders",
    methods=["GET", "POST"]
)
def api_reminders():

    if request.method == "POST":

        data = request.get_json(force=True)

        text = (
            (data or {})
            .get("text", "")
            .strip()
        )

        if text:

            response = engine.process_command(
                text,
                source="web"
            )

            return jsonify({
                "response": response
            })

        return jsonify({
            "ok": False
        }), 400

    return jsonify(
        db.get_all_reminders(limit=100)
    )


@app.route(
    "/api/reminders/<int:reminder_id>",
    methods=["DELETE"]
)
def api_delete_reminder(reminder_id):

    db.delete_reminder(reminder_id)

    return jsonify({
        "ok": True
    })


# ============================================================
# PREFERENCES
# ============================================================

@app.route(
    "/api/preferences",
    methods=["GET", "POST"]
)
def api_preferences():

    if request.method == "POST":

        data = request.get_json(force=True) or {}

        for key, value in data.items():

            db.set_preference(
                key,
                value
            )

        return jsonify({
            "ok": True
        })

    return jsonify(
        db.get_all_preferences()
    )


# ============================================================
# START
# ============================================================

def run_web_app():

    db.init_db()

    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=False,
        use_reloader=False
    )


if __name__ == "__main__":

    run_web_app()