# AI-Powered Renewable Energy Forecasting System - Copilot Instructions

## Project Overview

This is a Flask-based renewable energy forecasting dashboard for solar and wind power plants. The system provides role-based access where users see dashboards specific to their plant type (solar/wind/both), while admins manage all plants with a tabbed interface.

## Architecture & Core Components

### Database Design (Azure SQL Server)
- **Plants** → **Users** (one-to-many via `plant_id` FK)
- **Plants** → **Hourly/Daily Predictions** (one-to-many via `plant_id` FK)
- Plant types: `'solar'`, `'wind'`, or `'both'`
- Predictions stored separately: `hourly_solar_predictions`, `hourly_wind_predictions`, `daily_solar_predictions`, `daily_wind_predictions`

### ML Pipeline Flow (`ml_pipeline/`)
1. **fetch_weather.py**: Fetches 5-day hourly forecasts from Open-Meteo API, parses coordinates from strings like "28.579202°N 77.631433°E"
2. **predict_hourly.py**: Loads scikit-learn models from `models/` directory, applies domain-specific logic (e.g., solar generation = 0 when sunshine=0 AND radiation<0)
3. **aggregate_daily.py**: Sums hourly predictions to daily totals, generates threshold-based recommendations

### Key Patterns & Conventions

#### Route Structure
- **Web routes**: `/`, `/login`, `/solar_dashboard`, `/wind_dashboard`, `/admin_dashboard`
- **API routes**: `/api/*` for AJAX endpoints (all return JSON with `{'success': bool, 'message': str, ...}`)
- **Authentication**: `@login_required` + `@admin_required` decorators

#### Data Flow Example
```python
# API refresh pattern used throughout
@app.route('/api/refresh-solar-data')
@login_required
def refresh_solar_data():
    # 1. Get user's plant
    plant = Plant.query.get(current_user.plant_id)
    # 2. Fetch weather → predict → aggregate → save
    weather_data = fetch_weather_data(plant.location)
    hourly_predictions = predict_hourly_generation(weather_data, "solar", plant.id)
    daily_predictions = aggregate_daily_generation(hourly_predictions, plant.threshold_value)
    save_predictions_to_db(hourly_predictions, daily_predictions, plant.id, db, "solar")
```

#### Frontend Integration
- **Chart.js** for visualizations in `static/js/*_dashboard.js`
- AJAX pattern: User actions trigger `/api/*` calls, then re-render charts
- Date selectors control hourly chart data: `fetchSolarHourlyData(date, plantId)`

## Development Workflow

### Setup Commands (Windows/Azure SQL Server)
```bash
# Initial setup
python setup.py  # Checks Azure SQL config, installs requirements
python app.py    # Creates tables via SQLAlchemy, starts Flask dev server

# Database reset
python init_db.py    # Check Azure SQL configuration
python init_admin.py # Create default admin user
```

### Testing ML Pipeline
```python
# Test weather fetch
from ml_pipeline.fetch_weather import fetch_weather_data
weather_df = fetch_weather_data("28.579202°N 77.631433°E")

# Test predictions
from ml_pipeline.predict_hourly import predict_hourly_generation
predictions = predict_hourly_generation(weather_df, "solar", plant_id=1)
```

### Database Session Management
- Uses Flask-SQLAlchemy ORM with models in `app.py`
- Raw pyodbc connections in ML pipeline for bulk operations with `?` parameterized queries
- Environment variables in `.env`: `AZURE_SQL_SERVER`, `AZURE_SQL_USERNAME`, `AZURE_SQL_PASSWORD`, `AZURE_SQL_DATABASE`
- Date filtering uses `date_filter(column, date_value)` helper for SQL Server compatibility

## Critical Integration Points

### Model Loading Pattern
Models are joblib bundles containing both scaler and trained model:
```python
model_bundle = joblib.load('models/solar_power_rf_model.pkl')
scaler = model_bundle['scaler']
model = model_bundle['model']
```

### Weather API Integration
- Uses Open-Meteo (free, no API key required)
- Coordinate parsing handles multiple formats: "lat°N lng°E" or "lat,lng"
- Default fallback coordinates: `23.276474, 77.460590`

### Database Session Management
- Uses Flask-SQLAlchemy ORM with models in `app.py`
- Raw MySQL connections via `get_db_connection()` for setup scripts
- Environment variables in `.env`: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`

## Plant-Specific Logic

### User Dashboard Routing
```python
# Users see different dashboards based on plant_type
if current_user.plant_type == 'solar':
    return redirect(url_for('solar_dashboard'))
elif current_user.plant_type == 'wind':
    return redirect(url_for('wind_dashboard'))
# Admins see unified admin_dashboard with tabs
```

### Threshold Recommendations
- Each plant has `threshold_value` for minimum daily generation
- System generates recommendations when predicted < threshold
- Stored in daily prediction tables as `recommendation_status` + `recommendation_message`

## File Organization Notes

- **Static assets**: `static/css/style.css`, `static/js/{solar,wind,admin}_dashboard.js`
- **Templates**: Jinja2 with custom filters (`divide`, `strftime`, `now`)
- **Models**: Pre-trained sklearn models in `models/` (solar: .pkl, wind: .pkl.gz)
- **Database scripts**: `database/create_tables.sql` with proper FK constraints and indexes

## Common Gotchas

1. **Solar prediction edge case**: Always check `if sunshine=0 AND radiation<0 then generation=0`
2. **Date handling**: Use `date_filter()` helper function for SQLAlchemy date filtering, not `func.date()`
3. **SQL Server syntax**: Use `?` for parameters (not `%s`), `GETDATE()` (not `NOW()`), `CAST(column AS DATE)` for date extraction
4. **Plant association**: Users must have `plant_id` set; admins can access all plants
5. **Environment setup**: Requires Azure SQL Server credentials in `.env` file
6. **Model file paths**: Use `os.path.join(os.path.dirname(...), 'models', 'filename')` for relative paths
