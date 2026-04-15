<h1 align="center">McGill Medical AI Assistant</h1>

<p align="center">
  <strong>A voice-first appointment booking system for clinics — call in, talk to an AI receptionist, get booked.</strong><br/>
  Built for the McGill AI Society (MAIS) 2025 Hackathon. 4th place out of ~40 teams.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/n8n-EA4B71?style=flat&logo=n8n&logoColor=white" />
  <img src="https://img.shields.io/badge/ElevenLabs-Voice-000000?style=flat" />
  <img src="https://img.shields.io/badge/MAIS%202025-4th%20Place-gold?style=flat" />
</p>

---

## What is this?

A patient calls a phone number. An ElevenLabs voice agent picks up, has a natural conversation — "I'd like to book a physical next Tuesday afternoon" — extracts the intent, and forwards the structured details to an n8n workflow. n8n normalizes the date and time, verifies the slot, and hits a Flask webhook that writes the appointment to a SQLite database. When the patient logs into the clinic's web portal, their upcoming appointment is already there.

End to end: **voice → LLM intent extraction → automation workflow → backend → patient portal.** No keyboard involved.

---

## Why we built it

Clinic receptionists spend a huge portion of their day on the phone doing the same three tasks: identifying the caller, finding a slot, writing it down. It's repetitive, error-prone, and bottlenecks the rest of the clinic.

We wanted to see how far you could get in 24 hours by stitching together the three pieces that have recently become good enough to replace that workflow — conversational voice AI, low-code automation, and a tiny backend. The judges seemed to like the answer: we placed **4th out of about 40 teams**, with a task-completion rate around **90%** across our test calls.

---

## How it works

```
   ┌───────────┐     ┌──────────────┐     ┌──────────────┐     ┌───────────────┐
   │  Patient  │ --> │  ElevenLabs  │ --> │     n8n      │ --> │    Flask      │
   │   call    │     │  voice agent │     │  workflow    │     │   webhook     │
   └───────────┘     └──────────────┘     └──────────────┘     └──────┬────────┘
                     Captures intent       Normalizes date/time,              │
                     and entities          validates, forwards        writes to DB
                                                                              │
                                                                      ┌───────▼───────┐
                                                                      │ SQLite +      │
                                                                      │ Flask portal  │
                                                                      └───────────────┘
                                                                      Patient logs in
                                                                      and sees booking
```

**Step by step:**

1. **Voice capture** — ElevenLabs runs a conversational agent tuned for clinic bookings. It asks the caller for name, McGill ID, reason, and preferred time.
2. **Intent to JSON** — The agent emits a structured payload (`User_name`, `Mcgill_id`, `Reason`, `Date`, `Time`, `duration`).
3. **n8n workflow** — Parses the natural-language date ("next Tuesday at 2") into ISO format, checks for conflicts, and posts the final payload to our Flask webhook.
4. **Flask backend** — Authenticates the request with a shared token, looks up the user by McGill ID, and inserts the appointment into SQLite.
5. **Patient portal** — A small Flask website with login / sign-up lets users see their "Next Appointment" card, styled to match a real clinic dashboard.

Sensitive fields are encrypted at rest using a **Fernet** key loaded from `.env`, and passwords are hashed with Werkzeug.

---

## Tech stack

| Layer | Tool |
|---|---|
| Voice agent | ElevenLabs Conversational AI |
| Orchestration | n8n (self-hosted workflow) |
| Web backend | Flask + Flask-Session + Flask-WTF |
| Database | SQLite (via CS50's `SQL` wrapper) |
| Security | Werkzeug password hashing, Fernet symmetric encryption, CSRF protection |
| Frontend | Jinja2 templates + static CSS |

---

## Install & run locally

```bash
git clone https://github.com/deathnote21306/HackatonNov2025.git
cd HackatonNov2025

python -m venv .venv
source .venv/bin/activate            # Windows: .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Create a `.env`:

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=dev-key-change-me
DATABASE_URL=sqlite:///app.db
N8N_WEBHOOK_TOKEN=super-secret-token
FERNET_KEY=<paste-generated-key>
```

Generate a Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Initialize the database (`sqlite3 database.db`):

```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  mcgill_id TEXT
);

CREATE TABLE appointments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  kind TEXT,
  start_at TEXT NOT NULL,
  status TEXT DEFAULT 'confirmed'
);
```

Run:

```bash
flask run
```

Open <http://127.0.0.1:5000>.

---

## Connecting n8n / ElevenLabs

The webhook endpoint lives at:

```
POST /webhooks/elevenlabs
```

Expected payload:

```json
{
  "User_name": "williams",
  "Mcgill_id": "261167713",
  "Reason": "physical",
  "Date": "2025-11-05",
  "Time": "14:00",
  "duration": 40
}
```

Include the shared `N8N_WEBHOOK_TOKEN` for authentication. For local testing, expose Flask with:

```bash
npx localtunnel --port 5000
```

The exported n8n workflow (`AI Appointment Booking (Fixed).json`) and a link to the hosted ElevenLabs agent live at the repo root.

---

## Project layout

```
app.py                              Flask routes, auth, webhook handler
helpers.py                          Shared utilities (apology page, appointment queries)
templates/                          Jinja2 pages: login, sign-up, dashboard
static/                             Stylesheets and assets
AI Appointment Booking (Fixed).json Exported n8n workflow
AI Receptionist Link                ElevenLabs agent URL
requirements.txt                    Python dependencies
```

---

## Design decisions worth noting

- **Let specialized tools do what they're good at.** ElevenLabs handles voice, n8n handles the messy date-parsing and branching logic, Flask just stores the result. Gluing three simple things beats building one complicated thing in a hackathon.
- **Shared-token webhook auth.** Simple, sufficient for the demo, and easy to rotate.
- **Encrypt sensitive fields at rest.** Medical context raised the bar on what "good enough" meant even for a 24-hour build.
- **Server-rendered portal.** Flask + Jinja templates kept the frontend to a couple of files so we could spend the weekend on the voice pipeline.

---

## Team

Built by McGill U1 & U2 students at the MAIS 2025 Hackathon.

---

Part of [William's portfolio](https://deathnote21306.github.io/).
