from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

""" Employee attendance tracking system that includes 
functionality for workers to sign in, record their attendance, 
and allow HR to view attendance records through a dashboard."""

# Initialize SQLite database
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

    # Create workers table in the attendance database if it does not exist
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
                UNIQUE(name, surname) 
            )''')
    
    
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

    # Attach employee database to fetch worker details
    conn = get_db_connection()
    conn.execute('ATTACH DATABASE "employee.db" AS db1')

    # Fetch worker data from the employee database
    worker = conn.execute('SELECT * FROM db1.employees WHERE worker_id = ?', (worker_id,)).fetchone()

    if not worker:
        conn.close()
        return "Worker not found", 404

    # Check if the worker has already signed in today
    attendance = conn.execute(
        'SELECT * FROM attendance WHERE worker_id = ? AND date = ? AND sign_out_time IS NULL',
        (worker_id, date)
    ).fetchone()
    
    if attendance:
        conn.close()
        return render_template('signed_in.html')

    # Define starting and "too late" times
    on_time_limit = datetime.strptime('16:00:00', '%H:%M:%S')
    too_late_limit = datetime.strptime('16:30:00', '%H:%M:%S')
    sign_in_time = datetime.strptime(current_time, '%H:%M:%S')

    if sign_in_time > too_late_limit:
        status = "Too Late"
        late_duration = sign_in_time - on_time_limit
        late_duration_str = str(late_duration).split('.')[0]  # Remove microseconds
        conn.close()
        return render_template('too_late.html', time=current_time, late_duration=late_duration_str)

    # Determine if the worker is late
    status = "On Time" if sign_in_time <= on_time_limit else "Late"

    late_duration = None
    if status == "Late":
        late_duration = sign_in_time - on_time_limit
        late_duration_str = str(late_duration).split('.')[0]  # Remove microseconds
    else:
        late_duration_str = None

    # Save attendance with sign-in time
    conn.execute(
        '''INSERT INTO attendance (worker_id, date, sign_in_time, status, late_duration) 
           VALUES (?, ?, ?, ?, ?)''',
        (worker_id, date, current_time, status, late_duration_str)
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

    # Attach employee database to fetch worker names
    conn.execute('ATTACH DATABASE "employee.db" AS db1')

    # Get attendance for today
    attendance = conn.execute(
        '''SELECT w.name, a.date, a.sign_in_time, a.status, a.late_duration, a.sign_out_time 
           FROM workers w 
           LEFT JOIN attendance a 
           ON w.id = a.worker_id AND a.date = ? 
           ORDER BY w.name''', (today,)
    ).fetchall()
    conn.close()
    return render_template('hr_dashboard.html', attendance=attendance, date=today)

if __name__ == '__main__':
    init_db()
    add_sample_workers()
    app.run(debug=True) 