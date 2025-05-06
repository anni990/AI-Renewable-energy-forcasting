import pymysql
import os

def init_db():
    """Create the database if it doesn't exist"""
    try:
        # Connect to MySQL server (not to a specific database)
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password=''
        )
        # Create database if it doesn't exist
        with conn.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS renewable_energy")
            print("✅ Database 'renewable_energy' created or already exists.")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

if __name__ == "__main__":
    print("Initializing database...")
    if init_db():
        print("\nDatabase setup complete! You can now run the application with:")
        print("python app.py")
    else:
        print("\nFailed to initialize database. Make sure MySQL server is running via XAMPP.") 