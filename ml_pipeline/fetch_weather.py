import requests
import pandas as pd
from datetime import datetime
import re
import math

def parse_coordinates(location_string):
    """
    Parse coordinates from a string format like "28.579202°N 77.631433°E"
    Returns (latitude, longitude) as floats
    """
    # Default coordinates if parsing fails
    default_lat, default_lng = 23.276474, 77.460590
    
    if not location_string:
        return default_lat, default_lng
    
    try:
        # Extract numbers and directions
        pattern = r"(\d+\.\d+)°([NS])\s+(\d+\.\d+)°([EW])"
        match = re.search(pattern, location_string)
        
        if match:
            lat_value = float(match.group(1))
            lat_dir = match.group(2)
            lng_value = float(match.group(3))
            lng_dir = match.group(4)
            
            # Adjust sign based on direction
            latitude = lat_value if lat_dir == 'N' else -lat_value
            longitude = lng_value if lng_dir == 'E' else -lng_value
            
            return latitude, longitude
        
        # Try simple comma-separated format "lat,lng"
        comma_pattern = r"(-?\d+\.\d+),\s*(-?\d+\.\d+)"
        comma_match = re.search(comma_pattern, location_string)
        
        if comma_match:
            return float(comma_match.group(1)), float(comma_match.group(2))
            
        return default_lat, default_lng
    except Exception as e:
        print(f"Error parsing coordinates: {e}")
        return default_lat, default_lng

def fetch_weather_data(location=None, latitude=23.276474, longitude=77.460590, forecast_days=5):
    """
    Fetch hourly weather forecast for a given location using Open-Meteo API.
    
    Args:
        location (str, optional): Location string in format like "28.579202°N 77.631433°E"
        latitude (float, optional): Latitude coordinate
        longitude (float, optional): Longitude coordinate
        forecast_days (int, optional): Number of days to forecast
        
    Returns:
        DataFrame: Cleaned and structured hourly weather data
    """
    # If location is provided, extract coordinates
    if location:
        latitude, longitude = parse_coordinates(location)
        
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}"
        "&hourly=temperature_2m,relative_humidity_2m,pressure_msl,"
        "direct_radiation,windspeed_10m,sunshine_duration,winddirection_10m,"
        "windgusts_10m,precipitation"
        f"&forecast_days={forecast_days}&timezone=auto"
    )

    response = requests.get(url)

    if response.status_code != 200:
        raise Exception("Failed to fetch weather data")

    data = response.json()
    hourly = data['hourly']

    # Create DataFrame
    df = pd.DataFrame({
        'time': pd.to_datetime(hourly['time']),
        'WindSpeed': hourly['windspeed_10m'],
        'Sunshine': [s / 60 for s in hourly['sunshine_duration']],  # convert seconds to hours
        'AirPressure': hourly['pressure_msl'],
        'Radiation': hourly['direct_radiation'],
        'AirTemperature': hourly['temperature_2m'],
        'RelativeAirHumidity': hourly['relative_humidity_2m'],
        'WindDirection': hourly['winddirection_10m'],
        'WindGust': hourly['windgusts_10m'],
        'Precipitation': hourly['precipitation']
    })

    # Extract month and hour from datetime
    df['Month'] = df['time'].dt.month
    df['Hour'] = df['time'].dt.hour
    df['Date'] = df['time'].dt.date  # for daily aggregation

    return df

def fetch_wind_weather_data(location=None, latitude=23.276474, longitude=77.460590, forecast_days=5):
    """
    Fetch hourly weather forecast for wind power prediction.
    
    Args:
        location (str, optional): Location string in format like "28.579202°N 77.631433°E"
        latitude (float, optional): Latitude coordinate
        longitude (float, optional): Longitude coordinate
        forecast_days (int, optional): Number of days to forecast
        
    Returns:
        DataFrame: Weather data formatted for wind power prediction
    """
    # Get general weather data
    df = fetch_weather_data(location, latitude, longitude, forecast_days)
    
    # Calculate wind direction deviation (simplified approach)
    # Calculating the difference between direction and 180 degrees (optimal wind direction)
    # This is a simplified approach and can be adjusted based on actual wind turbine specifications
    df['wind_dir_dev'] = abs((df['WindDirection'] - 180) % 360)
    if df['wind_dir_dev'].max() > 180:
        df['wind_dir_dev'] = df['wind_dir_dev'].apply(lambda x: min(x, 360-x))
    
    # Map features to match the expected input for the wind model
    wind_df = pd.DataFrame({
        'time': df['time'],
        'wind_speed': df['WindSpeed'],
        'temperature': df['AirTemperature'],
        'RH': df['RelativeAirHumidity'],
        'pressure': df['AirPressure'],
        'gust': df['WindGust'],
        'wind_dir_dev': df['wind_dir_dev'],
        'precipitation': df['Precipitation'],
        'Month': df['Month'],
        'Hour': df['Hour'],
        'Date': df['Date']
    })
    
    return wind_df

if __name__ == "__main__":
    # Test the function
    data = fetch_weather_data()
    print(f"Fetched {len(data)} hourly weather records")
    print("Sample data:", data.head())
    
    # Test wind weather data
    wind_data = fetch_wind_weather_data()
    print(f"Fetched {len(wind_data)} hourly wind weather records")
    print("Wind data sample:", wind_data.head()) 