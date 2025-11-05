import mysql.connector
from datetime import datetime

def seed_database():
    try:
        print(" Seeding database with EXACT dates from your CSV for November 11, 2025...")
       
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'root2003',
            'database': 'nabeh_factory'
        }
       
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
       
        # Clear existing data
        cursor.execute("DELETE FROM notification_logs")
        cursor.execute("DELETE FROM machine_states")
        cursor.execute("DELETE FROM machines")
       
        # Judging date: November 11, 2025
        judging_date = datetime(2025, 11, 11).date()
       
        # YOUR EXACT CSV DATES
        machines_data = [
            ('Compressor A-1', 8, 18000.00, 296000.00, '2025-08-01', '2025-11-25', 15),
            ('Crude/Product Pump A-2', 8, 23000.00, 460000.00, '2025-07-10', '2025-11-28', 12),
            ('Electric Motor A-3', 6, 15000.00, 200000.00, '2025-07-01', '2025-11-15', 15),
            ('Gas Turbine A-4', 9, 40000.00, 1000000.00, '2025-04-01', '2025-12-25', 25),
            ('Heat Exchanger A-5', 7, 14000.00, 280000.00, '2025-04-15', '2025-11-18', 20),
            ('Conveyor System A-6', 5, 8000.00, 89000.00, '2025-05-20', '2025-11-09', 10),
            ('PLC/SCADA System A-7', 10, 22000.00, 128000.00, '2025-08-01', '2025-12-10', 12),
            ('Cooling Fan A-8', 5, 9000.00, 80000.00, '2025-05-01', '2025-11-10', 8),
            ('Water Treatment Unit A-9', 4, 11000.00, 139000.00, '2025-06-15', '2026-01-10', 18),
            ('Power Generator A-10', 9, 25000.00, 430000.00, '2025-07-01', '2025-11-20', 20),
            ('Pipeline A-11', 6, 20000.00, 340000.00, '2025-06-01', '2026-03-15', 40),
            ('Filter/Separator A-12', 4, 6000.00, 49000.00, '2025-05-15', '2025-11-07', 10),
            ('High-Pressure System A-13', 7, 16000.00, 220000.00, '2025-07-20', '2025-11-30', 18),
            ('Vacuum Pump A-14', 3, 10000.00, 110000.00, '2025-06-01', '2025-11-05', 12),
            ('Pump A-15', 5, 12000.00, 102000.00, '2025-07-15', '2026-01-15', 12),
        ]
       
        # Insert data
        insert_query = """
            INSERT INTO machines
            (machine_name, criticality, hourly_downtime_cost, total_maintenance_cost,
             last_maintenance, next_maintenance, life_time_years)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
       
        cursor.executemany(insert_query, machines_data)
       
        # Seed initial machine states
        cursor.execute("""
            INSERT INTO machine_states (machine_id, risk_state, last_notification_sent, notification_count)
            SELECT machine_id, 'Low', NULL, 0 FROM machines
        """)
       
        # Add some sample notification logs for demo
        sample_notifications = [
            ('technicians@nabehfactory.com', '⚠️ REMINDER: Compressor A-1 Maintenance Due Soon', 'Compressor A-1', 'medium_risk', 'sent'),
            ('maintenance@nabehfactory.com', '🚨 CRITICAL: Filter/Separator A-12 MAINTENANCE OVERDUE!', 'Filter/Separator A-12', 'high_risk', 'sent'),
            ('operations@nabehfactory.com', '📊 Daily Maintenance Report - 2025-11-10', 'System', 'daily_report', 'sent')
        ]

        cursor.executemany("""
            INSERT INTO notification_logs (recipient, subject, machine_name, alert_type, status, sent_at)
            VALUES (%s, %s, %s, %s, %s, NOW() - INTERVAL FLOOR(RAND() * 24) HOUR)
        """, sample_notifications)
       
        conn.commit()
       
        print(f"✅ Successfully seeded {len(machines_data)} machines with EXACT CSV dates")
       
        # Show exact risk distribution for Nov 11, 2025
        cursor.execute("""
            SELECT
                machine_name,
                next_maintenance,
                DATEDIFF(next_maintenance, '2025-11-11') as days_from_judging
            FROM machines
            ORDER BY days_from_judging
        """)
       
        print(f"\n📊 EXACT RISK DISTRIBUTION for November 11, 2025:")
        print("=" * 70)
       
        high_count = 0
        medium_count = 0
        low_count = 0
       
        for machine in cursor.fetchall():
            days_from_judging = machine[2]
            if days_from_judging < 0:
                status = "🔴 OVERDUE"
                high_count += 1
            elif days_from_judging <= 7:
                status = "🟡 DUE SOON"
                medium_count += 1
            else:
                status = "🟢 SAFE"
                low_count += 1
               
            print(f"• {machine[0]:<25} | {status} | Due: {machine[1]} (in {days_from_judging} days)")
       
        print("=" * 70)
        print(f"🎯 Perfect demo: {high_count}🔴 RED, {medium_count}🟡 YELLOW, {low_count}🟢 GREEN")
       
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    seed_database()