from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import mysql.connector
from datetime import datetime, date, timedelta
import math
import threading
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)
app.secret_key = 'nabeh_factory_secret_2024'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root2003',
    'database': 'nabeh_factory'
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

# ==================== EMAIL SIMULATION FUNCTIONS ====================

def send_email(to, subject, body, html_body=None):
    """Simulate email sending - print to console and log to database"""
    print(f"""
    📧 EMAIL SIMULATION
    To: {to}
    Subject: {subject}
    Body: {body[:100]}...
    {"="*50}
    """)
   
    # Log to database for demo
    log_notification(to, subject, "simulated")
    return True

def log_notification(recipient, subject, status="simulated"):
    """Log notification to database for demo purposes"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Extract machine name from subject for demo
        machine_name = "System"
        alert_type = "general"
        
        # Better machine name extraction
        if "Electric Motor" in subject:
            machine_name = "Electric Motor A-3"
        elif "Heat Exchanger" in subject:
            machine_name = "Heat Exchanger A-5"
        elif "Conveyor" in subject:
            machine_name = "Conveyor System A-6"
        elif "Cooling Fan" in subject:
            machine_name = "Cooling Fan A-8"
        elif "Filter/Separator" in subject:
            machine_name = "Filter/Separator A-12"
        elif "Vacuum Pump" in subject:
            machine_name = "Vacuum Pump A-14"
        elif "Compressor" in subject:
            machine_name = "Compressor A-1"
        elif "Daily Report" in subject:
            alert_type = "daily_report"
        elif "OVERDUE" in subject:
            alert_type = "high_risk"
        elif "Due Soon" in subject:
            alert_type = "medium_risk"
        
        cursor.execute("""
            INSERT INTO notification_logs (recipient, subject, machine_name, alert_type, status, sent_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (recipient, subject, machine_name, alert_type, status))
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Logged notification for {machine_name}")
    except Exception as e:
        print(f"Note: Could not log notification: {e}")

