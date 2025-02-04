from flask import Blueprint, render_template
from pymongo import MongoClient
from datetime import datetime

admin_blueprint = Blueprint('admin', __name__, template_folder='templates')

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["attendance_db"]
users_collection = db["users"]
attendance_collection = db["attendance_records"]

@admin_blueprint.route('/dashboard')
def dashboard():
    users = list(users_collection.find())
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    attendance_today = list(attendance_collection.find({
        "timestamp": {"$gte": today}
    }))
    
    attendance_data = []
    for user in users:
        record = next((r for r in attendance_today if r["employee_id"] == user["employee_id"]), None)
        if record:
            status = record["status"]
            arrival_time = record["timestamp"].strftime("%H:%M:%S")
        else:
            status = "Absent"
            arrival_time = "N/A"

        attendance_data.append({
            "employee_id": user["employee_id"],
            "name": user["name"],
            "status": status,
            "arrival_time": arrival_time
        })
    
    return render_template('dashboard.html', attendance_data=attendance_data)
