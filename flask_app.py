from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'emergency_blood_secret_key'

# Setup path for Render (Cloud environment)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Self-healing: Create tables if they don't exist
    conn.execute('CREATE TABLE IF NOT EXISTS donors (id INTEGER PRIMARY KEY, name TEXT, blood_group TEXT, phone TEXT, address TEXT, password TEXT, profile_pic TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS hospitals (id INTEGER PRIMARY KEY, hospital_name TEXT, address TEXT, contact_number TEXT, password TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS emergency_requests (id INTEGER PRIMARY KEY, hospital_id INTEGER, blood_group TEXT, emergency_level TEXT, units INTEGER, status TEXT DEFAULT "Active")')
    conn.execute('CREATE TABLE IF NOT EXISTS accepted_donations (id INTEGER PRIMARY KEY, request_id INTEGER, donor_id INTEGER, estimated_arrival_time TEXT, status TEXT DEFAULT "Pending")')
    conn.commit()
    return conn

@app.route('/')
def home():
    db = get_db()
    try:
        total_donors = db.execute('SELECT COUNT(*) FROM donors').fetchone()[0]
        total_hospitals = db.execute('SELECT COUNT(*) FROM hospitals').fetchone()[0]
        lives_saved = db.execute("SELECT COUNT(*) FROM accepted_donations WHERE status = 'Completed'").fetchone()[0]
    except:
        total_donors, total_hospitals, lives_saved = 0, 0, 0
    db.close()
    return render_template('base.html', total_donors=total_donors, total_hospitals=total_hospitals, lives_saved=lives_saved)

# --- Add your other existing routes here (registration, login, dashboard, etc.) ---
# Ensure all your routes end with db.close()

if __name__ == '__main__':
    app.run()