def get_notification_recipients(alert_level):
    """Get actual email recipients from users table based on alert level"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
       
        if alert_level == 'High':
            # For high risk: get all users (technicians, maintenance, operations)
            cursor.execute("SELECT email FROM users")
        elif alert_level == 'Medium':
            # For medium risk: get technicians and maintenance (user_ids 11011, 11022, 11044)
            cursor.execute("SELECT email FROM users WHERE user_id IN (11011, 11022, 11044)")
        elif alert_level == 'daily_report':
            # For daily reports: get management and operations (user_ids 11033, 11055)
            cursor.execute("SELECT email FROM users WHERE user_id IN (11033, 11055)")
        else:
            # Default: get all users
            cursor.execute("SELECT email FROM users")
       
        recipients = [row['email'] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
       
        print(f"📧 Found {len(recipients)} recipients for {alert_level} alert")
        return recipients
       
    except Exception as e:
        print(f"❌ Error getting recipients: {str(e)}")
        # Fallback to demo emails
        return ['technician1@nabehfactory.com', 'maintenance@nabehfactory.com']

def track_machine_state_changes():
    """Track when machines change risk states and trigger simulated notifications"""
    print("🔄 Checking for machine state changes...")
   
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
       
        cursor.execute("SELECT * FROM machines")
        machines = cursor.fetchall()
       
        demo_date = date.today()
        state_changes = []
       
        for machine in machines:
            current_risk, _, _ = calculate_risk_level(machine['next_maintenance'], demo_date)
           
            cursor.execute(
                "SELECT risk_state FROM machine_states WHERE machine_id = %s ORDER BY created_at DESC LIMIT 1",
                (machine['machine_id'],)
            )
            last_state_record = cursor.fetchone()
            last_state = last_state_record['risk_state'] if last_state_record else 'Low'
           
            if current_risk != last_state:
                print(f"🔄 State change: {machine['machine_name']} - {last_state} → {current_risk}")
               
                cursor.execute("""
                    INSERT INTO machine_states (machine_id, risk_state, last_notification_sent, notification_count)
                    VALUES (%s, %s, NULL, 0)
                """, (machine['machine_id'], current_risk))
               
                state_changes.append({
                    'machine': machine,
                    'previous_state': last_state,
                    'new_state': current_risk,
                    'days_until_due': (machine['next_maintenance'] - demo_date).days
                })
       
        # Send simulated notifications for state changes
        for change in state_changes:
            send_state_change_notification(change)
       
        conn.commit()
        cursor.close()
        conn.close()
       
        print(f"✅ Processed {len(state_changes)} state changes")
        return state_changes
       
    except Exception as e:
        print(f"❌ Error tracking state changes: {str(e)}")
        return []

def send_state_change_notification(state_change):
    """Send simulated notification when machine risk state changes"""
    machine = state_change['machine']
    new_state = state_change['new_state']
    days_until_due = state_change['days_until_due']
   
    if new_state == 'High':
        recipients = get_notification_recipients('High')
        subject = f"🚨 CRITICAL: {machine['machine_name']} MAINTENANCE OVERDUE!"
        body = f"""
            URGENT: {machine['machine_name']} is {abs(days_until_due)} days OVERDUE!

            Machine Details:
            - Criticality: {machine['criticality']}/10
            - Next Maintenance: {machine['next_maintenance']}
            - Last Maintenance: {machine['last_maintenance']}
            - Hourly Downtime Cost: SAR {machine['hourly_downtime_cost']:,.0f}

            IMMEDIATE ACTION REQUIRED: Schedule maintenance now to avoid production stoppage.

            Nabeh Factory Monitoring System
            """
    elif new_state == 'Medium':
        recipients = get_notification_recipients('Medium')
        subject = f"⚠️ REMINDER: {machine['machine_name']} Maintenance Due Soon"
        body = f"""
        REMINDER: {machine['machine_name']} maintenance due in {days_until_due} days.

        Machine Details:
        - Criticality: {machine['criticality']}/10
        - Next Maintenance: {machine['next_maintenance']}
        - Last Maintenance: {machine['last_maintenance']}
        - Hourly Downtime Cost: SAR {machine['hourly_downtime_cost']:,.0f}

        Please schedule maintenance within the next 3 days.

        Nabeh Factory Monitoring System
        """
    else:
        return
   
    for recipient in recipients:
        send_email(recipient, subject, body)

def send_daily_report():
    """Send simulated daily maintenance report"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
       
        demo_date = date.today()
       
        # Get machine statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total_machines,
                SUM(CASE WHEN DATEDIFF(next_maintenance, %s) < 0 THEN 1 ELSE 0 END) as overdue_count,
                SUM(CASE WHEN DATEDIFF(next_maintenance, %s) BETWEEN 0 AND 7 THEN 1 ELSE 0 END) as due_soon_count
            FROM machines
        """, (demo_date, demo_date))
        stats = cursor.fetchone()
       
        # Get high priority machines
        cursor.execute("""
            SELECT machine_name, criticality, next_maintenance,
                   DATEDIFF(next_maintenance, %s) as days_until_due
            FROM machines
            WHERE DATEDIFF(next_maintenance, %s) <= 7
            ORDER BY days_until_due ASC
            LIMIT 10
        """, (demo_date, demo_date))
        priority_machines = cursor.fetchall()
       
        subject = f"📊 Daily Maintenance Report - {date.today().strftime('%Y-%m-%d')}"
        body = f"""
        DAILY MAINTENANCE REPORT - {date.today().strftime('%Y-%m-%d')}

        OVERVIEW:
        • Total Machines: {stats['total_machines']}
        • Overdue Machines: {stats['overdue_count']}
        • Due Soon (Next 7 days): {stats['due_soon_count']}

        PRIORITY MAINTENANCE:
        """
       
        for machine in priority_machines:
            status = "OVERDUE" if machine['days_until_due'] < 0 else "DUE SOON"
            body += f"• {machine['machine_name']} (Criticality: {machine['criticality']}/10) - {machine['next_maintenance']} ({machine['days_until_due']} days) - {status}\n"
       
        body += "\nGenerated by Nabeh Factory Monitoring System"
       
        # Get recipients from users table for daily reports
        recipients = get_notification_recipients('daily_report')
        for recipient in recipients:
            send_email(recipient, subject, body)
       
        cursor.close()
        conn.close()
        print("Daily report simulation completed")
       
    except Exception as e:
        print(f"Error sending daily report: {str(e)}")

# ==================== SCHEDULER ====================

def start_scheduler():
    """Start background scheduler for automated monitoring"""
    scheduler = BackgroundScheduler()
   
    # Check for state changes every 5 minutes
    scheduler.add_job(
        func=track_machine_state_changes,
        trigger='interval',
        minutes=5,
        id='state_monitoring'
    )
   
    # Send daily reports at 8:00 AM
    scheduler.add_job(
        func=send_daily_report,
        trigger='cron',
        hour=8,
        minute=0,
        id='daily_reports'
    )
   
    scheduler.start()
    print("Automated monitoring scheduler started")
   
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

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

        demo_date = date.today()

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

        demo_date = date.today()
       
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

# ==================== NOTIFICATION ROUTES ====================

@app.route('/check-states')
def check_states_manual():
    """Manually trigger state change detection"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    changes = track_machine_state_changes()
   
    return jsonify({
        'status': 'success',
        'message': f'Detected {len(changes)} state changes',
        'changes': changes
    })

