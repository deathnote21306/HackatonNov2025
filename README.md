# 🩺 McGill Medical AI Assistant (MAIS 2025)

This project is an **AI medical appointment assistant** built by McGill students for the MAIS 2025 Hackathon.  
It listens to patient calls (via ElevenLabs), extracts appointment details, and books them automatically using Flask, SQLite, and n8n.

---

## ⚙️ Setup Instructions

### 1. Clone the project
```bash
git clone https://github.com/<your-username>/<repo>.git
cd <repo>
```

### 2. Create a virtual environment
```bash
python -m venv .venv
. .\.venv\Scripts\Activate.ps1    # Windows
# or
source .venv/bin/activate            # macOS/Linux
```

### 3. Install dependencies
```bash
pip install flask flask-session flask-wtf python-dotenv cryptography cs50
```

### 4. Create a `.env` file
Create a file named `.env` in your project folder:
```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=dev-key-change-me
DATABASE_URL=sqlite:///app.db
N8N_WEBHOOK_TOKEN=super-secret-token
FERNET_KEY=<paste-generated-key>
```
To generate a Fernet key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## 🗄️ Database Setup
Run these commands to create your tables:
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

### Optional: Add a test user
Generate a password hash:
```bash
python - <<'PY'
from werkzeug.security import generate_password_hash
print(generate_password_hash("test123"))
PY
```

Then open `sqlite3 app.db` and run:
```sql
INSERT INTO users (username, password_hash, mcgill_id)
VALUES ('williams', '<PASTE_HASH>', '261167713');
```

---

## ▶️ Run the app
```bash
flask run
```
Then visit:
👉 [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🌐 Connect n8n or ElevenLabs
Your webhook endpoint (in `app.py`):
```
POST /webhooks/elevenlabs
```

Example request body:
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

---

## 🧠 Workflow Summary
1. **ElevenLabs Agent** → captures user intent (“Book me a checkup next Tuesday”)
2. **n8n Workflow** → converts date/time to ISO and checks availability
3. **Flask Webhook** → receives the final appointment and saves it in SQLite
4. **Website (Flask)** → displays “Next Appointment” for logged-in users

---

## 💡 Tips
- Run Flask in VS Code terminal inside `.venv`
- Add `.env` to `.gitignore`
- If testing n8n locally, expose your Flask server using:
  ```bash
  npx localtunnel --port 5000
  ```

---

## 👥 Team
Built by McGill U1 & U2 students — MAIS 2025 Hackathon

