import os

from cryptography.fernet import Fernet
from flask import Flask, flash, redirect, render_template, request, session, jsonify, request, abort
from flask_session import Session
from cs50 import SQL
from flask_wtf import CSRFProtect
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apologize, get_user_appointments
from datetime import datetime, timezone, timedelta

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
    # auth
    if request.headers.get("X-N8N-Token") != N8N_WEBHOOK_TOKEN:
        abort(401)

    payload = request.get_json(silent=True) or {}
    body = payload.get("body") if isinstance(payload.get("body"), dict) else payload

    # read fields (accept different casings)
    user_name = body.get("User_name") or body.get("user_name")
    mcgill_id = (body.get("Mcgill_id") or body.get("mcgill_id") or "").strip()
    reason    = body.get("Reason") or body.get("reason") or "General"
    date_str  = body.get("Date") or body.get("date")          # "YYYY-MM-DD"
    time_str  = body.get("Time") or body.get("time")          # "HH:MM"

    start_iso = body.get("startISO")

    # upsert user by mcgill_id (minimal)
    user_id = None
    if mcgill_id:
        rows = db.execute("SELECT id FROM users WHERE mcgill_id = ?", mcgill_id)
        if rows:
            user_id = rows[0]["id"]
        else:
            uname = user_name or f"user_{mcgill_id}"
            user_id = db.execute(
                "INSERT INTO users (username, mcgill_id, password_hash) VALUES (?, ?, ?)",
                uname, mcgill_id, generate_password_hash(mcgill_id)
            )
    def to_dt(iso, d, t):
        if iso:
            try: return datetime.fromisoformat(iso.replace("Z","+00:00"))
            except: pass
        if d and t:
            try: return datetime.strptime(f"{d} {t}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except: return None
        return None

    start_dt = to_dt(start_iso, date_str, time_str)
    if not start_dt:
        return jsonify({"ok": True, "note": "missing/invalid start time"}), 200

    # insert appointment
    appt_id = db.execute(
        """INSERT INTO appointments
           (user_id, kind, start_at, status, reason)
           VALUES (?, ?, ?, 'scheduled', ?)""", user_id, start_dt.isoformat(),
         reason
    )

    return jsonify({"ok": True, "appointment_id": appt_id})