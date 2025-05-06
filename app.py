import os
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-for-dev')
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}/{os.environ.get('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

# Add now() function to Jinja2 environment as a global
@app.template_filter('now')
def _jinja2_filter_now():
    return datetime.now()

# Register now() as a global function in Jinja2
app.jinja_env.globals['now'] = datetime.now

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'renewable_energy')
}

def get_db_connection():
    """Create a database connection to the MySQL database"""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
    
    return conn

def init_db():
    """Initialize the database with tables if they don't exist"""
    # First, create the database if it doesn't exist
    try:
        temp_conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = temp_conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.close()
        temp_conn.close()
        print(f"Database '{DB_CONFIG['database']}' created or already exists.")
    except Error as e:
        print(f"Error creating database: {e}")
        return

    # Now connect to the database and create tables
    conn = get_db_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Read SQL script file
            sql_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'create_tables.sql')
            if os.path.exists(sql_path):
                with open(sql_path, 'r') as f:
                    sql_script = f.read()
                
                # Execute SQL script statement by statement
                for statement in sql_script.split(';'):
                    if statement.strip():
                        try:
                            cursor.execute(statement)
                            conn.commit()
                        except Error as e:
                            print(f"Error executing statement: {statement}")
                            print(f"Error message: {e}")
                
                print("Database tables initialized successfully.")
            else:
                print(f"SQL script file not found at {sql_path}")
        except Error as e:
            print(f"Error initializing database: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        print("Error: Could not establish connection to database.")

# Import models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.id', ondelete='SET NULL'), nullable=True)
    plant_type = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def is_authenticated(self):
        return True
        
    @property
    def is_active(self):
        return True
        
    @property
    def is_anonymous(self):
        return False
        
    def get_id(self):
        return str(self.id)

class Plant(db.Model):
    __tablename__ = 'plants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    threshold_value = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = db.relationship('User', backref='plant', lazy=True)
    hourly_solar_predictions = db.relationship('HourlySolarPrediction', backref='plant', lazy=True, cascade="all, delete-orphan")
    hourly_wind_predictions = db.relationship('HourlyWindPrediction', backref='plant', lazy=True, cascade="all, delete-orphan")
    daily_solar_predictions = db.relationship('DailySolarPrediction', backref='plant', lazy=True, cascade="all, delete-orphan")
    daily_wind_predictions = db.relationship('DailyWindPrediction', backref='plant', lazy=True, cascade="all, delete-orphan")

class HourlySolarPrediction(db.Model):
    __tablename__ = 'hourly_solar_predictions'
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.id', ondelete='CASCADE'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    weather_data = db.Column(db.JSON, nullable=False)
    predicted_generation = db.Column(db.Float, nullable=True)
    actual_generation = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HourlyWindPrediction(db.Model):
    __tablename__ = 'hourly_wind_predictions'
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.id', ondelete='CASCADE'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    weather_data = db.Column(db.JSON, nullable=False)
    predicted_generation = db.Column(db.Float, nullable=True)
    actual_generation = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DailySolarPrediction(db.Model):
    __tablename__ = 'daily_solar_predictions'
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_predicted_generation = db.Column(db.Float, nullable=True)
    total_actual_generation = db.Column(db.Float, nullable=True)
    recommendation_status = db.Column(db.Boolean, default=False)
    recommendation_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DailyWindPrediction(db.Model):
    __tablename__ = 'daily_wind_predictions'
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_predicted_generation = db.Column(db.Float, nullable=True)
    total_actual_generation = db.Column(db.Float, nullable=True)
    recommendation_status = db.Column(db.Boolean, default=False)
    recommendation_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        if current_user.role != 'admin':
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Route for user registration"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        plant_type = request.form['plant_type']
        plant_id = request.form.get('plant_id', None)  # Optional for admin users
        
        # Validate input
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        # Determine if this is an admin user
        is_admin = (plant_type == 'both')
        role = 'admin' if is_admin else 'user'
        
        # Regular users must specify a plant_id
        if not is_admin and not plant_id:
            flash('Plant ID is required for non-admin users', 'danger')
            return redirect(url_for('register'))
        
        # Convert plant_id to int if it exists
        if plant_id:
            try:
                plant_id = int(plant_id)
            except ValueError:
                flash('Invalid plant ID', 'danger')
                return redirect(url_for('register'))
        
        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
            return redirect(url_for('register'))
        
        # Insert the new user
        try:
            # Create password hash
            password_hash = generate_password_hash(password)
            
            # Create new user object
            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=role,
                plant_id=plant_id if not is_admin else None,
                plant_type=plant_type
            )
            
            # Add to database
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error during registration: {str(e)}', 'danger')
            return redirect(url_for('register'))
    
    # GET request - show registration form
    # For regular users, we need to fetch available plants
    plants = Plant.query.all()
    
    return render_template('register.html', plants=plants)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            
            # After successful login, trigger data fetching and prediction
            try:
                print(f"=== Login successful for user: {username} (ID: {user.id}) ===")
                # Only process for users with plants
                if user.plant_id:
                    print(f"User has plant_id: {user.plant_id}")
                    plant = Plant.query.get(user.plant_id)
                    if plant:
                        print(f"Found plant: {plant.name} (Type: {plant.type}, Location: {plant.location})")
                        # Import ML pipeline modules
                        from ml_pipeline.fetch_weather import fetch_weather_data
                        from ml_pipeline.predict_hourly import predict_hourly_generation
                        from ml_pipeline.aggregate_daily import aggregate_daily_generation, filter_daylight_hours, save_predictions_to_db
                        
                        # Fetch weather data with plant location
                        print(f"Fetching weather data for location: {plant.location}")
                        weather_data = fetch_weather_data(location=plant.location)
                        print(f"Fetched {len(weather_data)} weather records")
                        
                        # Process based on plant type
                        if plant.type == 'solar':
                            print("Processing solar plant predictions...")
                            # Predict hourly generation
                            hourly_predictions = predict_hourly_generation(weather_data, "solar", plant.id)
                            print(f"Generated {len(hourly_predictions)} hourly predictions")
                            
                            # Filter to daylight hours for solar predictions
                            filtered_predictions = filter_daylight_hours(hourly_predictions)
                            print(f"Filtered to {len(filtered_predictions)} daylight hour predictions")
                            
                            # Aggregate to daily predictions
                            daily_predictions = aggregate_daily_generation(filtered_predictions, plant.threshold_value)
                            print(f"Aggregated to {len(daily_predictions)} daily predictions")
                            
                            # Save to database - pass db instance but no longer needed
                            print("Saving predictions to database...")
                            save_predictions_to_db(hourly_predictions, daily_predictions, plant.id, None, "solar")
                            print("Database update completed")
                        
                        elif plant.type == 'wind':
                            print("Wind plant processing not yet implemented")
                            # Wind prediction logic will be implemented later
                            pass
                    else:
                        print(f"No plant found with ID: {user.plant_id}")
                else:
                    print("User has no plant assigned")
            except Exception as e:
                print(f"Error during prediction after login: {str(e)}")
                import traceback
                print(traceback.format_exc())
                # Non-critical error, continue to dashboard
                
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Route for user dashboard based on their plant type"""
    # Get user's plant type
    plant_type = current_user.plant_type
    
    if plant_type == 'solar':
        # Get today's date
        today = datetime.now().date()
        
        # Fetch solar plant data for today
        solar_data = HourlySolarPrediction.query.filter_by(plant_id=current_user.plant_id)\
            .filter(db.func.date(HourlySolarPrediction.timestamp) == today)\
            .order_by(HourlySolarPrediction.timestamp.desc()).all()
        
        # If no data for today, get the most recent 24 hours
        if not solar_data:
            solar_data = HourlySolarPrediction.query.filter_by(plant_id=current_user.plant_id)\
                .order_by(HourlySolarPrediction.timestamp.desc()).limit(24).all()
        
        plant = Plant.query.get(current_user.plant_id)
        
        # Get daily predictions for charts - get the latest 6 dates
        daily_solar_data = DailySolarPrediction.query.filter_by(plant_id=current_user.plant_id)\
            .order_by(DailySolarPrediction.date.desc()).limit(6).all()
        
        # Generate recommendations
        recommendations = []
        for data in daily_solar_data:
            if data.recommendation_status:
                recommendations.append({
                    'date': data.date,
                    'message': data.recommendation_message or f"Solar generation below threshold ({data.total_predicted_generation:.2f} kWh). Consider backup power."
                })
        
        return render_template('solar_dashboard.html', 
                              solar_data=solar_data, 
                              plant=plant,
                              recommendations=recommendations,
                              daily_solar_data=daily_solar_data,
                              today=today)
    
    elif plant_type == 'wind':
        # Get today's date
        today = datetime.now().date()
        
        # Fetch wind plant data for today
        wind_data = HourlyWindPrediction.query.filter_by(plant_id=current_user.plant_id)\
            .filter(db.func.date(HourlyWindPrediction.timestamp) == today)\
            .order_by(HourlyWindPrediction.timestamp.desc()).all()
            
        # If no data for today, get the most recent 24 hours
        if not wind_data:
            wind_data = HourlyWindPrediction.query.filter_by(plant_id=current_user.plant_id)\
                .order_by(HourlyWindPrediction.timestamp.desc()).limit(24).all()
        
        plant = Plant.query.get(current_user.plant_id)
        
        # Get daily predictions for charts - get the latest 6 dates
        daily_wind_data = DailyWindPrediction.query.filter_by(plant_id=current_user.plant_id)\
            .order_by(DailyWindPrediction.date.desc()).limit(6).all()
        
        # Generate recommendations
        recommendations = []
        for data in daily_wind_data:
            if data.recommendation_status:
                recommendations.append({
                    'date': data.date,
                    'message': data.recommendation_message or f"Wind generation below threshold ({data.total_predicted_generation:.2f} kWh). Consider backup power."
                })
        
        return render_template('wind_dashboard.html', 
                              wind_data=wind_data, 
                              plant=plant,
                              recommendations=recommendations,
                              daily_wind_data=daily_wind_data,
                              today=today)
    
    elif plant_type == 'both':
        # This is an admin user, show both solar and wind data
        plants = Plant.query.all()
        
        # Get distinct lists of plants by type
        solar_plants = Plant.query.filter_by(type='solar').all()
        wind_plants = Plant.query.filter_by(type='wind').all()
        
        # Get recent solar and wind predictions
        solar_predictions = db.session.query(
            Plant.name.label('plant_name'),
            DailySolarPrediction.date,
            DailySolarPrediction.total_predicted_generation,
            DailySolarPrediction.total_actual_generation,
            DailySolarPrediction.recommendation_status
        ).join(DailySolarPrediction).order_by(DailySolarPrediction.date.desc()).limit(10).all()
        
        wind_predictions = db.session.query(
            Plant.name.label('plant_name'),
            DailyWindPrediction.date,
            DailyWindPrediction.total_predicted_generation,
            DailyWindPrediction.total_actual_generation,
            DailyWindPrediction.recommendation_status
        ).join(DailyWindPrediction).order_by(DailyWindPrediction.date.desc()).limit(10).all()
        
        # Generate recommendations/alerts
        recommendations = []
        
        # Get solar plants below threshold
        solar_alerts = db.session.query(
            Plant.name.label('plant_name'),
            DailySolarPrediction.date,
            DailySolarPrediction.total_predicted_generation,
            Plant.threshold_value,
            DailySolarPrediction.recommendation_message.label('message')
        ).join(DailySolarPrediction)\
         .filter(DailySolarPrediction.recommendation_status == True)\
         .order_by(DailySolarPrediction.date.desc())\
         .limit(5).all()
        
        for alert in solar_alerts:
            recommendations.append({
                'plant_name': alert.plant_name,
                'date': alert.date.strftime('%Y-%m-%d'),
                'message': alert.message or f"Solar generation below threshold ({alert.total_predicted_generation:.2f} < {alert.threshold_value:.2f} kWh)."
            })
        
        # Get wind plants below threshold
        wind_alerts = db.session.query(
            Plant.name.label('plant_name'),
            DailyWindPrediction.date,
            DailyWindPrediction.total_predicted_generation,
            Plant.threshold_value,
            DailyWindPrediction.recommendation_message.label('message')
        ).join(DailyWindPrediction)\
         .filter(DailyWindPrediction.recommendation_status == True)\
         .order_by(DailyWindPrediction.date.desc())\
         .limit(5).all()
        
        for alert in wind_alerts:
            recommendations.append({
                'plant_name': alert.plant_name,
                'date': alert.date.strftime('%Y-%m-%d'),
                'message': alert.message or f"Wind generation below threshold ({alert.total_predicted_generation:.2f} < {alert.threshold_value:.2f} kWh)."
            })
        
        return render_template('admin_dashboard.html', 
                              plants=plants,
                              solar_plants=solar_plants,
                              wind_plants=wind_plants,
                              solar_predictions=solar_predictions,
                              wind_predictions=wind_predictions,
                              recommendations=recommendations)
    
    else:
        flash('Invalid plant type. Please contact administrator.', 'danger')
        return redirect(url_for('home'))

@app.route('/register_plant', methods=['GET', 'POST'])
# @login_required
# @admin_required
def register_plant():
    if request.method == 'POST':
        plant_name = request.form['plant_name']
        location = request.form['location']
        plant_type = request.form['plant_type']
        threshold_value = float(request.form['threshold_value'])
        
        # Create new plant
        new_plant = Plant(
            name=plant_name,
            location=location,
            type=plant_type,
            threshold_value=threshold_value
        )
        
        db.session.add(new_plant)
        db.session.commit()
        
        flash(f'Plant "{plant_name}" registered successfully!', 'success')
        
        # Trigger initial forecast generation
        if plant_type == 'solar':
            return redirect(url_for('update_solar_forecasts'))
        elif plant_type == 'wind':
            # When wind forecast is implemented, redirect to that
            flash('Wind forecast generation not yet implemented', 'warning')
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('dashboard'))
    
    return render_template('register_plant.html')

@app.route('/update_solar_forecasts')
@login_required
@admin_required
def update_solar_forecasts():
    """Route to update solar forecasts for all solar plants"""
    try:
        print("=== Starting update_solar_forecasts route ===")
        # Import ML pipeline modules - ensure app context is passed along
        from ml_pipeline.fetch_weather import fetch_weather_data
        from ml_pipeline.predict_hourly import predict_hourly_generation
        from ml_pipeline.aggregate_daily import aggregate_daily_generation, filter_daylight_hours, save_predictions_to_db
        
        # Get all solar plants
        solar_plants = Plant.query.filter_by(type='solar').all()
        print(f"Found {len(solar_plants)} solar plants")
        
        for plant in solar_plants:
            print(f"Processing plant: {plant.name} (ID: {plant.id})")
            # Fetch weather data with plant location
            weather_data = fetch_weather_data(location=plant.location)
            print(f"Fetched {len(weather_data)} weather records for plant {plant.id}")
            
            # Predict hourly generation
            hourly_predictions = predict_hourly_generation(weather_data, "solar", plant.id)
            print(f"Generated {len(hourly_predictions)} hourly predictions for plant {plant.id}")
            
            # Filter to daylight hours for solar predictions
            filtered_predictions = filter_daylight_hours(hourly_predictions)
            print(f"Filtered to {len(filtered_predictions)} daylight hour predictions for plant {plant.id}")
            
            # Aggregate to daily predictions
            daily_predictions = aggregate_daily_generation(filtered_predictions, plant.threshold_value)
            print(f"Aggregated to {len(daily_predictions)} daily predictions for plant {plant.id}")
            
            # Save to database with direct MySQL connection
            print(f"Saving predictions to database for plant {plant.id}...")
            save_predictions_to_db(hourly_predictions, daily_predictions, plant.id, None, "solar")
            print(f"Database update completed for plant {plant.id}")
        
        flash('Solar forecasts updated successfully', 'success')
        print("=== Completed update_solar_forecasts route ===")
    except Exception as e:
        print(f"Error updating solar forecasts: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash(f'Error updating solar forecasts: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/update_forecasts')
@login_required
@admin_required
def update_forecasts():
    """Legacy route that redirects to update_solar_forecasts until wind is implemented"""
    return redirect(url_for('update_solar_forecasts'))

@app.route('/user_profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    """Route for user profile editing"""
    if request.method == 'POST':
        # Extract form data
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        user = User.query.get(current_user.id)
        
        if email:
            # Update email
            user.email = email
        
        if current_password and new_password and confirm_password:
            # Check current password
            if check_password_hash(user.password_hash, current_password):
                # Validate new password
                if new_password == confirm_password:
                    # Update password
                    user.password_hash = generate_password_hash(new_password)
                else:
                    flash('New passwords do not match', 'danger')
                    return redirect(url_for('user_profile'))
            else:
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('user_profile'))
        
        try:
            # Save changes
            db.session.commit()
            flash('Profile updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
        
        return redirect(url_for('user_profile'))
    
    return render_template('user_profile.html', user=current_user)

# Add routes for chart data
@app.route('/api/solar_chart_data')
@login_required
def solar_chart_data():
    """API endpoint for solar generation chart data"""
    if current_user.plant_type != 'solar' and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get the plant ID
    plant_id = request.args.get('plant_id', current_user.plant_id)
    
    # Handle 'all' option for admin users
    if plant_id == 'all' and current_user.role == 'admin':
        # Get total generation per day across all solar plants
        daily_data = db.session.query(
            DailySolarPrediction.date,
            db.func.sum(DailySolarPrediction.total_predicted_generation).label('predicted'),
            db.func.sum(DailySolarPrediction.total_actual_generation).label('actual')
        ).group_by(DailySolarPrediction.date)\
         .order_by(DailySolarPrediction.date.desc())\
         .limit(7).all()
        
        # Format data for chart
        dates = [d.date.strftime('%Y-%m-%d') for d in daily_data]
        predictions = [float(d.predicted) for d in daily_data]
        actuals = [float(d.actual) if d.actual else 0 for d in daily_data]
        
        # Calculate average threshold across all solar plants
        avg_threshold = db.session.query(db.func.avg(Plant.threshold_value))\
            .filter(Plant.type == 'solar').scalar() or 0
        
        # Prepare data for chart
        chart_data = {
            'dates': dates,
            'predictions': predictions,
            'actuals': actuals,
            'threshold': float(avg_threshold)
        }
        
        return jsonify(chart_data)
    else:
        # Query daily solar predictions for a specific plant
        try:
            plant_id = int(plant_id)
        except ValueError:
            return jsonify({'error': 'Invalid plant ID'}), 400
            
        daily_data = DailySolarPrediction.query.filter_by(plant_id=plant_id)\
            .order_by(DailySolarPrediction.date.desc())\
            .limit(7).all()
        
        # Format data for chart
        dates = [d.date.strftime('%Y-%m-%d') for d in daily_data]
        predictions = [float(d.total_predicted_generation) for d in daily_data]
        actuals = [float(d.total_actual_generation) if d.total_actual_generation else 0 for d in daily_data]
        
        # Get threshold value
        plant = Plant.query.get(plant_id)
        threshold = plant.threshold_value if plant else 0
        
        # Prepare data for chart
        chart_data = {
            'dates': dates,
            'predictions': predictions,
            'actuals': actuals,
            'threshold': threshold
        }
        
        return jsonify(chart_data)

@app.route('/api/wind_chart_data')
@login_required
def wind_chart_data():
    """API endpoint for wind generation chart data"""
    if current_user.plant_type != 'wind' and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get the plant ID
    plant_id = request.args.get('plant_id', current_user.plant_id)
    
    # Handle 'all' option for admin users
    if plant_id == 'all' and current_user.role == 'admin':
        # Get total generation per day across all wind plants
        daily_data = db.session.query(
            DailyWindPrediction.date,
            db.func.sum(DailyWindPrediction.total_predicted_generation).label('predicted'),
            db.func.sum(DailyWindPrediction.total_actual_generation).label('actual')
        ).group_by(DailyWindPrediction.date)\
         .order_by(DailyWindPrediction.date)\
         .limit(7).all()
        
        # Format data for chart
        dates = [d.date.strftime('%Y-%m-%d') for d in daily_data]
        predictions = [float(d.predicted) for d in daily_data]
        actuals = [float(d.actual) if d.actual else 0 for d in daily_data]
        
        # Calculate average threshold across all wind plants
        avg_threshold = db.session.query(db.func.avg(Plant.threshold_value))\
            .filter(Plant.type == 'wind').scalar() or 0
        
        # Prepare data for chart
        chart_data = {
            'dates': dates,
            'predictions': predictions,
            'actuals': actuals,
            'threshold': float(avg_threshold)
        }
        
        return jsonify(chart_data)
    else:
        # Query daily wind predictions for a specific plant
        try:
            plant_id = int(plant_id)
        except ValueError:
            return jsonify({'error': 'Invalid plant ID'}), 400
            
        daily_data = DailyWindPrediction.query.filter_by(plant_id=plant_id)\
            .order_by(DailyWindPrediction.date)\
            .limit(7).all()
        
        # Format data for chart
        dates = [d.date.strftime('%Y-%m-%d') for d in daily_data]
        predictions = [float(d.total_predicted_generation) for d in daily_data]
        actuals = [float(d.total_actual_generation) if d.total_actual_generation else 0 for d in daily_data]
        
        # Get threshold value
        plant = Plant.query.get(plant_id)
        threshold = plant.threshold_value if plant else 0
        
        # Prepare data for chart
        chart_data = {
            'dates': dates,
            'predictions': predictions,
            'actuals': actuals,
            'threshold': threshold
        }
        
        return jsonify(chart_data)

@app.route('/plant_profile', methods=['GET', 'POST'])
@login_required
@admin_required
def plant_profile():
    """Route for managing plants"""
    plants = Plant.query.all()
    
    # Handle form submission for editing plants
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'edit':
            plant_id = request.form.get('plant_id')
            name = request.form.get('name')
            location = request.form.get('location')
            threshold_value = request.form.get('threshold_value')
            
            plant = Plant.query.get(plant_id)
            if plant:
                plant.name = name
                plant.location = location
                plant.threshold_value = float(threshold_value)
                db.session.commit()
                flash('Plant updated successfully', 'success')
        
        elif action == 'delete':
            plant_id = request.form.get('plant_id')
            plant = Plant.query.get(plant_id)
            if plant:
                db.session.delete(plant)
                db.session.commit()
                flash('Plant deleted successfully', 'success')
        
        return redirect(url_for('plant_profile'))
    
    return render_template('plant_profile.html', plants=plants)

# Add API routes for dashboard data
@app.route('/api/weather-data')
@login_required
def get_weather_data():
    """API endpoint for current weather data"""
    try:
        # Get user's plant location
        plant_id = request.args.get('plant_id', current_user.plant_id)
        if not plant_id:
            return jsonify({
                'success': False,
                'message': "No plant ID provided"
            })
            
        # Get the plant
        plant = Plant.query.get(plant_id)
        if not plant:
            return jsonify({
                'success': False,
                'message': "Plant not found"
            })
            
        # Use ML pipeline to get weather data
        from ml_pipeline.fetch_weather import fetch_weather_data
        
        # Get location from plant or use default
        weather_df = fetch_weather_data(location=plant.location)
        
        # Get current hour's data
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        # Find the closest hour in the data
        closest_row = None
        closest_time_diff = timedelta(days=365)  # Start with a very large value
        
        for _, row in weather_df.iterrows():
            time_diff = abs(row['time'] - current_hour)
            if time_diff < closest_time_diff:
                closest_time_diff = time_diff
                closest_row = row
                
        if closest_row is not None:
            # Determine weather condition based on metrics
            condition = "Unknown"
            if closest_row['Radiation'] > 500:
                condition = "Sunny"
            elif closest_row['Radiation'] > 200:
                condition = "Partly Cloudy"
            elif closest_row['Sunshine'] > 0:
                condition = "Cloudy"
            else:
                # Check for rain using humidity as a proxy
                if closest_row['RelativeAirHumidity'] > 80:
                    condition = "Rainy"
                else:
                    condition = "Overcast"
            
            # Return current weather data
            weather_data = {
                'condition': condition,
                'temperature': float(closest_row['AirTemperature']),
                'humidity': float(closest_row['RelativeAirHumidity']),
                'wind_speed': float(closest_row['WindSpeed']),
                'radiation': float(closest_row['Radiation']),
                'timestamp': closest_row['time'].strftime('%Y-%m-%d %H:%M:%S'),
                'air_pressure': float(closest_row['AirPressure'])
            }
            
            return jsonify({
                'success': True,
                'data': weather_data
            })
        else:
            return jsonify({
                'success': False,
                'message': "No weather data available"
            })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f"Error fetching weather data: {str(e)}"
        })

@app.route('/api/plant/<int:plant_id>')
@login_required
@admin_required
def get_plant_data(plant_id):
    """API endpoint for getting plant data for editing"""
    try:
        plant = Plant.query.get(plant_id)
        if not plant:
            return jsonify({
                'success': False,
                'message': 'Plant not found'
            })
        
        plant_data = {
            'id': plant.id,
            'name': plant.name,
            'location': plant.location,
            'type': plant.type,
            'threshold_value': plant.threshold_value
        }
        
        return jsonify({
            'success': True,
            'plant': plant_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error fetching plant data: {str(e)}"
        })

@app.route('/api/refresh-solar-data')
@login_required
def refresh_solar_data():
    """API endpoint to refresh solar generation data"""
    try:
        print("=== Starting solar data refresh via API ===")
        # Get user's plant
        plant_id = current_user.plant_id
        if not plant_id:
            print(f"Error: User {current_user.username} has no plant assigned")
            return jsonify({
                'success': False,
                'message': "No plant assigned to user"
            })
        
        print(f"Processing refresh for user: {current_user.username}, plant ID: {plant_id}")
        
        # Import ML pipeline modules - ensure app instance is available
        from ml_pipeline.fetch_weather import fetch_weather_data
        from ml_pipeline.predict_hourly import predict_hourly_generation
        from ml_pipeline.aggregate_daily import aggregate_daily_generation, filter_daylight_hours, save_predictions_to_db
        
        # Fetch weather data with plant location
        plant = Plant.query.get(plant_id)
        if not plant:
            print(f"Error: Plant with ID {plant_id} not found")
            return jsonify({
                'success': False,
                'message': "No plant assigned to user"
            })
        
        print(f"Found plant: {plant.name} (Type: {plant.type}, Location: {plant.location})")
        
        print(f"Fetching weather data for location: {plant.location}")
        weather_data = fetch_weather_data(location=plant.location)
        print(f"Fetched {len(weather_data)} weather records")
        
        # Predict hourly generation
        print("Generating hourly predictions...")
        hourly_predictions = predict_hourly_generation(weather_data, "solar", plant_id)
        print(f"Generated {len(hourly_predictions)} hourly predictions")
        
        # Filter to daylight hours for solar predictions
        filtered_predictions = filter_daylight_hours(hourly_predictions)
        print(f"Filtered to {len(filtered_predictions)} daylight hour predictions")
        
        # Aggregate to daily predictions
        daily_predictions = aggregate_daily_generation(filtered_predictions, plant.threshold_value)
        print(f"Aggregated to {len(daily_predictions)} daily predictions")
        
        # Save to database with direct MySQL connection
        print("Saving predictions to database...")
        save_predictions_to_db(hourly_predictions, daily_predictions, plant_id, None, "solar") 
        print("Database update completed")
        
        return jsonify({
            'success': True,
            'message': "Solar data refreshed successfully"
        })
    except Exception as e:
        print(f"Error refreshing solar data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f"Error refreshing solar data: {str(e)}"
        })

@app.route('/api/refresh-wind-data')
@login_required
def refresh_wind_data():
    """API endpoint to refresh wind generation data"""
    try:
        # Get user's plant
        plant_id = current_user.plant_id
        if not plant_id:
            return jsonify({
                'success': False,
                'message': "No plant assigned to user"
            })
        
        # Wind prediction not yet implemented
        return jsonify({
            'success': False,
            'message': "Wind prediction not yet implemented"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error refreshing wind data: {str(e)}"
        })

@app.route('/api/hourly_solar_data')
@login_required
def hourly_solar_data():
    """API endpoint for hourly solar generation data by date"""
    try:
        # Get parameters
        date_str = request.args.get('date')
        plant_id = request.args.get('plant_id', current_user.plant_id)
        
        if not plant_id:
            return jsonify({
                'success': False,
                'message': "No plant ID provided"
            })
        
        try:
            plant_id = int(plant_id)
        except ValueError:
            return jsonify({
                'success': False,
                'message': "Invalid plant ID"
            })
            
        # Parse date
        if date_str:
            try:
                selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': "Invalid date format. Use YYYY-MM-DD"
                })
        else:
            # Default to today
            selected_date = datetime.now().date()
        
        # Check if the date is in the future
        today = datetime.now().date()
        is_future_date = selected_date > today
        
        if is_future_date:
            # Generate predictive data for future dates
            from ml_pipeline.fetch_weather import fetch_weather_data
            from ml_pipeline.predict_hourly import predict_hourly_generation
            
            # Fetch weather forecast for the selected date
            try:
                # Get plant location for weather data
                plant = Plant.query.get(plant_id)
                if not plant:
                    return jsonify({
                        'success': False,
                        'message': "Plant not found"
                    })
                
                # For this example, we'll use a simple approach to generate future data
                # In a real app, you would use actual weather forecasts and your ML model
                
                # Get base pattern from most recent data
                recent_data = HourlySolarPrediction.query.filter(
                    HourlySolarPrediction.plant_id == plant_id
                ).order_by(HourlySolarPrediction.timestamp.desc()).limit(24).all()
                
                if not recent_data:
                    # No historical data to base predictions on
                    return jsonify({
                        'success': False,
                        'message': "No historical data available for predictions"
                    })
                
                # Generate future predictions
                future_hours = []
                future_predictions = []
                
                # Get the day difference to adjust values
                days_in_future = (selected_date - today).days
                day_factor = 1 + (days_in_future * 0.05)  # 5% variation per day
                
                # Generate 24 hours of data for the future date
                base_date = datetime.combine(selected_date, datetime.min.time())
                for hour in range(24):
                    hour_timestamp = base_date + timedelta(hours=hour)
                    future_hours.append(hour_timestamp.strftime('%H:%M'))
                    
                    # Get the corresponding hour from historical data
                    # Use a variation based on the day in the future (for demo purposes)
                    base_prediction = 0
                    for data in recent_data:
                        if data.timestamp.hour == hour:
                            base_prediction = data.predicted_generation or 0
                            break
                    
                    # Adjust prediction based on day factor and add some randomness
                    import random
                    random_factor = random.uniform(0.9, 1.1)  # ±10% random variation
                    adjusted_prediction = base_prediction * day_factor * random_factor
                    
                    # Solar should be near zero during night hours
                    if hour < 6 or hour > 18:
                        adjusted_prediction = adjusted_prediction * 0.1  # Minimal at night
                    
                    future_predictions.append(round(adjusted_prediction, 2))
                
                return jsonify({
                    'success': True,
                    'date': selected_date.strftime('%Y-%m-%d'),
                    'hours': future_hours,
                    'predictions': future_predictions,
                    'actuals': [0] * len(future_hours)  # Actuals will be empty for future dates
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f"Error generating future predictions: {str(e)}"
                })
        else:
            # For past dates, use actual database records
            hourly_data = HourlySolarPrediction.query.filter(
                HourlySolarPrediction.plant_id == plant_id,
                db.func.date(HourlySolarPrediction.timestamp) == selected_date
            ).order_by(HourlySolarPrediction.timestamp).all()
            
            if not hourly_data:
                return jsonify({
                    'success': False,
                    'message': f"No data found for date {date_str}"
                })
            
            # Format data for chart
            hours = [d.timestamp.strftime('%H:%M') for d in hourly_data]
            predictions = [float(d.predicted_generation) if d.predicted_generation else 0 for d in hourly_data]
            actuals = [float(d.actual_generation) if d.actual_generation else 0 for d in hourly_data]
            
            return jsonify({
                'success': True,
                'date': selected_date.strftime('%Y-%m-%d'),
                'hours': hours,
                'predictions': predictions,
                'actuals': actuals
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error fetching hourly data: {str(e)}"
        })

@app.route('/api/hourly_wind_data')
@login_required
def hourly_wind_data():
    """API endpoint for hourly wind generation data by date"""
    try:
        # Get parameters
        date_str = request.args.get('date')
        plant_id = request.args.get('plant_id', current_user.plant_id)
        
        if not plant_id:
            return jsonify({
                'success': False,
                'message': "No plant ID provided"
            })
        
        try:
            plant_id = int(plant_id)
        except ValueError:
            return jsonify({
                'success': False,
                'message': "Invalid plant ID"
            })
            
        # Parse date
        if date_str:
            try:
                selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': "Invalid date format. Use YYYY-MM-DD"
                })
        else:
            # Default to today
            selected_date = datetime.now().date()
        
        # Check if the date is in the future
        today = datetime.now().date()
        is_future_date = selected_date > today
        
        if is_future_date:
            # Generate predictive data for future dates
            try:
                # Get plant location for weather data
                plant = Plant.query.get(plant_id)
                if not plant:
                    return jsonify({
                        'success': False,
                        'message': "Plant not found"
                    })
                
                # For this example, we'll use a simple approach to generate future data
                # In a real app, you would use actual weather forecasts and your ML model
                
                # Get base pattern from most recent data
                recent_data = HourlyWindPrediction.query.filter(
                    HourlyWindPrediction.plant_id == plant_id
                ).order_by(HourlyWindPrediction.timestamp.desc()).limit(24).all()
                
                if not recent_data:
                    # No historical data to base predictions on
                    return jsonify({
                        'success': False,
                        'message': "No historical data available for predictions"
                    })
                
                # Generate future predictions
                future_hours = []
                future_predictions = []
                
                # Get the day difference to adjust values
                days_in_future = (selected_date - today).days
                day_factor = 1 + (days_in_future * 0.07)  # 7% variation per day for wind
                
                # Generate 24 hours of data for the future date
                base_date = datetime.combine(selected_date, datetime.min.time())
                for hour in range(24):
                    hour_timestamp = base_date + timedelta(hours=hour)
                    future_hours.append(hour_timestamp.strftime('%H:%M'))
                    
                    # Get the corresponding hour from historical data
                    # Use a variation based on the day in the future (for demo purposes)
                    base_prediction = 0
                    for data in recent_data:
                        if data.timestamp.hour == hour:
                            base_prediction = data.predicted_generation or 0
                            break
                    
                    # Adjust prediction based on day factor and add some randomness
                    import random
                    random_factor = random.uniform(0.85, 1.15)  # ±15% random variation
                    adjusted_prediction = base_prediction * day_factor * random_factor
                    
                    # Wind doesn't necessarily follow day/night patterns as strongly as solar
                    future_predictions.append(round(adjusted_prediction, 2))
                
                return jsonify({
                    'success': True,
                    'date': selected_date.strftime('%Y-%m-%d'),
                    'hours': future_hours,
                    'predictions': future_predictions,
                    'actuals': [0] * len(future_hours)  # Actuals will be empty for future dates
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f"Error generating future predictions: {str(e)}"
                })
        else:
            # For past dates, use actual database records
            hourly_data = HourlyWindPrediction.query.filter(
                HourlyWindPrediction.plant_id == plant_id,
                db.func.date(HourlyWindPrediction.timestamp) == selected_date
            ).order_by(HourlyWindPrediction.timestamp).all()
            
            if not hourly_data:
                return jsonify({
                    'success': False,
                    'message': f"No data found for date {date_str}"
                })
            
            # Format data for chart
            hours = [d.timestamp.strftime('%H:%M') for d in hourly_data]
            predictions = [float(d.predicted_generation) if d.predicted_generation else 0 for d in hourly_data]
            actuals = [float(d.actual_generation) if d.actual_generation else 0 for d in hourly_data]
            
            return jsonify({
                'success': True,
                'date': selected_date.strftime('%Y-%m-%d'),
                'hours': hours,
                'predictions': predictions,
                'actuals': actuals
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error fetching hourly data: {str(e)}"
        })


if __name__ == '__main__':
    # Initialize the database before running the app
    init_db()
    
    # Create all tables
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully.")
        except Exception as e:
            print(f"Error creating database tables: {e}")
    
    app.run(debug=True) 