from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'cute_secret_key_for_rosy_crimson'

# ☁️ CLOUD SAFE PATHS: This guarantees the server never loses your folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 🔥 UPDATED HOMEPAGE WITH LIVE STATS
@app.route('/')
def home():
    db = get_db()
    try:
        total_donors = db.execute('SELECT COUNT(*) FROM donors').fetchone()[0]
        total_hospitals = db.execute('SELECT COUNT(*) FROM hospitals').fetchone()[0]
        lives_saved = db.execute("SELECT COUNT(*) FROM accepted_donations WHERE status = 'Completed'").fetchone()[0]
    except:
        # Failsafe just in case the database is empty
        total_donors, total_hospitals, lives_saved = 0, 0, 0
    finally:
        db.close()
    
    return render_template('base.html', 
                           total_donors=total_donors, 
                           total_hospitals=total_hospitals, 
                           lives_saved=lives_saved)

# ==========================================
# 🌸 DONOR ROUTES
# ==========================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name, blood_group = request.form['name'], request.form['blood_group']
        phone, address, password = request.form['phone'], request.form['address'], request.form['password']

        pic_filename = 'default.png'
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file.filename != '':
                pic_filename = file.filename.replace(" ", "_")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_filename))

        db = get_db()
        try:
            db.execute('INSERT INTO donors (name, blood_group, phone, address, password, profile_pic) VALUES (?, ?, ?, ?, ?, ?)',
                       (name, blood_group, phone, address, password, pic_filename))
            db.commit()
        except Exception as e:
            print("Error:", e)
        finally:
            db.close()
        return redirect(url_for('home'))
    return render_template('register_donor.html')

@app.route('/login-donor', methods=['GET', 'POST'])
def login_donor():
    error = None
    if request.method == 'POST':
        db = get_db()
        donor = db.execute('SELECT * FROM donors WHERE phone = ? AND password = ?', (request.form['phone'], request.form['password'])).fetchone()
        db.close()
        if donor:
            session['donor_id'] = donor['id']
            return redirect(url_for('donor_dashboard'))
        else:
            error = "❌ Account not found or wrong password!"
    return render_template('login_donor.html', error=error)

@app.route('/donor-dashboard')
def donor_dashboard():
    if 'donor_id' not in session: return redirect(url_for('login_donor'))
    db = get_db()
    donor = db.execute('SELECT * FROM donors WHERE id = ?', (session['donor_id'],)).fetchone()
    
    matching_requests = db.execute('''
        SELECT emergency_requests.*, hospitals.hospital_name, hospitals.address, hospitals.contact_number 
        FROM emergency_requests 
        JOIN hospitals ON emergency_requests.hospital_id = hospitals.id 
        WHERE emergency_requests.blood_group = ? AND emergency_requests.status = 'Active'
        ORDER BY emergency_requests.id DESC
    ''', (donor['blood_group'],)).fetchall()
    
    bags_donated = db.execute("SELECT COUNT(*) FROM accepted_donations WHERE donor_id = ? AND status = 'Completed'", (session['donor_id'],)).fetchone()[0]
    db.close()
    
    return render_template('donor_dashboard.html', donor=donor, requests=matching_requests, bags_donated=bags_donated)

@app.route('/screen/<int:request_id>')
def screen(request_id):
    if 'donor_id' not in session: return redirect(url_for('login_donor'))
    return render_template('screening.html', request_id=request_id)

@app.route('/process-screening/<int:request_id>', methods=['POST'])
def process_screening(request_id):
    if 'donor_id' not in session: return redirect(url_for('login_donor'))
    if 'yes' in [request.form.get(f'q{i}') for i in range(1, 5)]:
        return "<script>alert('You are currently not eligible for donation. Please take care and donate next time! 🌸'); window.location.href='/donor-dashboard';</script>"
    return redirect(url_for('eta', request_id=request_id))

