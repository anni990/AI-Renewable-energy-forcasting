import os
import sys
import subprocess
import pymysql

def check_database_connection():
    """Check if we have Azure SQL Server connection details"""
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = ['AZURE_SQL_SERVER', 'AZURE_SQL_USERNAME', 'AZURE_SQL_PASSWORD', 'AZURE_SQL_DATABASE']
        missing_vars = []
        
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            print("Please make sure your .env file contains all Azure SQL Server credentials.")
            return False
        
        print("✅ Azure SQL Server environment variables found.")
        return True
    except Exception as e:
        print(f"❌ Error checking database configuration: {e}")
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
    
    print("\nChecking Azure SQL Server configuration...")
    if not check_database_connection():
        print("\n⚠️ Azure SQL Server configuration incomplete.")
        print("Please make sure your .env file contains:")
        print("  AZURE_SQL_SERVER=your-server.database.windows.net")
        print("  AZURE_SQL_USERNAME=your-username")
        print("  AZURE_SQL_PASSWORD=your-password")
        print("  AZURE_SQL_DATABASE=your-database-name")
        return
    
    if not install_dependencies():
        return
    
    print("\n"+"="*60)
    print("✅ Setup completed successfully!")
    print("\nYou can now run the application with:")
    print("  python app.py")
    print("\nThen visit: http://127.0.0.1:5000 in your browser")
    print("\nRegister your first user, which will automatically be an admin.")
    print("="*60)

if __name__ == "__main__":
    main() 