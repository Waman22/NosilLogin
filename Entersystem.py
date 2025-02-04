from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'


""" Employee attendance tracking system that includes 
functionality for workers to sign in, record their attendance, 
and allow HR to view attendance records through a dashboard."""


""" Employee attendance tracking system that includes 
functionality for workers to sign in, record their attendance, 
and allow HR to view attendance records through a dashboard."""

def init_db():
    conn = sqlite3.connect('Employee_attendance.db')
    c = conn.cursor()

    # Create attendance table
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worker_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    sign_in_time TEXT,
                    sign_out_time TEXT,
                    status TEXT NOT NULL,
                    late_duration TEXT,
                    FOREIGN KEY (worker_id) REFERENCES workers(id))''')

    # Create workers table
    c.execute('''CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id TEXT UNIQUE,  
                name TEXT NOT NULL,
                surname TEXT NOT NULL,
                dob TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                cellphone TEXT NOT NULL,  
                id_number TEXT NOT NULL,  
                course TEXT NOT NULL,
                specialization TEXT NOT NULL,
                address TEXT NOT NULL,
                cohort TEXT NOT NULL,
                UNIQUE(name, surname))''')

    # Create absent table
    c.execute('''CREATE TABLE IF NOT EXISTS absent (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worker_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    FOREIGN KEY (worker_id) REFERENCES workers(id))''')

    # Create late table
    c.execute('''CREATE TABLE IF NOT EXISTS late (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worker_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    sign_in_time TEXT,
                    late_duration TEXT NOT NULL,
                    FOREIGN KEY (worker_id) REFERENCES workers(id))''')

    # Create present table
    c.execute('''CREATE TABLE IF NOT EXISTS present (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worker_id INTEGER NOT NULL,
                    sign_in_time TEXT,
                    date TEXT NOT NULL,
                    FOREIGN KEY (worker_id) REFERENCES workers(id))''')

    conn.commit()
    conn.close()

# Helper function to get database connection
def get_db_connection():
    conn = sqlite3.connect('Employee_attendance.db')
    conn.row_factory = sqlite3.Row
    return conn


# Add sample workers from the employee database into workers table
def add_sample_workers():
    conn = get_db_connection()
    c = conn.cursor()

    # Ensure employee.db has been attached correctly and has the 'employees' table
    try:
        c.execute('''ATTACH DATABASE 'employee.db' AS db1;''')

        # Copy employees data from employee.db (db1) to the workers table
        c.execute('''INSERT OR IGNORE INTO workers (worker_id, name, surname, dob, email,cellphone,id_number, course, specialization, address, cohort)
                     SELECT worker_id, name, surname, dob, email,cellphone,id_number, course, specialization, address, cohort
                     FROM db1.employees''')
        conn.commit()

    except sqlite3.OperationalError:
        print("Error: Could not attach employee.db or find employees table.")
    finally:
        conn.close()
        



@app.route('/')
def home():
    return render_template('attendance_form.html')

@app.route('/signin', methods=['POST'])
def signin():
    worker_id = request.form.get('worker_id')
    if not worker_id:
        return "Worker ID is required", 400

    now = datetime.now()
    current_time = now.strftime('%H:%M:%S')
    date = now.strftime('%Y-%m-%d')

    conn = get_db_connection()
    conn.execute('ATTACH DATABASE "employee.db" AS db1')

    # Fetch worker details
    worker = conn.execute('SELECT * FROM workers WHERE worker_id = ?', (worker_id,)).fetchone()
    if not worker:
        conn.close()
        return "Worker not found", 404

    # Check if the worker has already signed in today
    attendance = conn.execute(
        'SELECT * FROM attendance WHERE worker_id = ? AND date = ? AND sign_out_time IS NULL',
        (worker['id'], date)
    ).fetchone()
    if attendance:
        conn.close()
        return render_template('signed_in.html')

    # Determine status and late duration
    on_time_limit = datetime.strptime('07:00:00', '%H:%M:%S')
    too_late_limit = datetime.strptime('16:00:00', '%H:%M:%S')
    sign_in_time = datetime.strptime(current_time, '%H:%M:%S')

    if sign_in_time > too_late_limit:
        status = "Too Late"
        late_duration = sign_in_time - on_time_limit
        late_duration_str = str(late_duration).split('.')[0]
        conn.execute(
            'INSERT INTO late (worker_id, date,sign_in_time, late_duration) VALUES (?, ?, ?,?)',
            (worker['id'], date,current_time, late_duration_str)
        )
    else:
        status = "On Time"
        conn.execute(
            'INSERT INTO present (worker_id,sign_in_time, date) VALUES (?, ?,?)',
            (worker['id'], current_time,date)
        )

    # Insert into attendance table
    late_duration_str = None if status == "On Time" else late_duration_str
    conn.execute(
        '''INSERT INTO attendance (worker_id, date, sign_in_time, status, late_duration) 
           VALUES (?, ?, ?, ?, ?)''',
        (worker['id'], date, current_time, status, late_duration_str)
    )
    conn.commit()
    conn.close()

    session['worker_name'] = worker['name']
    session['status'] = status
    session['late_duration'] = late_duration_str
    session['arrival_time'] = current_time
    return redirect(url_for('logout'))



@app.route('/logout')
def logout():
    worker_name = session.get('worker_name', None)
    status = session.get('status', None)
    arrival_time = session.get('arrival_time', None)
    late_duration = session.get('late_duration', None)

    if not worker_name or not status:
        return "No active session found. Please sign in first.", 400

    return render_template(
        'logout.html',
        worker_name=worker_name,
        status=status,
        arrival_time=arrival_time,
        late_duration=late_duration
    )


@app.route('/signout', methods=['POST'])
def signout():
    worker_id = request.form.get('worker_id')
    if not worker_id:
        return "Worker ID is required", 400

    now = datetime.now()
    current_time = now.strftime('%H:%M:%S')
    date = now.strftime('%Y-%m-%d')

    # Define the knocking-out time (e.g., 17:00:00)
    knocking_out_time = datetime.strptime('17:00:00', '%H:%M:%S')

    # Check if the current time is earlier than the knocking-out time
    current_time_obj = datetime.strptime(current_time, '%H:%M:%S')
    if current_time_obj < knocking_out_time:
        return f"You cannot sign out before the knocking-out time of {knocking_out_time.strftime('%H:%M:%S')}.", 400

    # Attach employee database to fetch worker details
    conn = get_db_connection()
    conn.execute('ATTACH DATABASE "employee.db" AS db1')

    # Check if the worker is signed in but not signed out yet
    attendance = conn.execute(
        'SELECT * FROM attendance WHERE worker_id = ? AND date = ? AND sign_out_time IS NULL',
        (worker_id, date)
    ).fetchone()

    if not attendance:
        conn.close()
        return "You have not signed in or have already signed out today.", 400

    # Update the attendance record with sign-out time
    conn.execute(
        'UPDATE attendance SET sign_out_time = ? WHERE id = ?',
        (current_time, attendance['id'])
    )
    conn.commit()
    conn.close()

    return render_template('signout.html', time=current_time)


@app.route('/hr_dashboard')
def hr_dashboard():
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db_connection()

    # Fetch present employees
    present = conn.execute('''
    SELECT w.name, w.surname, strftime('%H:%M:%S', p.sign_in_time) AS sign_in_time, p.date
    FROM present p
    JOIN workers w ON w.id = p.worker_id
    WHERE p.date = ?
''', (today,)).fetchall()


    # Fetch late employees
    late = conn.execute('''
        SELECT w.name, w.surname, l.date,l.sign_in_time, l.late_duration
        FROM late l
        JOIN workers w ON w.id = l.worker_id
        WHERE l.date = ?
    ''', (today,)).fetchall()

    # Fetch absent employees
    absent = conn.execute('''
        SELECT w.name, w.surname
        FROM workers w
        WHERE w.id NOT IN (
            SELECT a.worker_id FROM attendance a WHERE a.date = ?
        )
    ''', (today,)).fetchall()

    conn.close()

    return render_template(
        'hr_dashboard.html',
        present=present,
        late=late,
        absent=absent,
        date=today
    )

if __name__ == '__main__':
    init_db()
    add_sample_workers()
    app.run(debug=True,port= 5001)
