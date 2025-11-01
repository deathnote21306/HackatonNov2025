import os

from cryptography.fernet import Fernet
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from flask_wtf import CSRFProtect
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apologize, login_required

app = Flask(__name__)

app.config['SECRET_KEY'] = 'dev-change-me'
csrf = CSRFProtect(app)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///app.db")

load_dotenv()

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
        return render_template("user_panel.html")
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
    if session.get("user_id"):
        return render_template("user_panel.html")
    else:
        return render_template("index.html")



