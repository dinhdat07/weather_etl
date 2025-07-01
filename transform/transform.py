from datetime import datetime
import json
import logging
import os
from typing import List, Dict, Any

# Constants
DEFAULT_COUNTRY = 'VN'
UNKNOWN_CITY = 'Unknown'

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> List[Dict[str, Any]]:
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
            logger.info(f"Loaded {len(data)} records from {filepath}")
            return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load {filepath}: {str(e)}")
        raise

def _validate_coordinates(lat: float, lon: float) -> None:
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise ValueError(f"Invalid coordinates: lat={lat}, lon={lon}")
    
def save_json_file(data: List[Dict[str, Any]], filepath: str) -> None:
    with open(filepath, 'w+', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(data)} records to {filepath}")

def _transform_common_fields(row: Dict) -> Dict:
    city = row.get('city', UNKNOWN_CITY)
    lat = row.get('lat')
    lon = row.get('lon')
    country = row.get('country', DEFAULT_COUNTRY)
    
    if lat is not None and lon is not None:
        _validate_coordinates(lat, lon)
    
    return {
        'city': city,
        'lat': lat,
        'lon': lon,
        'country': country
    }

def transform_weather_data(raw_data: List[Dict[str, any]]) -> List[Dict[str, any]]:
    logger.info(f"Transforming weather data, {len(raw_data)} records")
    transformed_data = []
    for row in raw_data:
        base_info = _transform_common_fields(row)
        data = row.get('data', {})

        # extract fields with safe defaults
        data = row.get('data', {})
        weather = data.get('weather', [{}])[0] if data.get('weather') else {}
        main = data.get('main', {})
        wind = data.get('wind', {})
        rain = data.get('rain', {})


        # timestamp conversion
        timestamp = data.get('dt')
        time = datetime.fromtimestamp(timestamp).isoformat() if timestamp else None

        record = {
            **base_info,
            'temperature': main.get('temp'),
            'feels_like': main.get('feels_like'),
            'weather_main': weather.get('main'),
            'weather_description': weather.get('description'),
            'humidity': main.get('humidity'),
            'clouds': data.get('clouds', {}).get('all'),
            'pressure': main.get('pressure'),
            'wind_speed': wind.get('speed'),
            'wind_deg': wind.get('deg'),
            'visibility': data.get('visibility'),
            'rain_1h': rain.get('1h'),
            'timestamp': timestamp,
            'time': time  
        }
        transformed_data.append(record)

    logger.info(f"Transformed weather data: {len(transformed_data)} records")
    return transformed_data

def transform_forecast_data(raw_data: List[Dict[str, any]]) -> List[Dict[str, any]]:
    logger.info(f"Transforming forecast data, {len(raw_data)} records")
    transformed_data = []
    for row in raw_data:
        base_info = _transform_common_fields(row)
        data = row.get('data', {})
        list = data.get('list', [])

        for item in list:

            # extract fields with safe defaults
            weather = item.get('weather', [{}])[0] if item.get('weather') else {}
            main = item.get('main', {})
            wind = item.get('wind', {})
            rain = item.get('rain', {})

            # timestamp conversion
            timestamp = item.get('dt')
            time = datetime.fromtimestamp(timestamp).isoformat() if timestamp else None

            record = {
                **base_info,

                'temperature': main.get('temp'),
                'feels_like': main.get('feels_like'),
                'weather_main': weather.get('main'),
                'weather_description': weather.get('description'),
                'humidity': item.get('humidity'),
                'clouds': item.get('clouds', {}).get('all'),
                'pop': item.get('pop'),
                'pressure': main.get('pressure'),
                'wind_speed': wind.get('speed'),
                'wind_deg': wind.get('deg'),
                'visibility': item.get('visibility'),
                'rain_3h': rain.get('3h'),
                'timestamp': timestamp,
                'time': time  
            }
            transformed_data.append(record)

    logger.info(f"Transformed forecast data: {len(transformed_data)} records")
    return transformed_data

def transform_air_quality(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    logger.info(f"Transforming air quality data, {len(raw_data)} records")
    transformed_data = []
    
    for row in raw_data:
        # extract location data
        base_info = _transform_common_fields(row)
        
        
        # extract air quality data
        aqi_data = row.get("data", {}).get("list", [{}])[0]  
        components = aqi_data.get("components", {})
    
        timestamp = aqi_data.get("dt")
        time_iso = datetime.fromtimestamp(timestamp).isoformat() if timestamp else None
        
        # transformed record
        record = {
            **base_info,

            "aqi": aqi_data.get("main", {}).get("aqi"),  
            "co": components.get("co"),  
            "no": components.get("no"),  
            "no2": components.get("no2"),  
            "o3": components.get("o3"),  
            "so2": components.get("so2"),  
            "pm2_5": components.get("pm2_5"),  # PM2.5
            "pm10": components.get("pm10"),  # PM10
            "nh3": components.get("nh3"),  
            "timestamp": timestamp, 
            "time": time_iso  
        }
        
        transformed_data.append(record)
    logger.info(f"Transformed air quality data: {len(transformed_data)} records")
    return transformed_data


def main():
    try:
        logger.info("Starting data transformation pipeline...")
        processed_dir = "processed"
        os.makedirs(processed_dir, exist_ok=True)
        
        # weather data
        weather_file = "raw/current_weather_2025-07-01T17-40.json"
        weather_raw = load_json_file(weather_file)
        weather_transformed = transform_weather_data(weather_raw)
        weather_output = os.path.join(processed_dir, "current_weather_transformed.json")
        save_json_file(weather_transformed, weather_output)
        
        # forecast data
        forecast_file = "raw/forecast_5d3h_2025-07-01T17-40.json"
        forecast_raw = load_json_file(forecast_file)
        forecast_transformed = transform_forecast_data(forecast_raw)
        forecast_output = os.path.join(processed_dir, "forecast_transformed.json")
        save_json_file(forecast_transformed, forecast_output)
        
        # air quality data
        air_quality_file = "raw/air_pollution_2025-07-01T17-39.json"
        air_quality_raw = load_json_file(air_quality_file)
        air_quality_transformed = transform_air_quality(air_quality_raw)
        air_quality_output = os.path.join(processed_dir, "air_quality_transformed.json")
        save_json_file(air_quality_transformed, air_quality_output)
        
        logger.info("Data transformation pipeline completed successfully.")
        
    except Exception as e:
        logger.exception(f"Pipeline failed with error: {str(e)}")

if __name__ == "__main__":
    main()