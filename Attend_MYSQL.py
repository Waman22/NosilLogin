from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL connection settings
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '@Ftsvolvl9',
    'database': 'NEW_WORKERS_database'
}

# Function to connect to MySQL server without specifying a database
def create_server_connection():
    try:
        connection = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        if connection.is_connected():
            print("Connected to MySQL server")
        return connection
    except Error as e:
        print("Error while connecting to MySQL server:", e)
        return None

# Function to create the database if it doesn't exist
def create_database():
    connection = create_server_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("CREATE DATABASE IF NOT EXISTS NEW_WORKERS_database")
            print("Database 'NEW_WORKERS_database' created or already exists.")
            connection.commit()
        except Error as e:
            print("Error while creating database:", e)
        finally:
            cursor.close()
            connection.close()

# Function to connect to the specified database
def create_database_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("Connected to 'NEW_WORKERS_database'")
        return connection
    except Error as e:
        print("Error while connecting to 'NEW_WORKERS_database':", e)
        return None

def init_db():
    conn = create_database_connection()
    if conn:
        try:
            c = conn.cursor()

            # Create workers table
            c.execute('''CREATE TABLE IF NOT EXISTS workers (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        worker_id VARCHAR(50) UNIQUE,  
                        name VARCHAR(50) NOT NULL,
                        surname VARCHAR(50) NOT NULL,
                        dob DATE NOT NULL,
                        email VARCHAR(100) NOT NULL UNIQUE,
                        cellphone VARCHAR(20) NOT NULL,  
                        id_number VARCHAR(50) NOT NULL,  
                        course VARCHAR(100) NOT NULL,
                        specialization VARCHAR(100) NOT NULL,
                        address TEXT NOT NULL,
                        cohort VARCHAR(50) NOT NULL,
                        UNIQUE(name, surname))''')

            # Create attendance table
            c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        worker_id INT NOT NULL,
                        date DATE NOT NULL,
                        sign_in_time TIME,
                        sign_out_time TIME,
                        status VARCHAR(50) NOT NULL,
                        late_duration TIME,
                        FOREIGN KEY (worker_id) REFERENCES workers(id))''')

            # Create absent table
            c.execute('''CREATE TABLE IF NOT EXISTS absent (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        worker_id INT NOT NULL,
                        date DATE NOT NULL,
                        FOREIGN KEY (worker_id) REFERENCES workers(id))''')

            # Create late table
            c.execute('''CREATE TABLE IF NOT EXISTS late (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        worker_id INT NOT NULL,
                        date DATE NOT NULL,
                        sign_in_time TIME,
                        late_duration TIME NOT NULL,
                        FOREIGN KEY (worker_id) REFERENCES workers(id))''')

            # Create present table
            c.execute('''CREATE TABLE IF NOT EXISTS present (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        worker_id INT NOT NULL,
                        sign_in_time TIME,
                        date DATE NOT NULL,
                        FOREIGN KEY (worker_id) REFERENCES workers(id))''')

            conn.commit()

        except mysql.connector.Error as err:
            print(f"Error creating tables: {err}")

        finally:
            conn.close()

def add_sample_workers():
    conn = create_database_connection()  # Connect to the NEW_WORKERS_database
    if conn:
        try:
            c = conn.cursor()

            # Connect to Worker_database for retrieving employee data
            worker_db_config = {
                'host': 'localhost',
                'user': 'root',
                'password': '@Ftsvolvl9',
                'database': 'Worker_database'  # Change this to the correct database where employees are stored
            }

            # Establish a new connection to Worker_database
            worker_conn = mysql.connector.connect(**worker_db_config)

            if worker_conn:
                worker_cursor = worker_conn.cursor()

                # Ensure the employees table exists in Worker_database
                worker_cursor.execute('''SHOW TABLES LIKE 'employees';''')
                result = worker_cursor.fetchone()

                if result:
                    print("Employees table exists, proceeding with data insertion.")

                    # Insert data from Worker_database.employees into NEW_WORKERS_database.workers
                    worker_cursor.execute('''SELECT worker_id, name, surname, dob, email, cellphone, id_number, course, specialization, address, cohort
                                              FROM employees''')
                    employees_data = worker_cursor.fetchall()

                    # Insert the fetched employee data into the workers table
                    for employee in employees_data:
                        c.execute('''INSERT IGNORE INTO workers (worker_id, name, surname, dob, email, cellphone, id_number, course, specialization, address, cohort)
                                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', employee)

                    conn.commit()
                    print("Data inserted successfully.")
                else:
                    print("Error: 'employees' table does not exist in Worker_database.")
                
                # Close Worker_database connection
                worker_cursor.close()
                worker_conn.close()

        except mysql.connector.Error as err:
            print(f"Error: {err}")

        finally:
            conn.close()


            
create_database()  # Make sure database exists before the app runs
init_db()  # Initialize tables after the database creation
            
@app.route('/')
def home():
    return render_template('attendance_form.html')

