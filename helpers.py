from flask import redirect, render_template, session
from functools import wraps
from datetime import datetime
from cs50 import SQL

db = SQL("sqlite:///database.db")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def apologize(message):
    return render_template("apology.html", message=message)

from datetime import datetime

def get_user_appointments(user_id: int):
    return db.execute("""
        SELECT
          id,
          kind,
          start_at,
          strftime('%Y-%m-%d', start_at) AS appt_date,
          strftime('%H:%M',     start_at) AS appt_time,
          status
        FROM appointments
        WHERE user_id = ?
        ORDER BY start_at ASC
    """, user_id)

def apologize(message):
    return render_template("apology.html", message=message)