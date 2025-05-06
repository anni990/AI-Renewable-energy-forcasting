import os
from werkzeug.security import generate_password_hash
from database.db_connection import get_db_connection, init_db

def create_admin_user(username='admin', email='admin@example.com', password='admin123'):
    """Create an admin user if no users exist in the database"""
    print("Initializing database...")
    # Initialize database first
    init_db()
    
    conn = get_db_connection()
    if not conn:
        print("Error: Could not connect to database.")
        return False
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Check if users table exists and if any users are present
        cursor.execute("SELECT COUNT(*) as count FROM users")
        result = cursor.fetchone()
        
        if result and result['count'] > 0:
            print(f"Admin user already exists. Total users: {result['count']}")
            return False
        
        # Create admin user
        cursor.execute(
            'INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)',
            (username, email, generate_password_hash(password), 'admin')
        )
        conn.commit()
        print(f"Created admin user: {username} with password: {password}")
        print("Please change this password after logging in!")
        return True
    
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    create_admin_user()
    print("\nYou can now run the application with: python app.py") 