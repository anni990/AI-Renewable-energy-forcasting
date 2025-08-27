import os
from dotenv import load_dotenv

def init_db():
    """Check Azure SQL Server configuration"""
    load_dotenv()
    
    try:
        required_vars = ['AZURE_SQL_SERVER', 'AZURE_SQL_USERNAME', 'AZURE_SQL_PASSWORD', 'AZURE_SQL_DATABASE']
        missing_vars = []
        
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            print("Please make sure your .env file contains all Azure SQL Server credentials.")
            return False
        
        print("✅ Azure SQL Server configuration found.")
        print("Database tables will be created automatically by SQLAlchemy when you run the application.")
        return True
    except Exception as e:
        print(f"❌ Error checking database configuration: {e}")
        return False

if __name__ == "__main__":
    print("Checking Azure SQL Server configuration...")
    if init_db():
        print("\nConfiguration check complete! You can now run the application with:")
        print("python app.py")
    else:
        print("\nFailed to find Azure SQL Server configuration. Please check your .env file.") 