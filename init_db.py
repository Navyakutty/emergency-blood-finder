import sqlite3

def initialize_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # 1. DONOR TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            profile_pic TEXT DEFAULT 'default.png',
            password TEXT NOT NULL,
            is_available INTEGER DEFAULT 1
        )
    ''')

    # 2. HOSPITAL TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_name TEXT NOT NULL,
            address TEXT NOT NULL,
            contact_number TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')

    # 3. EMERGENCY REQUESTS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emergency_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id INTEGER,
            blood_group TEXT,
            emergency_level TEXT,
            units INTEGER,
            status TEXT DEFAULT 'Active'
        )
    ''')

    # 4. NOTIFICATIONS TABLE (New!)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER,
            donor_id INTEGER,
            message TEXT,
            is_read INTEGER DEFAULT 0
        )
    ''')

    # 5. ACCEPTED DONATIONS TABLE (New! This fixes your error)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accepted_donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER,
            donor_id INTEGER,
            estimated_arrival_time TEXT,
            status TEXT DEFAULT 'Accepted'
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database updated successfully with ALL tables!")

if __name__ == '__main__':
    initialize_database()