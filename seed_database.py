import mysql.connector
from datetime import datetime, timedelta

def seed_database():
    try:
        print("🚀 Seeding database for November 11th judging...")

        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'root2003',
            'database': 'nibbah_factory'
        }

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Clear existing data
        cursor.execute("DELETE FROM machines")

        # Set judging date
        judging_date = datetime(2024, 11, 11).date()

        # Sample data optimized for November 11th demo
        machines_data = [
            # 🔴 HIGH RISK - Overdue on judging day
            ('Compressor A-1', 9, 18500.00, 296000.00, 
             judging_date - timedelta(days=70), judging_date - timedelta(days=3), 15),

            ('Hydraulic Press D-7', 10, 22000.00, 350000.00,
             judging_date - timedelta(days=65), judging_date - timedelta(days=1), 12),

            # 🟡 MEDIUM RISK - Due right after judging
            ('CNC Mill B-12', 8, 16500.00, 245000.00,
             judging_date - timedelta(days=40), judging_date + timedelta(days=1), 10),

            ('Paint Booth F-4', 6, 12000.00, 180000.00,
             judging_date - timedelta(days=35), judging_date + timedelta(days=3), 8),
            
            ('Heat Exchanger A-5', 7, 14000.00, 280000.00,
             judging_date - timedelta(days=30), judging_date + timedelta(days=5), 20),

            # 🟢 LOW RISK - Safe (future dates)
            ('Cooling System C-3', 6, 8500.00, 120000.00,
             judging_date - timedelta(days=25), judging_date + timedelta(days=15), 10),

            ('Welding Robot E-9', 5, 16000.00, 220000.00,
             judging_date - timedelta(days=20), judging_date + timedelta(days=25), 8),

            ('Gas Turbine A-4', 9, 40000.00, 1000000.00,
             judging_date - timedelta(days=15), judging_date + timedelta(days=40), 25),
        ]

        # Insert data
        insert_query = """
            INSERT INTO machines 
            (machine_name, criticality, hourly_downtime_cost, total_maintenance_cost,
             last_maintenance, next_maintenance, life_time_years)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(insert_query, machines_data)
        conn.commit()

        print(f"✅ Successfully seeded {len(machines_data)} machines")
        print("🎯 Perfect for Nov 11 demo: 2🔴 RED, 3🟡 YELLOW, 3🟢 GREEN")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    seed_database()