import requests
import pandas as pd
from datetime import datetime
import re

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
        "direct_radiation,windspeed_10m,sunshine_duration"
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
    })

    # Extract month and hour from datetime
    df['Month'] = df['time'].dt.month
    df['Hour'] = df['time'].dt.hour
    df['Date'] = df['time'].dt.date  # for daily aggregation

    return df

if __name__ == "__main__":
    # Test the function
    data = fetch_weather_data()
    print(f"Fetched {len(data)} hourly weather records")
    print("Sample data:", data.head()) 