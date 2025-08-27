from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd

def aggregate_daily_generation(hourly_predictions, threshold_value):
    """
    Aggregate hourly predictions into daily predictions and check threshold
    
    Args:
        hourly_predictions (list): List of hourly prediction dictionaries
        threshold_value (float): Threshold value for recommendations
    
    Returns:
        list: List of daily predictions with aggregated generation values
    """
    # Group predictions by date
    daily_data = defaultdict(float)
    
    for pred in hourly_predictions:
        timestamp = pred['timestamp']
        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        date_str = dt.strftime('%Y-%m-%d')
        
        # Sum up hourly generation for each day
        daily_data[date_str] += pred['predicted_generation']
    
    # Create list of daily predictions
    daily_predictions = []
    
    for date_str, total_generation in daily_data.items():
        # Check if prediction is below threshold
        below_threshold = total_generation < threshold_value
        
        daily_predictions.append({
            'date': date_str,
            'total_predicted_generation': round(total_generation, 2),
            'below_threshold': below_threshold
        })
    
    # Sort by date
    daily_predictions.sort(key=lambda x: x['date'])
    
    return daily_predictions

def save_predictions_to_db(hourly_predictions, daily_predictions, plant_id, db, plant_type="solar"):
    """
    Save hourly and daily predictions to the database
    
    Args:
        hourly_predictions (list): List of hourly prediction dictionaries
        daily_predictions (list): List of daily prediction dictionaries
        plant_id (int): ID of the plant
        db: SQLAlchemy database connection
        plant_type (str): 'solar' or 'wind'
    """
    print(f"==== Starting save_predictions_to_db - Plant ID: {plant_id}, Type: {plant_type} ====")
    print(f"Hourly predictions: {len(hourly_predictions)}, Daily predictions: {len(daily_predictions)}")
    
    # Import necessary modules without importing models directly
    import pyodbc
    import json
    from datetime import datetime
    import os
    
    try:
        # Connect directly to Azure SQL Server
        server = os.environ.get('AZURE_SQL_SERVER', 'localhost')
        database = os.environ.get('AZURE_SQL_DATABASE', 'renewable_energy')
        username = os.environ.get('AZURE_SQL_USERNAME', 'root')
        password = os.environ.get('AZURE_SQL_PASSWORD', '')
        
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
        )
        
        conn = pyodbc.connect(conn_str)
        
        if not conn:
            print("Error: Could not connect to the database")
            return
            
        cursor = conn.cursor()
        
        # Choose the appropriate table based on plant type
        if plant_type == "solar":
            hourly_table = "hourly_solar_predictions"
            daily_table = "daily_solar_predictions"
        else:  # wind
            hourly_table = "hourly_wind_predictions"
            daily_table = "daily_wind_predictions"
        
        updated_hourly = 0
        created_hourly = 0
        
        # Process hourly predictions
        for pred in hourly_predictions:
            timestamp = datetime.strptime(pred['timestamp'], '%Y-%m-%d %H:%M:%S')
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            print(f"Processing hourly prediction for: {timestamp_str}")
            
            # Check if record exists
            check_query = f"""
            SELECT id FROM {hourly_table} 
            WHERE plant_id = ? AND timestamp = ?
            """
            cursor.execute(check_query, (plant_id, timestamp_str))
            existing_record = cursor.fetchone()
            
            weather_data_json = pred['weather_data']
            predicted_gen = pred['predicted_generation']
            
            if existing_record:
                # Update existing record
                update_query = f"""
                UPDATE {hourly_table}
                SET weather_data = ?, predicted_generation = ?, created_at = GETDATE()
                WHERE plant_id = ? AND timestamp = ?
                """
                cursor.execute(update_query, (weather_data_json, predicted_gen, plant_id, timestamp_str))
                updated_hourly += 1
                print(f"Updated hourly prediction for timestamp: {timestamp_str}")
            else:
                # Insert new record
                insert_query = f"""
                INSERT INTO {hourly_table} (plant_id, timestamp, weather_data, predicted_generation, created_at)
                VALUES (?, ?, ?, ?, GETDATE())
                """
                cursor.execute(insert_query, (plant_id, timestamp_str, weather_data_json, predicted_gen))
                created_hourly += 1
                print(f"Created new hourly prediction for timestamp: {timestamp_str}")
        
        updated_daily = 0
        created_daily = 0
        
        # Process daily predictions
        for pred in daily_predictions:
            date_obj = datetime.strptime(pred['date'], '%Y-%m-%d').date()
            date_str = date_obj.strftime('%Y-%m-%d')
            print(f"Processing daily prediction for: {date_str}")
            
            # Check if record exists
            check_query = f"""
            SELECT id FROM {daily_table} 
            WHERE plant_id = ? AND date = ?
            """
            cursor.execute(check_query, (plant_id, date_str))
            existing_record = cursor.fetchone()
            
            pred_gen = pred['total_predicted_generation']
            is_below = 1 if pred['below_threshold'] else 0
            recommendation = "Energy generation below threshold" if pred['below_threshold'] else None
            
            if existing_record:
                # Update existing record
                update_query = f"""
                UPDATE {daily_table}
                SET total_predicted_generation = ?, recommendation_status = ?, recommendation_message = ?, created_at = GETDATE()
                WHERE plant_id = ? AND date = ?
                """
                cursor.execute(update_query, (pred_gen, is_below, recommendation, plant_id, date_str))
                updated_daily += 1
                print(f"Updated daily prediction for date: {date_str}")
            else:
                # Insert new record
                insert_query = f"""
                INSERT INTO {daily_table} (plant_id, date, total_predicted_generation, recommendation_status, recommendation_message, created_at)
                VALUES (?, ?, ?, ?, ?, GETDATE())
                """
                cursor.execute(insert_query, (plant_id, date_str, pred_gen, is_below, recommendation))
                created_daily += 1
                print(f"Created new daily prediction for date: {date_str}")
        
        # Commit changes and close connection
        conn.commit()
        print(f"Database updated successfully!")
        print(f"Hourly records: {updated_hourly} updated, {created_hourly} created")
        print(f"Daily records: {updated_daily} updated, {created_daily} created")
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"ERROR updating database: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    
    print(f"==== Completed save_predictions_to_db ====")

def filter_daylight_hours(hourly_predictions):
    """
    Filter predictions to only include daylight hours (7:00 to 20:00)
    
    Args:
        hourly_predictions (list): List of hourly prediction dictionaries
    
    Returns:
        list: Filtered list of hourly predictions
    """
    filtered_predictions = []
    
    for pred in hourly_predictions:
        timestamp = pred['timestamp']
        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        
        # Keep only hours between 7:00 and 20:00
        if 7 <= dt.hour <= 20:
            filtered_predictions.append(pred)
    
    return filtered_predictions

if __name__ == "__main__":
    # Test with sample hourly predictions
    from fetch_weather import fetch_weather_data
    from predict_hourly import predict_hourly_generation
    
    weather_data = fetch_weather_data()
    hourly_predictions = predict_hourly_generation(weather_data, "solar", 1)
    
    # Filter to daylight hours for solar predictions
    filtered_predictions = filter_daylight_hours(hourly_predictions)
    
    # Set a threshold of 1500 kWh per day
    threshold = 1500
    daily_predictions = aggregate_daily_generation(filtered_predictions, threshold)
    
    # Show daily predictions
    print(f"Aggregated to {len(daily_predictions)} daily predictions")
    for pred in daily_predictions:
        status = "BELOW THRESHOLD!" if pred['below_threshold'] else "OK"
        print(f"Date: {pred['date']} - Total: {pred['total_predicted_generation']} kWh - Status: {status}") 