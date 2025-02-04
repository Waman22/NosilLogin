from flask import Flask,render_template, request, redirect, url_for 
import sqlite3
import random
import time

app= Flask(__name__)



@app.route("/")
def Home():
    return render_template("home.html")

@app.route("/Services")
def services():
    return render_template("services.html")

@app.route("/About")
def About():
    return render_template("about.html")



@app.route("/sign", methods=['POST', 'GET'])
def sign():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        username = request.form['username']
        password = request.form['password']
        Date = request.form['Dob']
        email = request.form['email']
        Address = request.form['Address']
        region_count = int(request.form['region_count'])
        
        conn = sqlite3.connect('Sensors.db')
        c = conn.cursor()

        c.execute('SELECT * FROM Sign WHERE username = ?', (username,))
        user = c.fetchone()

        if user is None:
            c.execute("INSERT INTO Sign(name, surname, username, password, Dob, email, Address, region_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",(name, surname, username, password, Date, email, Address, region_count))
            conn.commit()

           # Insert user regions into user_regions table
            for region_id in range(1, region_count + 1):
                c.execute("INSERT INTO user_regions(username, region_id) VALUES (?, ?)", (username, region_id))
                conn.commit()

            return redirect(url_for('login2'))
        else:
            error = "Username already in use try another one."
            return render_template("sign.html", error = error)
    else:
        return render_template("sign.html")


@app.route("/login2", methods = ['POST', 'GET'])
def login2():
    if request.method== 'POST':
        username = request.form['username']  #request input from the html page
        password = request.form['password']
        conn = sqlite3.connect('Sensors.db')
        c = conn.cursor()
        c.execute("SELECT * FROM  Sign  WHERE username = ? AND password = ?", (username,password)) #check if a row exists where the username and password match the provided values
        user = c.fetchone()

        if user is not None:
            return redirect(url_for('index3', username=username))
        else:
            incorrect = "Username or Password is incorrect!!, TRY Again or SIGN UP."
            return render_template("login2.html",erro = incorrect)
    else:
        return render_template("login2.html")

@app.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        mail = request.form['email']
        
        conn = sqlite3.connect('Sensors.db')
        c = conn.cursor()
        c.execute("SELECT * FROM Sign WHERE email = ?", (mail,))
        details = c.fetchone()

        if details is not None:
            return render_template("forgot_password.html", details=details)
        else:
           incorrect = "Email not found. Please try again or sign up."
        return render_template("forgot_password.html", err=incorrect)
    else:
        return render_template("forgot_password.html")


# Connect to the SQLite database
conn = sqlite3.connect('Sensors.db')
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS user_regions (username TEXT, region_id INTEGER, FOREIGN KEY(username) REFERENCES Sign(username), FOREIGN KEY(region_id) REFERENCES regions(region_id), PRIMARY KEY (username, region_id))")
conn.commit()

c.close()
# Connect to the SQLite database
conn = sqlite3.connect('Sensors.db')
c = conn.cursor()

# Create the regions table if it doesn't exist
c.execute("CREATE TABLE IF NOT EXISTS regions (region_id INTEGER PRIMARY KEY, region_name TEXT)")

# Connect to the database
conn = sqlite3.connect('Sensors.db')
c = conn.cursor()

