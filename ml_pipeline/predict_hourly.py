import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

def predict_hourly_generation(weather_data, plant_type="solar", plant_id=1):
    """
    Predict hourly energy generation based on weather data
    
    Args:
        weather_data (DataFrame): DataFrame with hourly weather data
        plant_type (str): 'solar' or 'wind'
        plant_id (int): ID of the plant
    
    Returns:
        list: List of hourly predictions with timestamps and generation values
    """
    try:
        if plant_type == "solar":
            # Load model and scaler
            model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                'models', 'solar_power_rf_model.pkl')
            print(f"Loading model from: {model_path}")
            model_bundle = joblib.load(model_path)
            scaler = model_bundle['scaler']
            model = model_bundle['model']
            
            # Process the weather data
            df_weather = weather_data.copy()
            
            # Adjust radiation values as per the provided example
            df_weather['Radiation'] = df_weather['Radiation'] - np.median(df_weather['Radiation'])
            
            # Select feature columns in the same order used during training
            features = ['WindSpeed', 'Sunshine', 'AirPressure', 'Radiation',
                        'AirTemperature', 'RelativeAirHumidity', 'Month', 'Hour']
            X_features = df_weather[features]
            
            # Scale input features
            X_scaled = scaler.transform(X_features)
            
            # Predict
            df_weather['predicted_generation'] = model.predict(X_scaled)
            
            # Apply condition: if Sunshine is 0.0 and Radiation is negative, set production to 0.0
            df_weather.loc[(df_weather['Sunshine'] == 0.0) & (df_weather['Radiation'] < 0.0), 'predicted_generation'] = 0.0
            
            # Create list of hourly predictions
            hourly_predictions = []
            
            for _, row in df_weather.iterrows():
                # Create a dictionary with all weather data
                weather_data_dict = {
                    'WindSpeed': float(row['WindSpeed']),
                    'Sunshine': float(row['Sunshine']),
                    'AirPressure': float(row['AirPressure']),
                    'Radiation': float(row['Radiation']),
                    'AirTemperature': float(row['AirTemperature']),
                    'RelativeAirHumidity': float(row['RelativeAirHumidity'])
                }
                
                timestamp = row['time'].strftime('%Y-%m-%d %H:%M:%S')
                
                hourly_predictions.append({
                    'plant_id': plant_id,
                    'timestamp': timestamp,
                    'weather_data': json.dumps(weather_data_dict),
                    'predicted_generation': float(row['predicted_generation'])
                })
            
            return hourly_predictions
        
        elif plant_type == "wind":
            # Wind prediction logic will be added later
            # For now, return empty list
            return []
    except Exception as e:
        print(f"Error in predict_hourly_generation: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []

if __name__ == "__main__":
    # Test with sample weather data
    from fetch_weather import fetch_weather_data
    import pandas as pd
    import numpy as np
    
    # Get weather forecast data
    df_weather = fetch_weather_data()
    
    # Predict hourly generation
    hourly_predictions = predict_hourly_generation(df_weather, "solar", 1)
    
    # Show first few predictions
    print(f"Generated {len(hourly_predictions)} hourly predictions")
    for i in range(3):
        print(f"Hour {i+1}: {hourly_predictions[i]['timestamp']} - {hourly_predictions[i]['predicted_generation']} kW") 