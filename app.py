from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import mysql.connector
from datetime import datetime, date, timedelta
import math

app = Flask(__name__)
app.secret_key = 'nabeh_factory_secret_2024'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root2003',
    'database': 'nibbah_factory'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def calculate_risk_level(next_maintenance, reference_date=None):
    if reference_date is None:
        reference_date = date.today()

    if isinstance(next_maintenance, str):
        next_maintenance = datetime.strptime(next_maintenance, '%Y-%m-%d').date()

    days_until_due = (next_maintenance - reference_date).days

    if days_until_due < 0:
        return 'High', '🔴', 'high-risk'
    elif days_until_due <= 7:
        return 'Medium', '🟡', 'medium-risk'
    else:
        return 'Low', '🟢', 'low-risk'

def calculate_maintenance_status(next_maintenance, last_maintenance, reference_date=None):
    if reference_date is None:
        reference_date = date.today()

    if isinstance(next_maintenance, str):
        next_maintenance = datetime.strptime(next_maintenance, '%Y-%m-%d').date()
    if isinstance(last_maintenance, str):
        last_maintenance = datetime.strptime(last_maintenance, '%Y-%m-%d').date()

    days_until_due = (next_maintenance - reference_date).days
   
    if days_until_due < 0:
        return 'Overdue', 'This machine is overdue for maintenance!', 'immediate'
    elif days_until_due <= 3:
        return 'Critical', 'Urgent maintenance required!', 'urgent'
    elif days_until_due <= 7:
        return 'Warning', 'Maintenance due soon', 'warning'
    elif days_until_due <= 30:
        return 'Optimal', 'This machine is properly maintained', 'optimal'
    else:
        return 'Optimal', 'This machine is properly maintained', 'optimal'

def calculate_financial_impact(machine, reference_date=None):
    if reference_date is None:
        reference_date = date.today()

    if isinstance(machine['next_maintenance'], str):
        next_maintenance = datetime.strptime(machine['next_maintenance'], '%Y-%m-%d').date()
    else:
        next_maintenance = machine['next_maintenance']

    days_overdue = (reference_date - next_maintenance).days
    if days_overdue > 0:
        estimated_downtime_cost = machine['hourly_downtime_cost'] * 8 * days_overdue
        total_potential_loss = estimated_downtime_cost + machine['total_maintenance_cost']
        return total_potential_loss, estimated_downtime_cost, days_overdue
    return 0, 0, 0

# ==================== ROUTES ====================

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['userID']
        password = request.form['password']
       
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
       
            if user:
                session['user_id'] = user_id
                session['user_name'] = f"User {user_id}"
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error="Invalid User ID. Please try again.")
               
        except Exception as e:
            return render_template('login.html', error="Database error. Please try again.")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
       
        cursor.execute("SELECT * FROM machines")
        machines = cursor.fetchall()

        demo_date = date(2025, 11, 11)

        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        total_risk_exposure = 0

        for machine in machines:
            risk_level, risk_icon, risk_class = calculate_risk_level(machine['next_maintenance'], demo_date)
            machine['risk_level'] = risk_level
            machine['risk_icon'] = risk_icon
            machine['risk_class'] = risk_class

            if risk_level == 'High':
                high_risk_count += 1
                total_potential_loss, _, _ = calculate_financial_impact(machine, demo_date)
                total_risk_exposure += total_potential_loss
            elif risk_level == 'Medium':
                medium_risk_count += 1
            else:
                low_risk_count += 1

        cursor.execute("SELECT COUNT(*) as total_machines FROM machines")
        total_machines = cursor.fetchone()['total_machines']

        cursor.close()
        conn.close()
       
        return render_template('dashboard.html',
                             machines=machines,
                             total_machines=total_machines,
                             high_risk_count=high_risk_count,
                             medium_risk_count=medium_risk_count,
                             low_risk_count=low_risk_count,
                             total_risk_exposure=total_risk_exposure,
                             demo_date=demo_date)

    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/machine/<int:machine_id>')
def machine_details(machine_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM machines WHERE machine_id = %s", (machine_id,))
        machine = cursor.fetchone()

        demo_date = date(2025, 11, 11)
       
        if machine:
            risk_level, risk_icon, risk_class = calculate_risk_level(machine['next_maintenance'], demo_date)
            maintenance_status, status_message, status_class = calculate_maintenance_status(
                machine['next_maintenance'], machine['last_maintenance'], demo_date
            )
           
            machine['risk_level'] = risk_level
            machine['risk_icon'] = risk_icon
            machine['risk_class'] = risk_class
            machine['maintenance_status'] = maintenance_status
            machine['status_message'] = status_message
            machine['status_class'] = status_class

            days_until_service = (machine['next_maintenance'] - demo_date).days
            machine['days_until_service'] = days_until_service

            total_potential_loss, downtime_cost, days_overdue = calculate_financial_impact(machine, demo_date)
        else:
            total_potential_loss, downtime_cost, days_overdue = 0, 0, 0

        cursor.close()
        conn.close()

        return render_template('machine_details.html',
                             machine=machine,
                             total_potential_loss=total_potential_loss,
                             downtime_cost=downtime_cost,
                             days_overdue=days_overdue,
                             demo_date=demo_date)

    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/add-machine', methods=['GET', 'POST'])
def add_machine():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            machine_name = request.form['machine_name']
            criticality = int(request.form['criticality'])
            life_time_years = int(request.form['life_time_years'])
            hourly_downtime_cost = float(request.form['hourly_downtime_cost'])
            total_maintenance_cost = float(request.form['total_maintenance_cost'])
            last_maintenance = request.form['last_maintenance']
            next_maintenance = request.form['next_maintenance']

            conn = get_db_connection()
            cursor = conn.cursor()
           
            insert_query = """
                INSERT INTO machines
                (machine_name, criticality, hourly_downtime_cost, total_maintenance_cost,
                 last_maintenance, next_maintenance, life_time_years)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(insert_query, (
                machine_name, criticality, hourly_downtime_cost, total_maintenance_cost,
                last_maintenance, next_maintenance, life_time_years
            ))

            conn.commit()
            cursor.close()
            conn.close()

            return render_template('add_machine.html',
                                 success=f"Machine '{machine_name}' added successfully to database!")

        except Exception as e:
            return render_template('add_machine.html', error=f"Error adding machine: {str(e)}")

    return render_template('add_machine.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