# Create the Time table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS Time (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Zone TEXT,
                timeframe TEXT,
                DateT TEXT,
                liters INTEGER,
                duration INTEGER,
                valid INTEGER
            )''')

# Commit the changes and close the connection
conn.commit()


# Close the cursor and connection
c.close()
conn.close()
# Generate random sensor data and insert it into the database

def generate_sensors_data(region_count):
    timestamp = "%.1f" % int(time.time())
    soil_moisture = "%.1f" % random.uniform(0.0, 1.0)
    temperature = "%.1f" % random.uniform(20.0, 30.0)
    humidity = "%.1f" % random.uniform(40.0, 60.0)
    water = "%.1f" % random.uniform(0.0, 1000.0)
    c = conn.cursor()

    # Limit the region count to a maximum of 30
    region_count = min(region_count, 30)

    for region_id in range(1, region_count + 1):
        c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "soil_moisture", soil_moisture, region_id))
        c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "temperature", temperature, region_id))
        c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "humidity", humidity, region_id))
        c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "water_levels", water, region_id))
    
    conn.commit()

# Start a separate thread to generate and insert the sensor data every minute
def background_thread(region_count):
    while True:
        generate_sensors_data(region_count)
        time.sleep(60)

# Start the background thread on app startup
from threading import Thread
bg_thread = Thread(target=background_thread)  #It assigns the background_thread function as the target for the thread and then starts the thread by calling its start() method.
bg_thread.start()


@app.route('/index3/<username>', methods=['POST', 'GET'])
def index3(username):
    conn = sqlite3.connect('Sensors.db')
    c = conn.cursor()

    # Retrieve the user's region count from the user_regions table
    c.execute("SELECT region_count FROM Sign WHERE username = ?", (username,))
    region_count = c.fetchone()[0]

    # Query the sensor data from the database, filtered by region if specified
    region = request.args.get('region', default=None, type=int)

    # If a region count is specified, generate new sensor data and update the database
    if region_count is not None:
        timestamp = str(int(time.time()))
        for region_id in range(1, region_count + 1):
            soil_moisture = "%.1f" % random.uniform(0.0, 100)
            temperature = "%.1f" % random.uniform(20.0, 30.0)
            humidity = "%.1f" % random.uniform(40.0, 60.0)
            water = "%.1f" % random.uniform(0.0, 1000.0)
            c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "soil_moisture", soil_moisture, region_id))
            c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "temperature", temperature, region_id))
            c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "humidity", humidity, region_id))
            c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "water_levels", water, region_id))
        conn.commit()

    # Query the sensor data from the database, filtered by region if specified
    if region is not None:
        c.execute("SELECT * FROM sensors_data WHERE region = ? ORDER BY timestamp DESC LIMIT 4", (region,))
    else:
        c.execute("SELECT * FROM sensors_data ORDER BY timestamp DESC LIMIT 4")
    sensor_data = c.fetchall()

    # Query the regions from the database
    c.execute("SELECT * FROM regions")
    regions = c.fetchall()

    # Close the cursor and connection
    c.close()
    conn.close()

    # Render the HTML template with the sensor data, regions, and region param
    return render_template('index3.html', username=username, sensor_data=sensor_data, regions=regions, region=region, region_count=region_count)

@app.route("/monitor/<username>", methods=['POST', 'GET'])
def monitor(username):
    conn = sqlite3.connect('Sensors.db')
    c = conn.cursor()

    # Retrieve the user's region count from the user_regions table
    c.execute("SELECT region_count FROM Sign WHERE username = ?", (username,))
    region_count = c.fetchone()[0]

    # Query the sensor data from the database, filtered by region if specified
    region = request.args.get('region', default=None, type=int)

    # If a region count is specified, generate new sensor data and update the database
    if region_count is not None:
        timestamp = str(int(time.time()))
        for region_id in range(1, region_count + 1):
            soil_moisture = "%.1f" % random.uniform(0.0, 100)
            temperature = "%.1f" % random.uniform(20.0, 30.0)
            humidity = "%.1f" % random.uniform(40.0, 60.0)
            water = "%.1f" % random.uniform(0.0, 1000.0)
            c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "soil_moisture", soil_moisture, region_id))
            c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "temperature", temperature, region_id))
            c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "humidity", humidity, region_id))
            c.execute("INSERT INTO sensors_data VALUES (?, ?, ?, ?)", (timestamp, "water_levels", water, region_id))
        conn.commit()

    # Query the sensor data from the database, filtered by region if specified
    if region is not None:
        c.execute("SELECT * FROM sensors_data WHERE region = ? ORDER BY timestamp DESC LIMIT 4", (region,))
    else:
        c.execute("SELECT * FROM sensors_data ORDER BY timestamp DESC LIMIT 4")
    sensor_data = c.fetchall()

    # Query the regions from the database
    c.execute("SELECT * FROM regions")
    regions = c.fetchall()

    # Close the cursor and connection
    c.close()
    conn.close()

     # Analyze patterns in sensor data
    pattern_feedback = analyze_sensor_data(sensor_data, region)

    # Render the HTML template with the sensor data, regions, and region param
    return render_template('monitor.html', username=username, sensor_data=sensor_data, regions=regions, region=region, region_count=region_count, pattern_feedback=pattern_feedback)

def analyze_sensor_data(sensor_data, region):
    # Extract the data values for each sensor type in the selected region
    soil_moisture_values = [float(data[2]) for data in sensor_data if data[1] == 'soil_moisture' and data[3] == region]
    temperature_values = [float(data[2]) for data in sensor_data if data[1] == 'temperature' and data[3] == region]
    humidity_values = [float(data[2]) for data in sensor_data if data[1] == 'humidity' and data[3] == region]
    water_levels_values = [float(data[2]) for data in sensor_data if data[1] == 'water_levels' and data[3] == region]

    # Perform analysis on the sensor data to identify patterns
    # Example: Check if values are within a desired range or if there are significant fluctuations

    # Generate pattern feedback based on the analysis
    pattern_feedback = {}

    if len(soil_moisture_values) > 0:
        average_soil_moisture = sum(soil_moisture_values) / len(soil_moisture_values)
        if average_soil_moisture < 30:
            pattern_feedback['soil_moisture'] = 'Low moisture levels in region {}'.format(region)
            pattern_feedback['watering'] = 'Water the plants in region {}'.format(region)
        elif average_soil_moisture > 75:
            pattern_feedback['soil_moisture'] = 'High moisture levels in region {}'.format(region)
        else:
            pattern_feedback['soil_moisture'] = 'Good moisture levels in region {}'.format(region)

    if len(temperature_values) > 0:
        average_temperature = sum(temperature_values) / len(temperature_values)
        if average_temperature < 10:
            pattern_feedback['temperature'] = 'Low temperature levels in region {}'.format(region)
            pattern_feedback['watering'] = 'Water the plants in region {}'.format(region)
        elif average_temperature > 35:
            pattern_feedback['temerature'] = 'High temperature levels in region {}'.format(region)
        else:
            pattern_feedback['temperature'] = 'Good temperature levels in region {}'.format(region)

    if len(humidity_values) > 0:
        average_humidity = sum(humidity_values) / len(humidity_values)
        if average_humidity < 40:
            pattern_feedback['humidity'] = 'Low Humidity levels in region {}'.format(region)
            pattern_feedback['watering'] = 'Water the plants in region {}'.format(region)
        elif average_humidity > 75:
            pattern_feedback['humidity'] = 'High Humidity levels in region {}'.format(region)
            print('Dont water the plants now')
        else:
            pattern_feedback['humidity'] = 'Good Humidity levels in region {}'.format(region)

            #for water levels 
    if len( water_levels_values) > 0:
        average_water = sum( water_levels_values) / len( water_levels_values)
        if average_water< 300:
            pattern_feedback['water_levels'] = 'Low water-levels in region {}'.format(region)
            pattern_feedback['watering'] = 'Please refill water tank  in region {}'.format(region)
        elif average_water > 750:
            pattern_feedback['water_levels'] = 'High Water-levels in region {}'.format(region)
            print('Dont water the plants now')
        else:
            pattern_feedback['water_levels'] = 'Good Water-levels in region {}'.format(region)
    return pattern_feedback



@app.route("/Time/<username>", methods=['POST', 'GET'])
def Time(username):
    conn = sqlite3.connect('Sensors.db')
    c = conn.cursor()

    if request.method == 'POST':
        Zone = request.form['region']
        Time = request.form['timeframe']
        date = request.form['DateT']
        level = request.form['liters']
        Duration = request.form['duration']
        Days = request.form['valid']

         # Convert the level to a float
        level = float(level)

        # Check if the level exceeds the limit
        if level > 900:
            level = 900

        # Retrieve the user's region count from the Sign table
        c.execute("SELECT region_count FROM Sign WHERE username = ?", (username,))
        region_count = c.fetchone()[0]

        c.execute('SELECT * FROM Time WHERE Zone = ? AND timeframe = ? AND DateT = ?', (Zone, Time, date))
        user = c.fetchone()

        if user is None:
            c.execute("INSERT INTO Time(Zone, timeframe, DateT, liters, duration, valid) VALUES (?, ?, ?, ?, ?, ?)",
                      (Zone, Time, date, level, Duration, Days))
            conn.commit()

            # Retrieve the inserted row for display
            c.execute("SELECT * FROM Time WHERE Zone = ? AND timeframe = ? AND DateT = ?", (Zone, Time, date))
            row = c.fetchone()

            # Close the cursor and connection
            c.close()
            conn.close()

            return redirect(url_for('TimeData', username=username, schedule_id=row[0]))

    # Retrieve the user's region count from the Sign table
    c.execute("SELECT region_count FROM Sign WHERE username = ?", (username,))
    region_count = c.fetchone()[0]

    # Close the cursor and connection
    c.close()
    conn.close()

    return render_template("Time.html", username=username, region_count=region_count)


    
@app.route('/TimeData/<username>/<int:schedule_id>')
def TimeData(username, schedule_id):
    conn = sqlite3.connect('Sensors.db')
    c = conn.cursor()

    # Retrieve the schedule details based on the schedule_id
    c.execute("SELECT * FROM Time WHERE id = ?", (schedule_id,))
    row = c.fetchone()

    # Close the cursor and connection
    c.close()
    conn.close()
    return render_template('TimeData.html', row=row, username=username)



@app.route("/modify/<username>/<int:schedule_id>", methods=['GET', 'POST'])
def modify(username, schedule_id):
    conn = sqlite3.connect('Sensors.db')
    c = conn.cursor()

    # Retrieve the user's region count from the Sign table
    c.execute("SELECT region_count FROM Sign WHERE username = ?", (username,))
    region_count = c.fetchone()[0]

    if request.method == 'POST':
        # Retrieve the modified schedule details from the form
        zone = request.form['region']
        time_frame = request.form['timeframe']
        date = request.form['DateT']
        liters = request.form['liters']
        duration = request.form['duration']
        valid_days = request.form['valid']

        # Update the schedule in the database based on the schedule_id
        c.execute("UPDATE Time SET Zone = ?, timeframe = ?, DateT = ?, liters = ?, duration = ?, valid = ? WHERE id = ?",
                  (zone, time_frame, date, liters, duration, valid_days, schedule_id))
        conn.commit()

        # Close the cursor and connection
        c.close()
        conn.close()

        return redirect(url_for('TimeData', username=username, schedule_id=schedule_id))

    # Retrieve the schedule details based on the schedule_id
    c.execute("SELECT * FROM Time WHERE id = ?", (schedule_id,))
    row = c.fetchone()

    # Close the cursor and connection
    c.close()
    conn.close()

    return render_template("modify.html", row=row, username=username, region_count=region_count)

@app.route("/delete/<username>/<int:schedule_id>")
def delete(username, schedule_id):
    conn = sqlite3.connect('Sensors.db')
    c = conn.cursor()

    # Retrieve the user's region count from the Sign table
    c.execute("SELECT region_count FROM Sign WHERE username = ?", (username,))
    region_count = c.fetchone()[0]

    # Retrieve the schedule details based on the schedule_id
    c.execute("SELECT * FROM Time WHERE id = ?", (schedule_id,))
    row = c.fetchone()

    # Delete the schedule from the database based on the schedule_id
    c.execute("DELETE FROM Time WHERE id = ?", (schedule_id,))
    conn.commit()

    # Close the cursor and connection
    c.close()
    conn.close()

    delete = "Schedule deleted successfully"
    return redirect(url_for('index3', username=username, delete=delete, row=row, region_count=region_count))


if __name__ == "__main__":
    app.run(debug=True)