@app.route('/eta/<int:request_id>', methods=['GET', 'POST'])
def eta(request_id):
    if 'donor_id' not in session: return redirect(url_for('login_donor'))
    if request.method == 'POST':
        db = get_db()
        db.execute('INSERT INTO accepted_donations (request_id, donor_id, estimated_arrival_time) VALUES (?, ?, ?)',
                   (request_id, session['donor_id'], request.form['arrival_time']))
        db.commit()
        db.close()
        return "<script>alert('✅ Thank you! The hospital has been notified and is expecting you.'); window.location.href='/donor-dashboard';</script>"
    return render_template('eta.html', request_id=request_id)

# ==========================================
# 🏥 HOSPITAL ROUTES
# ==========================================
@app.route('/register-hospital', methods=['GET', 'POST'])
def register_hospital():
    error = None
    if request.method == 'POST':
        db = get_db()
        try:
            db.execute('INSERT INTO hospitals (hospital_name, address, contact_number, password) VALUES (?, ?, ?, ?)',
                       (request.form['hospital_name'], request.form['address'], request.form['contact_number'], request.form['password']))
            db.commit()
            return "<script>alert('Hospital Registered Successfully! 🏥'); window.location.href='/login-hospital';</script>"
        except:
            error = "❌ This contact number is already registered!"
        finally:
            db.close()
    return render_template('register_hospital.html', error=error)

@app.route('/login-hospital', methods=['GET', 'POST'])
def login_hospital():
    error = None
    if request.method == 'POST':
        db = get_db()
        hospital = db.execute('SELECT * FROM hospitals WHERE hospital_name = ? AND password = ?', (request.form['hospital_name'], request.form['password'])).fetchone()
        db.close()
        if hospital:
            session['hospital_id'] = hospital['id']
            session['hospital_name'] = hospital['hospital_name']
            return redirect(url_for('hospital_dashboard'))
        else:
            error = "❌ Hospital not found or wrong password!"
    return render_template('login_hospital.html', error=error)

@app.route('/hospital-dashboard')
def hospital_dashboard():
    if 'hospital_id' not in session: return redirect(url_for('login_hospital'))
    db = get_db()
    hospital_id = session['hospital_id']
    active_requests = db.execute('SELECT * FROM emergency_requests WHERE hospital_id = ? ORDER BY id DESC', (hospital_id,)).fetchall()
    accepted_donors = db.execute('''
        SELECT accepted_donations.*, donors.name, donors.phone, donors.blood_group, emergency_requests.emergency_level
        FROM accepted_donations
        JOIN emergency_requests ON accepted_donations.request_id = emergency_requests.id
        JOIN donors ON accepted_donations.donor_id = donors.id
        WHERE emergency_requests.hospital_id = ?
        ORDER BY accepted_donations.id DESC
    ''', (hospital_id,)).fetchall()
    db.close()
    return render_template('hospital_dashboard.html', hospital_name=session['hospital_name'], requests=active_requests, accepted_donors=accepted_donors)

@app.route('/broadcast-emergency', methods=['POST'])
def broadcast_emergency():
    if 'hospital_id' not in session: return redirect(url_for('login_hospital'))
    db = get_db()
    db.execute('INSERT INTO emergency_requests (hospital_id, blood_group, emergency_level, units) VALUES (?, ?, ?, ?)', 
               (session['hospital_id'], request.form['blood_group'], request.form['urgency'], request.form['units']))
    db.commit()
    db.close()
    return redirect(url_for('hospital_dashboard'))

@app.route('/complete-donation/<int:donation_id>', methods=['POST'])
def complete_donation(donation_id):
    if 'hospital_id' not in session: return redirect(url_for('login_hospital'))
    db = get_db()
    db.execute("UPDATE accepted_donations SET status = 'Completed' WHERE id = ?", (donation_id,))
    db.commit()
    db.close()
    return redirect(url_for('hospital_dashboard'))

# ==========================================
# ⚙️ SYSTEM ROUTES
# ==========================================
@app.route('/setup-test-hospital')
def setup_test_hospital():
    db = get_db()
    try:
        db.execute("INSERT INTO hospitals (hospital_name, address, contact_number, password) VALUES ('Apollo', 'City Center', '9999999999', '1234')")
        db.commit()
    except:
        pass 
    finally:
        db.close()
    return redirect(url_for('login_hospital'))

if __name__ == '__main__':
    app.run(debug=True)