@app.route('/signin', methods=['POST'])
def signin():
    worker_id = request.form.get('worker_id')
    if not worker_id:
        flash("Worker ID is required", "error")
        return redirect(url_for('home'))

    now = datetime.now()
    current_time = now.strftime('%H:%M:%S')
    date = now.strftime('%Y-%m-%d')

    conn = create_database_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch worker details
    cursor.execute('SELECT * FROM workers WHERE worker_id = %s', (worker_id,))
    worker = cursor.fetchone()
    if not worker:
        conn.close()
        flash("Worker not found", "error")
        return redirect(url_for('home'))

    # Check if the worker has already signed in today
    cursor.execute(
        'SELECT * FROM attendance WHERE worker_id = %s AND date = %s AND sign_out_time IS NULL',
        (worker['id'], date)
    )
    attendance = cursor.fetchone()
    if attendance:
        conn.close()
        flash("Already signed in today", "info")
        return redirect(url_for('home'))

    # Determine status and late duration
    on_time_limit = datetime.strptime('07:00:00', '%H:%M:%S')
    too_late_limit = datetime.strptime('08:00:00', '%H:%M:%S')
    sign_in_time = datetime.strptime(current_time, '%H:%M:%S')

    if sign_in_time > too_late_limit:
        status = "Too Late"
        late_duration = sign_in_time - on_time_limit
        late_duration_str = str(late_duration).split('.')[0]
        cursor.execute(
            'INSERT INTO late (worker_id, date, sign_in_time, late_duration) VALUES (%s, %s, %s, %s)',
            (worker['id'], date, current_time, late_duration_str)
        )
    else:
        status = "On Time"
        cursor.execute(
            'INSERT INTO present (worker_id, sign_in_time, date) VALUES (%s, %s, %s)',
            (worker['id'], current_time, date)
        )

    # Insert into attendance table
    late_duration_str = None if status == "On Time" else late_duration_str
    cursor.execute(
        '''INSERT INTO attendance (worker_id, date, sign_in_time, status, late_duration) 
           VALUES (%s, %s, %s, %s, %s)''',
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
        flash("No active session found. Please sign in first.", "error")
        return redirect(url_for('home'))

    session.clear()  # Clear session after logging out
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
        flash("Worker ID is required", "error")
        return redirect(url_for('home'))

    now = datetime.now()
    current_time = now.strftime('%H:%M:%S')
    date = now.strftime('%Y-%m-%d')

    # Define the knocking-out time (e.g., 17:00:00)
    knocking_out_time = datetime.strptime('17:00:00', '%H:%M:%S')

    # Check if the current time is earlier than the knocking-out time
    current_time_obj = datetime.strptime(current_time, '%H:%M:%S')
    if current_time_obj < knocking_out_time:
        flash(f"You cannot sign out before the knocking-out time of {knocking_out_time.strftime('%H:%M:%S')}.", "error")
        return redirect(url_for('home'))

    # Attach employee database to fetch worker details
    conn = create_database_connection()
    cursor = conn.cursor(dictionary=True)

    # Check if the worker is signed in but not signed out yet
    cursor.execute(
        'SELECT * FROM attendance WHERE worker_id = %s AND date = %s AND sign_out_time IS NULL',
        (worker_id, date)
    )
    # Check if worker is absent
    cursor.execute('''INSERT INTO absent (worker_id, date)
                   SELECT id, %s FROM workers
                   WHERE id NOT IN (SELECT worker_id FROM attendance WHERE date = %s)''', (date, date))

    attendance = cursor.fetchone()

    if not attendance:
        conn.close()
        flash("You have not signed in or have already signed out today.", "error")
        return redirect(url_for('home'))

    # Update the attendance record with sign-out time
    cursor.execute(
        'UPDATE attendance SET sign_out_time = %s WHERE id = %s',
        (current_time, attendance['id'])
    )
    conn.commit()
    conn.close()

    return render_template('signout.html', time=current_time)



@app.route('/hr_dashboard')
def hr_dashboard():
    today = datetime.now().strftime('%Y-%m-%d')
    conn = create_database_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch present employees
    cursor.execute(''' 
        SELECT w.name, w.surname, TIME(p.sign_in_time) AS sign_in_time, p.date
        FROM present p
        JOIN workers w ON w.id = p.worker_id
        WHERE p.date = %s
    ''', (today,))
    present = cursor.fetchall()

    # Fetch late employees
    cursor.execute(''' 
        SELECT w.name, w.surname, l.date, l.sign_in_time, l.late_duration
        FROM late l
        JOIN workers w ON w.id = l.worker_id
        WHERE l.date = %s
    ''', (today,))
    late = cursor.fetchall()

    # Fetch absent employees
    cursor.execute(''' 
        SELECT w.name, w.surname
        FROM workers w
        WHERE w.id NOT IN (
            SELECT a.worker_id FROM attendance a WHERE a.date = %s
        )
    ''', (today,))
    absent = cursor.fetchall()

    conn.close()

    return render_template(
        'hr_dashboard.html',
        present=present,
        late=late,
        absent=absent,
        date=today
    )
#make an absent history table 



if __name__ == '__main__':
    init_db()
    add_sample_workers()
    app.run(debug=True, port=5001)
