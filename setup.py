import os
import sys
import subprocess
import pymysql

def check_mysql_connection():
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
        print(f"❌ Error connecting to MySQL: {e}")
        return False

def install_dependencies():
    print("\nInstalling required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def main():
    print("="*60)
    print("  Renewable Energy Forecasting System - Setup")
    print("="*60)
    
    print("\nChecking MySQL connection...")
    if not check_mysql_connection():
        print("\n⚠️ Could not connect to MySQL server.")
        print("Please make sure XAMPP is installed and MySQL service is running.")
        print("1. Open XAMPP Control Panel")
        print("2. Start MySQL service")
        print("3. Run this setup script again")
        return
    
    if not install_dependencies():
        return
    
    print("\n"+"="*60)
    print("✅ Setup completed successfully!")
    print("\nYou can now run the application with:")
    print("  python app.py")
    print("\nThis will create the database tables and start the server.")
    print("\nThen visit: http://127.0.0.1:5000 in your browser")
    print("\nRegister your first user, which will automatically be an admin.")
    print("="*60)

if __name__ == "__main__":
    main() 