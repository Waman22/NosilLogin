from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

#employee registration code

# Helper function to get a database connection
def get_db_connection():
    conn = sqlite3.connect('employee.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize the database
def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # Create employees table
    c.execute('''CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id TEXT UNIQUE,  
                name TEXT NOT NULL,
                surname TEXT NOT NULL,
                dob TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                cellphone TEXT NOT NULL,  -- New field
                id_number TEXT NOT NULL,  -- New field
                course TEXT NOT NULL,
                specialization TEXT NOT NULL,
                address TEXT NOT NULL,
                cohort TEXT NOT NULL,
                UNIQUE(name, surname) 
            )''')


    
    conn.commit()
    conn.close()

# Create a table for a specific cohort
def create_cohort_table(cohort_name):
    conn = get_db_connection()
    c = conn.cursor()

    # Format the cohort table name correctly (replace spaces and make lowercase)
    cohort_name_slug = cohort_name.replace(" ", "_").lower()

    # Create cohort-specific table
    create_table_sql = f'''
    CREATE TABLE IF NOT EXISTS {cohort_name_slug} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id TEXT UNIQUE,  
                name TEXT NOT NULL,
                surname TEXT NOT NULL,
                dob TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                cellphone TEXT NOT NULL,  -- New field
                id_number TEXT NOT NULL,  -- New field
                course TEXT NOT NULL,
                specialization TEXT NOT NULL,
                address TEXT NOT NULL,
                cohort TEXT NOT NULL,
                UNIQUE(name, surname)
    );
    '''
    
    c.execute(create_table_sql)
    conn.commit()
    conn.close()
    print(f"Table for {cohort_name} created or already exists.")


@app.route("/")
def Home():
    return render_template("layout.html")

@app.route("/Register", methods=['POST', 'GET'])
def Register():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        dob = request.form['dob']
        email = request.form['email']
        cellphone = request.form['cellphone']
        id_number = request.form['id_number']
        course = request.form['course']
        specialization = request.form['specialization']
        address = request.form['address']
        cohort = request.form['cohort']

        # Validate cellphone number (must be 10 digits)
        if not cellphone.isdigit() or len(cellphone) != 10:
            error = "Cellphone number must be exactly 10 digits."
            return render_template("employee.html", error=error)

        # Validate ID number (must be 13 digits)
        if not id_number.isdigit() or len(id_number) != 13:
            error = "ID number must be exactly 13 digits."
            return render_template("employee.html", error=error)

        # Validate the date of birth
        try:
            birth_date = datetime.strptime(dob, '%Y-%m-%d')
        except ValueError:
            error = "Invalid date format. Use YYYY-MM-DD."
            return render_template("employee.html", error=error)

        today = datetime.now()
        age = (today - birth_date).days // 365  # Calculate age in years
        if age < 18 or age > 35:
            error = "Date of birth must be for individuals between 18 and 35 years old."
            return render_template("employee.html", error=error)

        conn = get_db_connection()
        c = conn.cursor()

        try:
            # Insert into employees table
            c.execute('''INSERT INTO employees (name, surname, dob, email, cellphone, id_number, course, specialization, address, cohort)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (name, surname, dob, email, cellphone, id_number, course, specialization, address, cohort))
            conn.commit()

            # Retrieve the worker ID and update it as before
            worker_id = c.lastrowid
            formatted_worker_id = f"{worker_id:03}"
            c.execute('UPDATE employees SET worker_id = ? WHERE id = ?', (formatted_worker_id, worker_id))
            conn.commit()

            # Insert into the correct cohort-specific course table
            cohort_table_name = f"{course.replace(' ', '_').lower()}_{cohort.replace(' ', '_').lower()}"
            c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (cohort_table_name,))
            if not c.fetchone():
                # Create cohort-specific table if it doesn't exist
                c.execute(f'''
                    CREATE TABLE {cohort_table_name} (
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
                    );
                ''')
                conn.commit()

            c.execute(f'''INSERT INTO {cohort_table_name} 
                         (worker_id, name, surname, dob, email, cellphone, id_number, course, specialization, address, cohort) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)''',
                      (formatted_worker_id, name, surname, dob, email, cellphone, id_number, course, specialization, address, cohort))
            conn.commit()

            # Insert into specialization-specific table
            specialization_table = specialization.replace(" ", "_").lower()
            c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (specialization_table,))
            if not c.fetchone():
                # Create specialization-specific table if it doesn't exist
                c.execute(f'''
                    CREATE TABLE {specialization_table} (
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
                    );
                ''')
                conn.commit()

            c.execute(f'''INSERT INTO {specialization_table} 
                         (worker_id, name, surname, dob, email, cellphone, id_number, course, specialization, address, cohort) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)''',
                      (formatted_worker_id, name, surname, dob, email, cellphone, id_number, course, specialization, address, cohort))
            conn.commit()

        except sqlite3.IntegrityError as e:
            conn.close()
            if "email" in str(e):
                error = "The email address is already registered. Please use a different email."
            elif "name, surname" in str(e):
                error = "A person with the same name and surname is already registered."
            else:
                error = "An error occurred during registration. Please try again."
            return render_template("employee.html", error=error)

        conn.close()
        return redirect(url_for('Register_OUT', worker_id=formatted_worker_id))

    return render_template("employee.html")


# Route for confirming registration
@app.route("/Register_OUT")
def Register_OUT():
    worker_id = request.args.get('worker_id', None)
    if worker_id:
        worker_id = f"{int(worker_id):03}"  # Format worker_id as a zero-padded 3-digit string
    return render_template("Register_OUT.html", worker_id=worker_id)

# Call init_db to create tables on app start
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
