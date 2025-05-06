# AI-Powered Renewable Energy Forecasting System

A comprehensive dashboard system for solar and wind energy forecasting, featuring user-specific dashboards based on plant type and customized features for different user roles.

## Setup Instructions

### Prerequisites
- Python 3.9+
- MySQL via XAMPP
- Web browser

### Database Setup with XAMPP
1. Install XAMPP from https://www.apachefriends.org/ if not already installed
2. Open XAMPP Control Panel
3. Start the MySQL service
4. The application will automatically create the database when you run setup.py

### Installation

1. Clone the repository:
```
git clone <repository-url>
cd <repository-folder>
```

2. Create and activate a virtual environment:
```
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On macOS/Linux
```

3. Run the setup script:
```
python setup.py
```
This will:
- Check MySQL connection via XAMPP
- Create the database if it doesn't exist
- Install required Python packages

4. Start the application:
```
python app.py
```
This will create all necessary database tables.

5. Access the application:
Open your web browser and navigate to `http://127.0.0.1:5000`

6. Register your first user, which will automatically be given admin privileges.

## System Features

- **User-Specific Dashboards**:
  - Solar plant users: Detailed solar generation metrics
  - Wind plant users: Wind-specific performance data
  - Administrators: Complete overview of all plants with tabbed interface

- **Plant Management**:
  - Add, edit, and delete plants
  - View plant details and performance metrics

- **Weather Integration**:
  - Real-time weather data affecting generation
  - Visualization of weather conditions

- **Performance Monitoring**:
  - Daily and hourly forecasts
  - Historical data comparison
  - Threshold alerts

## Database Structure

The system uses MySQL via XAMPP with the following tables (all created automatically):
- `users`: User account information
- `plants`: Plant details and configuration
- `hourly_solar_predictions`: Hourly solar generation forecasts
- `hourly_wind_predictions`: Hourly wind generation forecasts
- `daily_solar_predictions`: Aggregated daily solar generation data
- `daily_wind_predictions`: Aggregated daily wind generation data

## Project Overview

This system provides a centralized AI forecasting platform designed for a company's wind and solar power plants. It enables stakeholders to monitor and plan energy generation by leveraging machine learning models trained on hourly weather data.

## Key Features

- Real-time weather data integration
- AI-powered energy generation forecasting
- Interactive dashboard with charts for visualizing predictions
- Hourly and daily generation predictions
- Threshold-based recommendations
- Secure admin authentication

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript, Chart.js
- **Backend**: Python (Flask)
- **ML Libraries**: scikit-learn, pandas, numpy
- **Database**: SQLite (for MVP), MySQL (for production)
- **Weather API**: OpenWeatherMap or Tomorrow.io

## Project Structure

```
├── app.py                     # Flask app entry point
│
├── models/                    # Trained ML models
│   ├── solar_model.pkl
│   ├── wind_model.pkl
│
├── static/                    # Static assets
│   ├── css/
│   ├── js/
│
├── templates/                 # HTML pages (Views)
│   ├── home.html
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│
├── ml_pipeline/               # ML logic
│   ├── fetch_weather.py       # Fetch hourly data via API
│   ├── predict_hourly.py      # Predicts hour-wise
│   ├── aggregate_daily.py     # Sum up hourly to daily
│
├── database/
│   ├── db_connection.py
│   ├── create_tables.sql
```

## System Flow

1. Admin registers a plant location with threshold value
2. Admin logs in daily to view dashboard
3. System fetches 5-day hourly weather forecast
4. ML models predict energy generation (hour-wise)
5. System aggregates hourly values to compute day-wise generation
6. Data is stored in database (hourly and daily tables)
7. System generates recommendations if predicted generation is below threshold
8. Dashboard displays real-time predictions and past generation data with charts

## License

This project is licensed under the MIT License - see the LICENSE file for details. 