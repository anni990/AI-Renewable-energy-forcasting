import os
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
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

# Custom filter for division
@app.template_filter('divide')
def _jinja2_filter_divide(value, divisor):
    try:
        return float(value) / float(divisor)
    except (ValueError, ZeroDivisionError):
        return 0

# Custom filter for date formatting with strftime
@app.template_filter('strftime')
def _jinja2_filter_strftime(date, fmt=None):
    if fmt is None:
        fmt = '%Y-%m-%d'
    if date is None:
        return ''
    return date.strftime(fmt)

# Register now() as a global function in Jinja2
app.jinja_env.globals['now'] = datetime.now
# Make timedelta available in templates
app.jinja_env.globals['timedelta'] = timedelta

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
                            print("Processing wind plant predictions...")
                            # Import wind-specific modules
                            from ml_pipeline.fetch_weather import fetch_wind_weather_data
                            from ml_pipeline.predict_hourly import predict_hourly_generation
                            from ml_pipeline.aggregate_daily import aggregate_daily_generation, save_predictions_to_db
                            
                            # Get wind-specific weather data
                            wind_weather_data = fetch_wind_weather_data(location=plant.location)
                            print(f"Fetched {len(wind_weather_data)} wind weather records")
                            
                            # Predict hourly generation
                            hourly_predictions = predict_hourly_generation(wind_weather_data, "wind", plant.id)
                            print(f"Generated {len(hourly_predictions)} hourly wind predictions")
                            
                            # Aggregate to daily predictions
                            daily_predictions = aggregate_daily_generation(hourly_predictions, plant.threshold_value)
                            print(f"Aggregated to {len(daily_predictions)} daily wind predictions")
                            
                            # Save to database
                            print("Saving wind predictions to database...")
                            save_predictions_to_db(hourly_predictions, daily_predictions, plant.id, None, "wind")
                            print("Wind database update completed")
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
    """Dashboard route - redirects to appropriate dashboard based on user role and plant type"""
    # Admin sees a different dashboard
    if current_user.role == 'admin':
        # Get all plants
        plants = Plant.query.all()
        
        # Get today's date
        today = datetime.utcnow().date()
        
        # Get plant lists for each type
        solar_plants = Plant.query.filter_by(type='solar').all()
        wind_plants = Plant.query.filter_by(type='wind').all()
        
        # Get daily predictions for solar plants
        solar_predictions = db.session.query(
            DailySolarPrediction,
            Plant.name.label('plant_name')
        ).join(Plant).filter(
            DailySolarPrediction.date >= today
        ).order_by(DailySolarPrediction.date, Plant.name).all()
        
        # Format solar predictions for display
        formatted_solar_predictions = []
        for prediction, plant_name in solar_predictions:
            formatted_solar_predictions.append({
                'plant_name': plant_name,
                'date': prediction.date.strftime('%Y-%m-%d'),
                'total_predicted_generation': round(prediction.total_predicted_generation, 2) if prediction.total_predicted_generation else 0,
                'total_actual_generation': round(prediction.total_actual_generation, 2) if prediction.total_actual_generation else None,
                'recommendation_status': prediction.recommendation_status,
                'recommendation_message': prediction.recommendation_message
            })
        
        # Get daily predictions for wind plants
        wind_predictions = db.session.query(
            DailyWindPrediction,
            Plant.name.label('plant_name')
        ).join(Plant).filter(
            DailyWindPrediction.date >= today
        ).order_by(DailyWindPrediction.date, Plant.name).all()
        
        # Format wind predictions for display
        formatted_wind_predictions = []
        for prediction, plant_name in wind_predictions:
            formatted_wind_predictions.append({
                'plant_name': plant_name,
                'date': prediction.date.strftime('%Y-%m-%d'),
                'total_predicted_generation': round(prediction.total_predicted_generation, 2) if prediction.total_predicted_generation else 0,
                'total_actual_generation': round(prediction.total_actual_generation, 2) if prediction.total_actual_generation else None,
                'recommendation_status': prediction.recommendation_status,
                'recommendation_message': prediction.recommendation_message
            })
        
        # Get hourly predictions for today for all solar plants
        solar_hourly = db.session.query(
            HourlySolarPrediction,
            Plant.name.label('plant_name')
        ).join(Plant).filter(
            func.date(HourlySolarPrediction.timestamp) == today
        ).order_by(HourlySolarPrediction.timestamp, Plant.name).all()
        
        # Format hourly solar data for charts
        formatted_solar_hourly = []
        for prediction, plant_name in solar_hourly:
            formatted_solar_hourly.append({
                'plant_name': plant_name,
                'hour': prediction.timestamp.strftime('%H:%M'),
                'timestamp': prediction.timestamp.strftime('%Y-%m-%d %H:%M'),
                'predicted_generation': round(prediction.predicted_generation, 2) if prediction.predicted_generation else 0,
                'actual_generation': round(prediction.actual_generation, 2) if prediction.actual_generation else 0
            })
        
        # Get hourly predictions for today for all wind plants
        wind_hourly = db.session.query(
            HourlyWindPrediction,
            Plant.name.label('plant_name')
        ).join(Plant).filter(
            func.date(HourlyWindPrediction.timestamp) == today
        ).order_by(HourlyWindPrediction.timestamp, Plant.name).all()
        
        # Format hourly wind data for charts
        formatted_wind_hourly = []
        for prediction, plant_name in wind_hourly:
            formatted_wind_hourly.append({
                'plant_name': plant_name,
                'hour': prediction.timestamp.strftime('%H:%M'),
                'timestamp': prediction.timestamp.strftime('%Y-%m-%d %H:%M'),
                'predicted_generation': round(prediction.predicted_generation, 2) if prediction.predicted_generation else 0,
                'actual_generation': round(prediction.actual_generation, 2) if prediction.actual_generation else 0
            })
            
        # Get solar recommendations/alerts
        solar_recommendations = db.session.query(
            DailySolarPrediction,
            Plant.name.label('plant_name')
        ).join(Plant).filter(
            DailySolarPrediction.date >= today,
            DailySolarPrediction.recommendation_status == True
        ).order_by(DailySolarPrediction.date).all()
        
        # Format solar recommendations
        formatted_solar_recommendations = []
        for recommendation, plant_name in solar_recommendations:
            formatted_solar_recommendations.append({
                'plant_name': plant_name,
                'date': recommendation.date.strftime('%Y-%m-%d'),
                'message': recommendation.recommendation_message or 'Energy generation below threshold'
            })
            
        # Get wind recommendations/alerts
        wind_recommendations = db.session.query(
            DailyWindPrediction,
            Plant.name.label('plant_name')
        ).join(Plant).filter(
            DailyWindPrediction.date >= today,
            DailyWindPrediction.recommendation_status == True
        ).order_by(DailyWindPrediction.date).all()
        
        # Format wind recommendations
        formatted_wind_recommendations = []
        for recommendation, plant_name in wind_recommendations:
            formatted_wind_recommendations.append({
                'plant_name': plant_name,
                'date': recommendation.date.strftime('%Y-%m-%d'),
                'message': recommendation.recommendation_message or 'Energy generation below threshold'
            })
            
        # Get available dates for hourly data selection
        available_dates = db.session.query(
            func.date(HourlySolarPrediction.timestamp).label('date')
        ).distinct().order_by(
            func.date(HourlySolarPrediction.timestamp).desc()
        ).limit(7).all()
        
        date_options = [date[0].strftime('%Y-%m-%d') for date in available_dates]
        
        # Prepare data for daily charts
        # Solar daily chart data - get last 7 days
        solar_daily_data_query = db.session.query(
            DailySolarPrediction.date,
            func.sum(DailySolarPrediction.total_predicted_generation).label('predicted'),
            func.sum(DailySolarPrediction.total_actual_generation).label('actual')
        ).group_by(DailySolarPrediction.date).order_by(DailySolarPrediction.date.desc()).limit(7).all()
        
        # Add fallback data if no results
        if not solar_daily_data_query:
            print("No solar daily data found, using fallback data")
            # Use the last 7 days as fallback dates
            fallback_dates = []
            for i in range(7):
                date = today - timedelta(days=i)
                fallback_dates.append((date, 0, 0))
            solar_daily_data_query = fallback_dates
        
        solar_daily_data = {
            'dates': [d[0].strftime('%Y-%m-%d') if isinstance(d, tuple) else d.date.strftime('%Y-%m-%d') for d in solar_daily_data_query],
            'predictions': [float(d[1]) if isinstance(d, tuple) else float(d.predicted) if d.predicted else 0 for d in solar_daily_data_query],
            'actuals': [float(d[2]) if isinstance(d, tuple) else float(d.actual) if d.actual else 0 for d in solar_daily_data_query]
        }
        
        # Wind daily chart data - get last 7 days
        wind_daily_data_query = db.session.query(
            DailyWindPrediction.date,
            func.sum(DailyWindPrediction.total_predicted_generation).label('predicted'),
            func.sum(DailyWindPrediction.total_actual_generation).label('actual')
        ).group_by(DailyWindPrediction.date).order_by(DailyWindPrediction.date.desc()).limit(7).all()
        
        # Add fallback data if no results
        if not wind_daily_data_query:
            print("No wind daily data found, using fallback data")
            # Use the last 7 days as fallback dates
            fallback_dates = []
            for i in range(7):
                date = today - timedelta(days=i)
                fallback_dates.append((date, 0, 0))
            wind_daily_data_query = fallback_dates
        
        wind_daily_data = {
            'dates': [d[0].strftime('%Y-%m-%d') if isinstance(d, tuple) else d.date.strftime('%Y-%m-%d') for d in wind_daily_data_query],
            'predictions': [float(d[1]) if isinstance(d, tuple) else float(d.predicted) if d.predicted else 0 for d in wind_daily_data_query],
            'actuals': [float(d[2]) if isinstance(d, tuple) else float(d.actual) if d.actual else 0 for d in wind_daily_data_query]
        }
        
        print("Solar daily data:", solar_daily_data)
        print("Wind daily data:", wind_daily_data)
        
        return render_template('admin_dashboard.html', 
                              plants=plants,
                              solar_plants=solar_plants,
                              wind_plants=wind_plants,
                              solar_predictions=formatted_solar_predictions,
                              wind_predictions=formatted_wind_predictions,
                              solar_hourly=formatted_solar_hourly,
                              wind_hourly=formatted_wind_hourly,
                              solar_recommendations=formatted_solar_recommendations,
                              wind_recommendations=formatted_wind_recommendations,
                              solar_daily_data=solar_daily_data,
                              wind_daily_data=wind_daily_data,
                              total_users=User.query.count(),
                              today=today.strftime('%Y-%m-%d'),
                              date_options=date_options)
    
    # Get the user's plant
    plant = None
    if current_user.plant_id:
        plant = Plant.query.get(current_user.plant_id)
        
    # Determine which dashboard to show based on plant type
    if current_user.plant_type == 'solar':
        # Get today and five days in the future
        today = datetime.utcnow().date()
        
        # Get hourly solar predictions for today
        solar_data = HourlySolarPrediction.query.filter(
            HourlySolarPrediction.plant_id == current_user.plant_id,
            func.date(HourlySolarPrediction.timestamp) == today
        ).all()
        
        # If no data for today, run forecast update
        if not solar_data and plant:
            from ml_pipeline.fetch_weather import fetch_weather_data
            from ml_pipeline.predict_hourly import predict_hourly_generation
            from ml_pipeline.aggregate_daily import filter_daylight_hours, aggregate_daily_generation, save_predictions_to_db
            
            print(f"No solar data found for today, running forecast update for plant {plant.id}")
            
            try:
                # Get weather forecast
                weather_data = fetch_weather_data(plant.location)
                
                # Predict hourly generation
                hourly_predictions = predict_hourly_generation(weather_data, "solar", plant.id)
                
                # Filter to daylight hours
                filtered_predictions = filter_daylight_hours(hourly_predictions)
                
                # Aggregate to daily
                daily_predictions = aggregate_daily_generation(filtered_predictions, plant.threshold_value)
                
                # Save to database
                save_predictions_to_db(filtered_predictions, daily_predictions, plant.id, db, "solar")
                
                # Refresh data from database
                solar_data = HourlySolarPrediction.query.filter(
                    HourlySolarPrediction.plant_id == current_user.plant_id,
                    func.date(HourlySolarPrediction.timestamp) == today
                ).all()
            except Exception as e:
                print(f"Error updating forecasts: {str(e)}")
                import traceback
                print(traceback.format_exc())
        
        # Get daily solar predictions
        daily_solar_data = DailySolarPrediction.query.filter(
            DailySolarPrediction.plant_id == current_user.plant_id,
            DailySolarPrediction.date >= today
        ).order_by(DailySolarPrediction.date).all()
        
        # Get recommendations (predictions below threshold)
        recommendations = []
        for prediction in daily_solar_data:
            if prediction.recommendation_status:
                recommendations.append({
                    'date': prediction.date.strftime('%Y-%m-%d'),
                    'message': prediction.recommendation_message or 'Energy generation below threshold'
                })
        
        # Render solar dashboard
        return render_template('solar_dashboard.html', 
                              plant=plant,
                              solar_data=solar_data,
                              daily_solar_data=daily_solar_data,
                              recommendations=recommendations,
                              today=today)
    
    elif current_user.plant_type == 'wind':
        # Get today and five days in the future
        today = datetime.utcnow().date()
        
        # Check if we've already generated predictions for today and upcoming days
        existing_daily_predictions = DailyWindPrediction.query.filter(
            DailyWindPrediction.plant_id == current_user.plant_id,
            DailyWindPrediction.date >= today
        ).count()
        
        # Get hourly wind predictions for today
        wind_data = HourlyWindPrediction.query.filter(
            HourlyWindPrediction.plant_id == current_user.plant_id,
            func.date(HourlyWindPrediction.timestamp) == today
        ).all()
        
        # If no data for today AND no predictions for upcoming days, run forecast update
        if not wind_data and existing_daily_predictions == 0 and plant:
            from ml_pipeline.fetch_weather import fetch_wind_weather_data
            from ml_pipeline.predict_hourly import predict_hourly_generation
            from ml_pipeline.aggregate_daily import aggregate_daily_generation, save_predictions_to_db
            
            print(f"No wind data found for today, running forecast update for plant {plant.id}")
            
            try:
                # Get weather forecast for wind
                weather_data = fetch_wind_weather_data(location=plant.location)
                
                # Predict hourly generation
                hourly_predictions = predict_hourly_generation(weather_data, "wind", plant.id)
                
                # Aggregate to daily
                daily_predictions = aggregate_daily_generation(hourly_predictions, plant.threshold_value)
                
                # Save to database
                save_predictions_to_db(hourly_predictions, daily_predictions, plant.id, db, "wind")
                
                # Refresh data from database
                wind_data = HourlyWindPrediction.query.filter(
                    HourlyWindPrediction.plant_id == current_user.plant_id,
                    func.date(HourlyWindPrediction.timestamp) == today
                ).all()
            except Exception as e:
                print(f"Error updating wind forecasts: {str(e)}")
                import traceback
                print(traceback.format_exc())
        
        # Get daily wind predictions
        daily_wind_data = DailyWindPrediction.query.filter(
            DailyWindPrediction.plant_id == current_user.plant_id,
            DailyWindPrediction.date >= today
        ).order_by(DailyWindPrediction.date).all()
        
        # Get recommendations (predictions below threshold)
        recommendations = []
        below_threshold_data = []
        for prediction in daily_wind_data:
            if prediction.recommendation_status or (
                prediction.total_predicted_generation and 
                plant and 
                plant.threshold_value and 
                prediction.total_predicted_generation < plant.threshold_value
            ):
                # Calculate energy deficit
                energy_deficit = 0
                if prediction.total_predicted_generation and plant and plant.threshold_value:
                    energy_deficit = max(0, plant.threshold_value - prediction.total_predicted_generation)
                    
                below_threshold_data.append({
                    'date': prediction.date.strftime('%Y-%m-%d'),  # Format as string for JSON
                    'predicted_generation': prediction.total_predicted_generation,
                    'threshold': plant.threshold_value if plant else 0,
                    'deficit': energy_deficit
                })
        
        # Render wind dashboard
        return render_template('wind_dashboard.html', 
                              plant=plant,
                              wind_data=wind_data,
                              daily_wind_data=daily_wind_data,
                              recommendations=recommendations,
                              today=today)
    
    # Default case - no plant type specified
    return render_template('dashboard_setup.html')

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
            return redirect(url_for('update_wind_forecasts'))
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
    """Route to update both solar and wind forecasts"""
    try:
        # Update solar forecasts
        print("=== Starting update of all forecasts ===")
        print("=== Updating solar forecasts ===")
        
        # Import solar ML pipeline modules
        from ml_pipeline.fetch_weather import fetch_weather_data
        from ml_pipeline.predict_hourly import predict_hourly_generation
        from ml_pipeline.aggregate_daily import aggregate_daily_generation, filter_daylight_hours, save_predictions_to_db
        
        # Get all solar plants
        solar_plants = Plant.query.filter_by(type='solar').all()
        print(f"Found {len(solar_plants)} solar plants")
        
        for plant in solar_plants:
            print(f"Processing solar plant: {plant.name} (ID: {plant.id})")
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
            
        # Update wind forecasts
        print("=== Updating wind forecasts ===")
        
        # Import wind ML pipeline modules
        from ml_pipeline.fetch_weather import fetch_wind_weather_data
        
        # Get all wind plants
        wind_plants = Plant.query.filter_by(type='wind').all()
        print(f"Found {len(wind_plants)} wind plants")
        
        for plant in wind_plants:
            print(f"Processing wind plant: {plant.name} (ID: {plant.id})")
            # Fetch wind weather data with plant location
            weather_data = fetch_wind_weather_data(location=plant.location)
            print(f"Fetched {len(weather_data)} wind weather records for plant {plant.id}")
            
            # Predict hourly generation
            hourly_predictions = predict_hourly_generation(weather_data, "wind", plant.id)
            print(f"Generated {len(hourly_predictions)} hourly predictions for plant {plant.id}")
            
            # Aggregate to daily predictions
            daily_predictions = aggregate_daily_generation(hourly_predictions, plant.threshold_value)
            print(f"Aggregated to {len(daily_predictions)} daily predictions for plant {plant.id}")
            
            # Save to database
            print(f"Saving predictions to database for plant {plant.id}...")
            save_predictions_to_db(hourly_predictions, daily_predictions, plant.id, None, "wind")
            print(f"Database update completed for plant {plant.id}")
        
        flash('All forecasts updated successfully', 'success')
        print("=== Completed update of all forecasts ===")
    except Exception as e:
        print(f"Error updating forecasts: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash(f'Error updating forecasts: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

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

@app.route('/api/refresh-wind-data')
@login_required
def refresh_wind_data():
    """API endpoint to refresh wind prediction data"""
    try:
        # Get the plant associated with the user
        if not current_user.plant_id:
            return jsonify({
                'success': False,
                'message': 'No plant associated with this user'
            })
        
        plant = Plant.query.get(current_user.plant_id)
        if not plant:
            return jsonify({
                'success': False,
                'message': 'Plant not found'
            })
        
        # Import required modules
        from ml_pipeline.fetch_weather import fetch_wind_weather_data
        from ml_pipeline.predict_hourly import predict_hourly_generation
        from ml_pipeline.aggregate_daily import aggregate_daily_generation, save_predictions_to_db
        
        # Get weather forecast for wind
        weather_data = fetch_wind_weather_data(plant.location)
        
        # Predict hourly generation
        hourly_predictions = predict_hourly_generation(weather_data, "wind", plant.id)
        
        # Aggregate to daily
        daily_predictions = aggregate_daily_generation(hourly_predictions, plant.threshold_value)
        
        # Save to database
        save_predictions_to_db(hourly_predictions, daily_predictions, plant.id, db, "wind")
        
        return jsonify({
            'success': True,
            'message': 'Wind power forecasts updated successfully'
        })
        
    except Exception as e:
        print(f"Error refreshing wind data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/api/wind_chart_data')
@login_required
def wind_chart_data():
    """API endpoint to get wind chart data for the user's plant"""
    plant_id = request.args.get('plant_id', default=current_user.plant_id, type=int)
    
    if not plant_id:
        return jsonify({
            'success': False,
            'message': 'No plant ID specified'
        })
    
    try:
        # Get today's date
        today = datetime.utcnow().date()
        
        # Get the next 6 days of predictions
        predictions = DailyWindPrediction.query.filter(
            DailyWindPrediction.plant_id == plant_id,
            DailyWindPrediction.date >= today
        ).order_by(DailyWindPrediction.date).limit(6).all()
        
        # Get plant threshold
        plant = Plant.query.get(plant_id)
        threshold = plant.threshold_value if plant else 0
        
        # Format the data for the chart
        dates = []
        prediction_values = []
        actual_values = []
        
        for pred in predictions:
            dates.append(pred.date.strftime('%Y-%m-%d'))
            prediction_values.append(float(pred.total_predicted_generation) if pred.total_predicted_generation else 0)
            actual_values.append(float(pred.total_actual_generation) if pred.total_actual_generation else 0)
        
        return jsonify({
            'success': True,
            'dates': dates,
            'predictions': prediction_values,
            'actuals': actual_values,
            'threshold': threshold
        })
        
    except Exception as e:
        print(f"Error fetching wind chart data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/api/hourly_wind_data')
@login_required
def hourly_wind_data():
    """API endpoint to get hourly wind prediction data for a specific date"""
    plant_id = request.args.get('plant_id', default=current_user.plant_id, type=int)
    date_str = request.args.get('date', default=None)
    
    if not plant_id:
        return jsonify({
            'success': False,
            'message': 'No plant ID specified'
        })
    
    if not date_str:
        # Default to today if no date provided
        date_str = datetime.utcnow().date().strftime('%Y-%m-%d')
    
    try:
        # Parse the date string
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get hourly predictions for the specified date
        hourly_predictions = HourlyWindPrediction.query.filter(
            HourlyWindPrediction.plant_id == plant_id,
            func.date(HourlyWindPrediction.timestamp) == date_obj
        ).order_by(HourlyWindPrediction.timestamp).all()
        
        # Format the data for the chart
        hours = []
        prediction_values = []
        actual_values = []
        
        for pred in hourly_predictions:
            hours.append(pred.timestamp.strftime('%H:%M'))
            prediction_values.append(float(pred.predicted_generation) if pred.predicted_generation else 0)
            actual_values.append(float(pred.actual_generation) if pred.actual_generation else 0)
        
        return jsonify({
            'success': True,
            'date': date_str,
            'hours': hours,
            'predictions': prediction_values,
            'actuals': actual_values
        })
        
    except Exception as e:
        print(f"Error fetching hourly wind data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

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
            # Check if required fields are in the data
            has_wind_direction = 'WindDirection' in closest_row
            
            weather_data = {
                'condition': condition,
                'temperature': float(closest_row['AirTemperature']),
                'humidity': float(closest_row['RelativeAirHumidity']),
                'wind_speed': float(closest_row['WindSpeed']),
                'wind_direction': float(closest_row['WindDirection']) if has_wind_direction else 'N/A',
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

@app.route('/api/hourly_solar_data', methods=['GET', 'POST'])
@login_required
def hourly_solar_data():
    """API endpoint to get hourly solar prediction data for a specific date"""
    plant_id = request.args.get('plant_id', default=current_user.plant_id, type=int)
    date_str = request.args.get('date', default=None)
    
    if not plant_id:
        return jsonify({
            'success': False,
            'message': 'No plant ID specified'
        })
    
    if not date_str:
        # Default to today if no date provided
        date_str = datetime.utcnow().date().strftime('%Y-%m-%d')
    
    try:
        # Parse the date string
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get hourly predictions for the specified date
        hourly_predictions = HourlySolarPrediction.query.filter(
            HourlySolarPrediction.plant_id == plant_id,
            func.date(HourlySolarPrediction.timestamp) == date_obj
        ).order_by(HourlySolarPrediction.timestamp).all()
        
        # Format the data for the chart
        hours = []
        prediction_values = []
        actual_values = []
        
        # Check if we have data
        if not hourly_predictions:
            print(f"No solar hourly data found for date {date_str} and plant {plant_id}")
            # Return fallback data - solar data typically available between 6am and 6pm
            fallback_hours = [(datetime.strptime(f"{date_str} {h:02d}:00", '%Y-%m-%d %H:%M')).strftime('%H:%M') for h in range(6, 19)]  # 6am to 6pm
            
            return jsonify({
                'success': True,
                'date': date_str,
                'hours': fallback_hours,
                'predictions': [0] * len(fallback_hours),
                'actuals': [0] * len(fallback_hours),
                'message': 'No data available for the selected date'
            })
        
        for pred in hourly_predictions:
            hours.append(pred.timestamp.strftime('%H:%M'))
            prediction_values.append(float(pred.predicted_generation) if pred.predicted_generation else 0)
            actual_values.append(float(pred.actual_generation) if pred.actual_generation else 0)
        
        return jsonify({
            'success': True,
            'date': date_str,
            'hours': hours,
            'predictions': prediction_values,
            'actuals': actual_values
        })
        
    except Exception as e:
        print(f"Error fetching hourly solar data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/update_wind_forecasts')
@login_required
@admin_required
def update_wind_forecasts():
    """Route to update wind forecasts for all wind plants"""
    try:
        print("=== Starting update_wind_forecasts route ===")
        # Import ML pipeline modules
        from ml_pipeline.fetch_weather import fetch_wind_weather_data
        from ml_pipeline.predict_hourly import predict_hourly_generation
        from ml_pipeline.aggregate_daily import aggregate_daily_generation, save_predictions_to_db
        
        # Get all wind plants
        wind_plants = Plant.query.filter_by(type='wind').all()
        print(f"Found {len(wind_plants)} wind plants")
        
        for plant in wind_plants:
            print(f"Processing plant: {plant.name} (ID: {plant.id})")
            # Fetch wind weather data with plant location
            weather_data = fetch_wind_weather_data(location=plant.location)
            print(f"Fetched {len(weather_data)} wind weather records for plant {plant.id}")
            
            # Predict hourly generation
            hourly_predictions = predict_hourly_generation(weather_data, "wind", plant.id)
            print(f"Generated {len(hourly_predictions)} hourly predictions for plant {plant.id}")
            
            # Aggregate to daily predictions
            daily_predictions = aggregate_daily_generation(hourly_predictions, plant.threshold_value)
            print(f"Aggregated to {len(daily_predictions)} daily predictions for plant {plant.id}")
            
            # Save to database
            print(f"Saving predictions to database for plant {plant.id}...")
            save_predictions_to_db(hourly_predictions, daily_predictions, plant.id, None, "wind")
            print(f"Database update completed for plant {plant.id}")
        
        flash('Wind forecasts updated successfully', 'success')
        print("=== Completed update_wind_forecasts route ===")
    except Exception as e:
        print(f"Error updating wind forecasts: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash(f'Error updating wind forecasts: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/api/admin_hourly_data')
@login_required
@admin_required
def admin_hourly_data():
    """API endpoint to get hourly data for a specific date for the admin dashboard"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    date_str = request.args.get('date', None)
    energy_type = request.args.get('type', 'solar')  # 'solar' or 'wind'
    plant_id = request.args.get('plant_id', 'all')  # Get plant_id parameter, default to 'all'
    
    if not date_str:
        # Default to today if no date provided
        date_str = datetime.utcnow().date().strftime('%Y-%m-%d')
    
    try:
        # Parse the date string
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        if energy_type == 'solar':
            # Get hourly solar predictions for the specified date for all plants
            query = db.session.query(
                HourlySolarPrediction,
                Plant.name.label('plant_name')
            ).join(Plant).filter(
                func.date(HourlySolarPrediction.timestamp) == date_obj
            )
            
            # Filter by plant_id if specified
            if plant_id != 'all':
                try:
                    plant_id = int(plant_id)
                    query = query.filter(Plant.id == plant_id)
                except ValueError:
                    return jsonify({'success': False, 'message': 'Invalid plant ID format'}), 400
                
            hourly_data = query.order_by(HourlySolarPrediction.timestamp, Plant.name).all()
            
            # Group data by hour for all plants
            hours = []
            grouped_data = {}
            
            # Check if we have data
            if not hourly_data:
                print(f"No solar hourly data found for date {date_str} and plant {plant_id}")
                # Return fallback data
                current_hour = datetime.now().hour
                fallback_hours = [(datetime.strptime(f"{date_str} {h:02d}:00", '%Y-%m-%d %H:%M')).strftime('%H:%M') for h in range(6, 19)]  # 6am to 6pm
                
                return jsonify({
                    'success': True,
                    'type': 'solar',
                    'date': date_str,
                    'hours': fallback_hours,
                    'plant_names': ['No Data'],
                    'plant_data': {'No Data': {'predicted': [0] * len(fallback_hours), 'actual': [0] * len(fallback_hours)}},
                    'total_predicted': [0] * len(fallback_hours),
                    'total_actual': [0] * len(fallback_hours),
                    'message': 'No data available for the selected date and plant'
                })
            
            for prediction, plant_name in hourly_data:
                hour = prediction.timestamp.strftime('%H:%M')
                
                if hour not in hours:
                    hours.append(hour)
                
                if plant_name not in grouped_data:
                    grouped_data[plant_name] = {
                        'predicted': [],
                        'actual': []
                    }
                
                grouped_data[plant_name]['predicted'].append(float(prediction.predicted_generation) if prediction.predicted_generation else 0)
                grouped_data[plant_name]['actual'].append(float(prediction.actual_generation) if prediction.actual_generation else 0)
            
            # Get plant names array
            plant_names = list(grouped_data.keys())
            
            # Get total predicted and actual for each hour
            total_predicted = []
            total_actual = []
            
            for hour_idx in range(len(hours)):
                hour_predicted = 0
                hour_actual = 0
                
                for plant in plant_names:
                    if hour_idx < len(grouped_data[plant]['predicted']):
                        hour_predicted += grouped_data[plant]['predicted'][hour_idx]
                    
                    if hour_idx < len(grouped_data[plant]['actual']):
                        hour_actual += grouped_data[plant]['actual'][hour_idx]
                
                total_predicted.append(round(hour_predicted, 2))
                total_actual.append(round(hour_actual, 2))
            
            return jsonify({
                'success': True,
                'type': 'solar',
                'date': date_str,
                'hours': hours,
                'plant_names': plant_names,
                'plant_data': grouped_data,
                'total_predicted': total_predicted,
                'total_actual': total_actual
            })
            
        elif energy_type == 'wind':
            # Get hourly wind predictions for the specified date for all plants
            query = db.session.query(
                HourlyWindPrediction,
                Plant.name.label('plant_name')
            ).join(Plant).filter(
                func.date(HourlyWindPrediction.timestamp) == date_obj
            )
            
            # Filter by plant_id if specified
            if plant_id != 'all':
                try:
                    plant_id = int(plant_id)
                    query = query.filter(Plant.id == plant_id)
                except ValueError:
                    return jsonify({'success': False, 'message': 'Invalid plant ID format'}), 400
                
            hourly_data = query.order_by(HourlyWindPrediction.timestamp, Plant.name).all()
            
            # Group data by hour for all plants
            hours = []
            grouped_data = {}
            
            # Check if we have data
            if not hourly_data:
                print(f"No wind hourly data found for date {date_str} and plant {plant_id}")
                # Return fallback data - wind data is usually available for all 24 hours
                fallback_hours = [(datetime.strptime(f"{date_str} {h:02d}:00", '%Y-%m-%d %H:%M')).strftime('%H:%M') for h in range(0, 24)]
                
                return jsonify({
                    'success': True,
                    'type': 'wind',
                    'date': date_str,
                    'hours': fallback_hours,
                    'plant_names': ['No Data'],
                    'plant_data': {'No Data': {'predicted': [0] * len(fallback_hours), 'actual': [0] * len(fallback_hours)}},
                    'total_predicted': [0] * len(fallback_hours),
                    'total_actual': [0] * len(fallback_hours),
                    'message': 'No data available for the selected date and plant'
                })
            
            for prediction, plant_name in hourly_data:
                hour = prediction.timestamp.strftime('%H:%M')
                
                if hour not in hours:
                    hours.append(hour)
                
                if plant_name not in grouped_data:
                    grouped_data[plant_name] = {
                        'predicted': [],
                        'actual': []
                    }
                
                grouped_data[plant_name]['predicted'].append(float(prediction.predicted_generation) if prediction.predicted_generation else 0)
                grouped_data[plant_name]['actual'].append(float(prediction.actual_generation) if prediction.actual_generation else 0)
            
            # Get plant names array
            plant_names = list(grouped_data.keys())
            
            # Get total predicted and actual for each hour
            total_predicted = []
            total_actual = []
            
            for hour_idx in range(len(hours)):
                hour_predicted = 0
                hour_actual = 0
                
                for plant in plant_names:
                    if hour_idx < len(grouped_data[plant]['predicted']):
                        hour_predicted += grouped_data[plant]['predicted'][hour_idx]
                    
                    if hour_idx < len(grouped_data[plant]['actual']):
                        hour_actual += grouped_data[plant]['actual'][hour_idx]
                
                total_predicted.append(round(hour_predicted, 2))
                total_actual.append(round(hour_actual, 2))
            
            # Debug log to check data structure before sending response
            print(f"Wind hourly data response: hours={len(hours)}, plants={len(plant_names)}, data points={len(total_predicted)}")
            
            return jsonify({
                'success': True,
                'type': 'wind',
                'date': date_str,
                'hours': hours,
                'plant_names': plant_names,
                'plant_data': grouped_data,
                'total_predicted': total_predicted,
                'total_actual': total_actual
            })
        
        else:
            return jsonify({
                'success': False,
                'message': f'Invalid energy type: {energy_type}'
            })
        
    except Exception as e:
        print(f"Error fetching admin hourly data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/manage_users', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_users():
    """Route for managing users - admin only"""
    
    # Handle form submission for user management
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            # Get form data
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role')
            plant_id = request.form.get('plant_id')
            plant_type = request.form.get('plant_type')
            
            # Validate required fields
            if not username or not email or not password:
                flash('Username, email, and password are required', 'danger')
                return redirect(url_for('manage_users'))
            
            # Check if username or email already exists
            existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
            if existing_user:
                flash('Username or email already exists', 'danger')
                return redirect(url_for('manage_users'))
            
            # Create new user
            try:
                # Create password hash
                password_hash = generate_password_hash(password)
                
                # Create new user object
                new_user = User(
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    role=role,
                    plant_id=plant_id if plant_id else None,
                    plant_type=plant_type
                )
                
                # Add to database
                db.session.add(new_user)
                db.session.commit()
                
                flash('User added successfully', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding user: {str(e)}', 'danger')
            
        elif action == 'edit':
            # Get form data
            user_id = request.form.get('user_id')
            email = request.form.get('email')
            role = request.form.get('role')
            plant_id = request.form.get('plant_id')
            plant_type = request.form.get('plant_type')
            new_password = request.form.get('new_password')
            
            # Get the user
            user = User.query.get(user_id)
            if not user:
                flash('User not found', 'danger')
                return redirect(url_for('manage_users'))
            
            # Update user data
            try:
                user.email = email
                user.role = role
                user.plant_id = plant_id if plant_id else None
                user.plant_type = plant_type
                
                # Update password if provided
                if new_password:
                    user.password_hash = generate_password_hash(new_password)
                
                db.session.commit()
                flash('User updated successfully', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating user: {str(e)}', 'danger')
            
        elif action == 'delete':
            user_id = request.form.get('user_id')
            
            # Cannot delete yourself
            if int(user_id) == current_user.id:
                flash('You cannot delete your own account', 'danger')
                return redirect(url_for('manage_users'))
            
            # Get the user
            user = User.query.get(user_id)
            if not user:
                flash('User not found', 'danger')
                return redirect(url_for('manage_users'))
            
            # Delete the user
            try:
                db.session.delete(user)
                db.session.commit()
                flash('User deleted successfully', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error deleting user: {str(e)}', 'danger')
        
        return redirect(url_for('manage_users'))
    
    # Get all users
    users = User.query.all()
    
    # Get all plants for the plant selection dropdown
    plants = Plant.query.all()
    
    return render_template('manage_users.html', users=users, plants=plants)

@app.route('/solar_recommendation', methods=['GET'])
@login_required
def solar_recommendation():
    """Route for solar recommendation page with detailed analysis"""
    # Get the plant associated with the user
    plant = None
    if current_user.plant_id:
        plant = Plant.query.get(current_user.plant_id)
    
    # Ensure user has permission to view solar recommendations
    if current_user.plant_type != 'solar' and current_user.role != 'admin':
        flash('You do not have permission to view solar recommendations', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get today's date and calculate future date
    today = datetime.utcnow().date()
    future_date = today + timedelta(days=5)
    
    # Get the time period from the request (default to 'upcoming')
    time_period = request.args.get('time_period', 'upcoming')
    
    # Get daily solar predictions filtered by time period
    query = DailySolarPrediction.query.filter(
        DailySolarPrediction.plant_id == current_user.plant_id
    )
    
    if time_period == 'past':
        # Past data: all dates before today
        query = query.filter(DailySolarPrediction.date < today)
    elif time_period == 'today':
        # Today's data only
        query = query.filter(DailySolarPrediction.date == today)
    else:  # 'upcoming' is default
        # Future data: today and up to 5 days in the future
        query = query.filter(
            DailySolarPrediction.date >= today,
            DailySolarPrediction.date <= future_date
        )
    
    # Get the filtered data ordered by date
    daily_solar_data = query.order_by(DailySolarPrediction.date).all()
    
    # Filter for below threshold predictions
    below_threshold_data = []
    for prediction in daily_solar_data:
        if prediction.recommendation_status or (
            prediction.total_predicted_generation and 
            plant and 
            plant.threshold_value and 
            prediction.total_predicted_generation < plant.threshold_value
        ):
            # Calculate energy deficit
            energy_deficit = 0
            if prediction.total_predicted_generation and plant and plant.threshold_value:
                energy_deficit = max(0, plant.threshold_value - prediction.total_predicted_generation)
                
            below_threshold_data.append({
                'date': prediction.date.strftime('%Y-%m-%d'),  # Convert date to string for JSON
                'predicted_generation': prediction.total_predicted_generation,
                'threshold': plant.threshold_value if plant else 0,
                'deficit': energy_deficit
            })
    
    # Calculate total energy deficit
    total_deficit = sum(item['deficit'] for item in below_threshold_data)
    
    # Calculate coal required
    # Using the formula: 1 kg of coal produces approximately 2.46 kWh of electricity
    coal_efficiency = 2.46  # kWh per kg of coal
    coal_required = total_deficit / coal_efficiency if coal_efficiency > 0 else 0
    
    return render_template('solar_recommendation.html', 
                          plant=plant,
                          below_threshold_data=below_threshold_data,
                          total_deficit=total_deficit,
                          coal_required=coal_required,
                          today=today,
                          future_date=future_date,
                          time_period=time_period)

@app.route('/wind_recommendation', methods=['GET'])
@login_required
def wind_recommendation():
    """Route for wind recommendation page with detailed analysis"""
    # Get the plant associated with the user
    plant = None
    if current_user.plant_id:
        plant = Plant.query.get(current_user.plant_id)
    
    # Ensure user has permission to view wind recommendations
    if current_user.plant_type != 'wind' and current_user.role != 'admin':
        flash('You do not have permission to view wind recommendations', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get today's date
    today = datetime.utcnow().date()
    # Calculate future date (today + 5 days)
    future_date = today + timedelta(days=5)
    
    # Get the time period from the request (default to 'upcoming')
    time_period = request.args.get('time_period', 'upcoming')
    
    # Get daily wind predictions filtered by time period
    query = DailyWindPrediction.query.filter(
        DailyWindPrediction.plant_id == current_user.plant_id
    )
    
    if time_period == 'past':
        # Past data: all dates before today
        query = query.filter(DailyWindPrediction.date < today)
    elif time_period == 'today':
        # Today's data only
        query = query.filter(DailyWindPrediction.date == today)
    else:  # 'upcoming' is default
        # Future data: today and up to 5 days in the future
        query = query.filter(
            DailyWindPrediction.date >= today,
            DailyWindPrediction.date <= future_date
        )
    
    # Get the filtered data ordered by date
    daily_wind_data = query.order_by(DailyWindPrediction.date).all()
    
    # Filter for below threshold predictions
    below_threshold_data = []
    for prediction in daily_wind_data:
        if prediction.recommendation_status or (
            prediction.total_predicted_generation and 
            plant and 
            plant.threshold_value and 
            prediction.total_predicted_generation < plant.threshold_value
        ):
            # Calculate energy deficit
            energy_deficit = 0
            if prediction.total_predicted_generation and plant and plant.threshold_value:
                energy_deficit = max(0, plant.threshold_value - prediction.total_predicted_generation)
                
            below_threshold_data.append({
                'date': prediction.date.strftime('%Y-%m-%d'),  # Format as string for JSON
                'predicted_generation': prediction.total_predicted_generation,
                'threshold': plant.threshold_value if plant else 0,
                'deficit': energy_deficit
            })
    
    # Calculate total energy deficit
    total_deficit = sum(item['deficit'] for item in below_threshold_data)
    
    # Calculate coal required
    # Using the formula: 1 kg of coal produces approximately 2.46 kWh of electricity
    coal_efficiency = 2.46  # kWh per kg of coal
    coal_required = total_deficit / coal_efficiency if coal_efficiency > 0 else 0
    
    return render_template('wind_recommendation.html', 
                          plant=plant,
                          below_threshold_data=below_threshold_data,
                          total_deficit=total_deficit,
                          coal_required=coal_required,
                          today=today,
                          future_date=future_date,
                          time_period=time_period)

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