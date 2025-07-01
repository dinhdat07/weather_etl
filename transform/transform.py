from datetime import datetime
import json
from typing import List, Dict, Any

filename = 'current_weather_2025-06-30T16-41.json'

def load_json_file(filepath: str) -> List[Dict[str, Any]]:
    with open(filepath, 'r+', encoding='utf-8') as file:
        return json.load(file)
    
def save_json_file(data: List[Dict[str, Any]], filepath: str) -> None:
    with open(filepath, 'w+', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def transform_weather_data(raw_data: List[Dict[str, any]]) -> List[Dict[str, any]]:
    transformed_data = []
    for row in raw_data:
        city = row.get('city', 'Unknown')
        data = row.get('data', {})

        # extract fields with safe defaults
        weather = data.get('weather', [{}])[0] if data.get('weather') else {}
        wind = data.get('wind', {})
        rain = data.get('rain', {})

        # timestamp conversion
        timestamp = data.get('dt')
        time = datetime.fromtimestamp(timestamp).isoformat() if timestamp else None

        record = {
            'city': city,
            'temperature': data.get('temperature'),
            'feels_like': data.get('feels_like'),
            'weather_main': weather.get('main'),
            'weather_description': weather.get('description'),
            'humidity': data.get('humidity'),
            'clouds': data.get('clouds', {}).get('all'),
            'pop': data.get('pop'),
            'pressure': data.get('pressure'),
            'wind_speed': wind.get('speed'),
            'wind_deg': wind.get('deg'),
            'visibility': data.get('visibility'),
            'rain_1h': rain.get('1h'),
            'timestamp': timestamp,
            'time': time  
        }
        transformed_data.append(record)
    return transformed_data

def transform_forecast_data(raw_data: List[Dict[str, any]]) -> List[Dict[str, any]]:
    transformed_data = []
    for row in raw_data:
        city = row.get('city', 'Unknown')
        data = row.get('data', {})
        list = data.get('list', [])

        for item in list:

            # extract fields with safe defaults
            weather = item.get('weather', [{}])[0] if item.get('weather') else {}
            wind = item.get('wind', {})
            rain = item.get('rain', {})

            # timestamp conversion
            timestamp = item.get('dt')
            time = datetime.fromtimestamp(timestamp).isoformat() if timestamp else None

            record = {
                'city': city,
                'temperature': item.get('temperature'),
                'feels_like': item.get('feels_like'),
                'weather_main': weather.get('main'),
                'weather_description': weather.get('description'),
                'humidity': item.get('humidity'),
                'clouds': item.get('clouds', {}).get('all'),
                'pop': item.get('pop'),
                'pressure': item.get('pressure'),
                'wind_speed': wind.get('speed'),
                'wind_deg': wind.get('deg'),
                'visibility': item.get('visibility'),
                'rain_3h': rain.get('3h'),
                'timestamp': timestamp,
                'time': time  
            }
            transformed_data.append(record)
        return transformed_data

def transform_air_quality(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    transformed_data = []
    
    for row in raw_data:
        
        # extract location data
        city = row.get("city", "Unknown")
        
        # extract air quality data
        aqi_data = row.get("data", {}).get("list", [{}])[0]  # Lấy phần tử đầu tiên trong 'list'
        components = aqi_data.get("components", {})
    
        timestamp = aqi_data.get("dt")
        time_iso = datetime.fromtimestamp(timestamp).isoformat() if timestamp else None
        
        # transformed record
        record = {
            "city": city,
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
    
    return transformed_data

