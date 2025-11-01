import os

from cryptography.fernet import Fernet
from flask import Flask, flash, redirect, render_template, request, session, jsonify, request, abort
from flask_session import Session
from cs50 import SQL
from flask_wtf import CSRFProtect
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apologize, get_user_appointments
from datetime import datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = 'dev-change-me'
csrf = CSRFProtect(app)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///database.db")

load_dotenv()

N8N_WEBHOOK_TOKEN = os.getenv("N8N_WEBHOOK_TOKEN", "super-secret")

FERNET_KEY = os.getenv("FERNET_KEY")
fernet = Fernet(FERNET_KEY)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@app.route("/index")
def index():
    if session.get("user_id"):
        return redirect("/user_panel")
    else:
        return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()

    if request.method == "POST":
        if not request.form.get("login_username"):
            return apologize("must provide username")

        elif not request.form.get("login_password"):
            return apologize("must provide password")

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("login_username")
        )

        if len(rows) != 1 or not check_password_hash(
            rows[0]["password_hash"], request.form.get("login_password")
        ):
            return apologize("invalid username and/or password")

        session["user_id"] = rows[0]["id"]

        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        if not request.form.get("username"):
            return apologize("must provide username")

        rows = db.execute("SELECT id FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) > 0:
            return apologize("username already taken")


        elif not request.form.get("password"):
            return apologize("must provide password")

        elif not request.form.get("confirmation"):
            return apologize("must provide confirmation")

        elif request.form.get("password") != request.form.get("confirmation"):
            return apologize("passwords must match")

        hash = generate_password_hash(request.form.get("password"))

        new_id = db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            request.form.get("username"),
            hash,
        )
        session["user_id"] = new_id

        return render_template("user_panel.html")
    else:
        return render_template("register.html")
    

@app.route("/user_panel")
def user_panel():
    if not session.get("user_id"):
        return redirect("/login")

    user_id = session["user_id"]
    appointments = get_user_appointments(user_id)

    return render_template(
        "user_panel.html",
        appointments=appointments
    )



@app.post("/webhooks/elevenlabs")
def elevenlabs_webhook():
    if request.headers.get("X-N8N-Token") != N8N_WEBHOOK_TOKEN:
        abort(401)

    data = request.get_json(silent=True) or {}

    # Expect n8n to send at least: user_id, transcript
    user_id      = data.get("user_id")            # int
    transcript   = data.get("transcript", "")     # str
    start_at     = data.get("start_at")           # 'YYYY-MM-DD HH:MM'  (optional)
    kind         = (data.get("kind") or "Consultation").strip()
    language     = data.get("language")
    caller       = data.get("caller")
    call_sid     = data.get("callSid")
    recording    = data.get("recordingUrl")

    # Always store raw payload for debugging/audit
    db.execute(
        "INSERT INTO call_transcripts (user_id, caller, call_sid, recording_url, transcript, language) VALUES (?, ?, ?, ?, ?, ?)",
        user_id, caller, call_sid, recording, transcript, language
    )

    # If we don't have a user_id or a parsed datetime yet, stop after storing transcript.
    if not user_id:
        return {"ok": True, "note": "stored transcript (missing user_id)"}

    # If n8n already parsed date/time, just use it. Otherwise, skip creating an appointment here.
    if not start_at:
        return {"ok": True, "note": "stored transcript (no start_at provided)"}

    # (Optional) sanity check: must look like 'YYYY-MM-DD HH:MM'
    try:
        datetime.strptime(start_at, "%Y-%m-%d %H:%M")
    except ValueError:
        return {"ok": True, "note": "start_at not in 'YYYY-MM-DD HH:MM' format"}

    # Create the appointment
    db.execute(
        "INSERT INTO appointments (user_id, kind, start_at, status) VALUES (?, ?, ?, ?)",
        user_id, kind, start_at, "pending"
    )

    return {"ok": True, "created": {"user_id": user_id, "kind": kind, "start_at": start_at}}