@app.route('/test-email')
def test_email():
    """Test email simulation using actual users"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    # Test with actual technician emails
    recipients = get_notification_recipients('Medium')
    for recipient in recipients:
        send_email(
            recipient,
            '🧪 TEST: Nabeh Factory Notification System',
            'This is a test of the automated notification system. All systems are functioning correctly.'
        )
   
    return jsonify({
        'status': 'success',
        'message': f'Test email simulation sent to {len(recipients)} actual users - check console'
    })

@app.route('/daily-report')
def trigger_daily_report():
    """Manually trigger daily report"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    send_daily_report()
   
    return jsonify({
        'status': 'success',
        'message': 'Daily report simulation completed - check console for details'
    })

@app.route('/notification-logs')
def notification_logs():
    """Show notification logs for demo"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM notification_logs ORDER BY sent_at DESC LIMIT 20")
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
       
        return jsonify({
            'status': 'success',
            'logs': logs
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/simulate-medium-risk')
def simulate_medium_risk():
    """Simulate a machine entering medium risk state"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    recipients = get_notification_recipients('Medium')
    for recipient in recipients:
        send_email(
            recipient,
            '⚠️ REMINDER: Electric Motor A-3 Maintenance Due Soon',
            'Electric Motor A-3 is due for maintenance in 5 days. Please schedule maintenance soon.'
        )
   
    return jsonify({
        'status': 'success',
        'message': f'Medium risk alert simulation sent to {len(recipients)} technicians/maintenance staff'
    })

@app.route('/simulate-high-risk')
def simulate_high_risk():
    """Simulate a machine entering high risk state"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    recipients = get_notification_recipients('High')
    for recipient in recipients:
        send_email(
            recipient,
            '🚨 CRITICAL: Filter/Separator A-12 MAINTENANCE OVERDUE!',
            'Filter/Separator A-12 is 3 days overdue for maintenance! Immediate action required.'
        )
   
    return jsonify({
        'status': 'success',
        'message': f'High risk alert simulation sent to {len(recipients)} all team members'
    })

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

# ==================== INITIALIZATION ====================

def initialize_monitoring():
    """Initialize the monitoring system on startup"""
    print("Initializing Nabeh Factory Monitoring System...")
    print("Email notifications: SIMULATION MODE")
    print("Automated monitoring: ENABLED")
    print("State change detection: ENABLED")
   
    # Check current states on startup
    track_machine_state_changes()

if __name__ == '__main__':
    initialize_monitoring()
    start_scheduler()
    app.run(debug=True, port=5000)
