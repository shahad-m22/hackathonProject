from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import mysql.connector
from datetime import datetime, date
import math

app = Flask(__name__)
app.secret_key = 'nibbah_factory_secret_2024'  # Needed for session management

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root2003',
    'database': 'nibbah_factory'
}

def get_db_connection():
    """Create and return database connection"""
    return mysql.connector.connect(**db_config)

def calculate_risk_level(next_maintenance, reference_date=None):
    """Calculate risk level based on days until next maintenance"""
    if reference_date is None:
        reference_date = date.today()
   
    if isinstance(next_maintenance, str):
        next_maintenance = datetime.strptime(next_maintenance, '%Y-%m-%d').date()
   
    days_until_due = (next_maintenance - reference_date).days
   
    if days_until_due <= 0:
        return 'High', '🔴', 'high-risk'
    elif days_until_due <= 7:
        return 'Medium', '🟡', 'medium-risk'
    else:
        return 'Low', '🟢', 'low-risk'

def calculate_financial_impact(machine, reference_date=None):
    """Calculate potential financial impact"""
    if reference_date is None:
        reference_date = date.today()
       
    if isinstance(machine['next_maintenance'], str):
        next_maintenance = datetime.strptime(machine['next_maintenance'], '%Y-%m-%d').date()
    else:
        next_maintenance = machine['next_maintenance']
   
    days_overdue = (reference_date - next_maintenance).days
    if days_overdue > 0:
        # Estimate 8 hours of downtime for overdue machines
        estimated_downtime_cost = machine['hourly_downtime_cost'] * 8
        total_potential_loss = estimated_downtime_cost + machine['total_maintenance_cost']
        return total_potential_loss, estimated_downtime_cost, days_overdue
    return 0, 0, 0

# ==================== ROUTES ====================

@app.route('/')
def home():
    """Redirect to login page"""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        user_id = request.form['userID']
        email = request.form['email']
        password = request.form['password']
       
        # Simple authentication - check if user exists in database
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE user_id = %s AND email = %s", (user_id, email))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
           
            if user:
                # For demo purposes, we're not checking password hashes
                session['user_id'] = user_id
                session['email'] = email
                session['user_name'] = f"User {user_id}"
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error="Invalid credentials. Please try again.")
               
        except Exception as e:
            return render_template('login.html', error="Database error. Please try again.")
   
    # GET request - show login form
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard page"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
       
        # Get all machines
        cursor.execute("SELECT * FROM machines")
        machines = cursor.fetchall()
       
        # For demo purposes - hardcoded to judging day (Nov 11)
        demo_date = date(2024, 11, 11)
        # demo_date = date.today()  # Uncomment for real-time during development
       
        # Calculate risk levels and statistics
        high_risk_count = 0
        medium_risk_count = 0
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
       
        # Calculate overview statistics
        cursor.execute("SELECT COUNT(*) as total_machines FROM machines")
        total_machines = cursor.fetchone()['total_machines']
       
        cursor.close()
        conn.close()
       
        return render_template('dashboard.html',
                             machines=machines,
                             total_machines=total_machines,
                             high_risk_count=high_risk_count,
                             medium_risk_count=medium_risk_count,
                             total_risk_exposure=total_risk_exposure,
                             demo_date=demo_date)
                             
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/machine/<int:machine_id>')
def machine_details(machine_id):
    """Machine details page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
       
        cursor.execute("SELECT * FROM machines WHERE machine_id = %s", (machine_id,))
        machine = cursor.fetchone()
       
        # For demo purposes
        demo_date = date(2024, 11, 11)
        # demo_date = date.today()  # Uncomment for real-time during development
       
        if machine:
            risk_level, risk_icon, risk_class = calculate_risk_level(machine['next_maintenance'], demo_date)
            machine['risk_level'] = risk_level
            machine['risk_icon'] = risk_icon
            machine['risk_class'] = risk_class
           
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
    """Add new machine page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    if request.method == 'POST':
        # Handle form submission for new machine
        try:
            machine_name = request.form['machineName']
            machine_type = request.form.get('machineType', '')
            location = request.form.get('location', '')
            status = request.form.get('status', 'Active')
            description = request.form.get('description', '')
           
            # For demo, we'll just show a success message
            # In a real app, you'd insert into database here
            return render_template('add_machine.html',
                                 success=f"Machine '{machine_name}' added successfully!")
                                 
        except Exception as e:
            return render_template('add_machine.html', error=str(e))
   
    # GET request - show the form
    return render_template('add_machine.html')

@app.route('/api/machines')
def api_machines():
    """JSON API endpoint for machines data"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
   
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
       
        cursor.execute("SELECT * FROM machines")
        machines = cursor.fetchall()
       
        # Calculate risk levels for API response
        demo_date = date(2024, 11, 11)
        for machine in machines:
            risk_level, risk_icon, risk_class = calculate_risk_level(machine['next_maintenance'], demo_date)
            machine['risk_level'] = risk_level
            machine['risk_icon'] = risk_icon
       
        cursor.close()
        conn.close()
       
        return jsonify(machines)
       
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send-test-alert')
def send_test_alert():
    """Test email alerts (optional feature)"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    # This would integrate with your email_notifier.py
    return jsonify({
        'success': True,
        'message': 'Test alert functionality would be implemented here'
    })

@app.route('/logout')
def logout():
    """Logout user and clear session"""
    session.clear()
    return redirect(url_for('login'))

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('error.html', error="Internal server error"), 500

# ==================== MAIN ====================

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
