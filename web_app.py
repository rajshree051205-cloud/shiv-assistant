# -*- coding: utf-8 -*-
"""
web_app.py
-----------
Local-only web dashboard (http://127.0.0.1:5000). Lets you type
commands, view history, and manage notes/reminders/preferences.
Talks to the exact same engine.py the voice agent uses, and the
exact same shiv.db, so everything stays in sync.
"""

from flask import Flask, request, jsonify, render_template

import config
import database as db
import engine

app = Flask(__name__)


@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/api/command", methods=["POST"])
def api_command():
    data = request.get_json(force=True)
    text = (data or {}).get("text", "")
    response = engine.process_command(text, source="web")
    return jsonify({"response": response})


@app.route("/api/history")
def api_history():
    return jsonify(db.get_history(limit=100))


@app.route("/api/notes", methods=["GET", "POST"])
def api_notes():
    if request.method == "POST":
        data = request.get_json(force=True)
        content = (data or {}).get("content", "").strip()
        if content:
            db.add_note(content)
        return jsonify({"ok": True})
    return jsonify(db.get_notes(limit=100))


@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
def api_delete_note(note_id):
    db.delete_note(note_id)
    return jsonify({"ok": True})


@app.route("/api/reminders", methods=["GET", "POST"])
def api_reminders():
    if request.method == "POST":
        data = request.get_json(force=True)
        text = (data or {}).get("text", "").strip()
        if text:
            response = engine.process_command(text, source="web")
            return jsonify({"response": response})
        return jsonify({"ok": False}), 400
    return jsonify(db.get_all_reminders(limit=100))


@app.route("/api/reminders/<int:reminder_id>", methods=["DELETE"])
def api_delete_reminder(reminder_id):
    db.delete_reminder(reminder_id)
    return jsonify({"ok": True})


@app.route("/api/preferences", methods=["GET", "POST"])
def api_preferences():
    if request.method == "POST":
        data = request.get_json(force=True) or {}
        for k, v in data.items():
            db.set_preference(k, v)
        return jsonify({"ok": True})
    return jsonify(db.get_all_preferences())


def run_web_app():
    db.init_db()
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    run_web_app()
