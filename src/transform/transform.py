import csv
import logging
import os
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import json
from timezonefinder import TimezoneFinder
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers.json_helpers import load_json_file, save_json_file


# Constants
DEFAULT_COUNTRY = 'VN'
UNKNOWN_CITY = 'Unknown'

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _validate_coordinates(lat: float, lon: float) -> None:
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise ValueError(f"Invalid coordinates: lat={lat}, lon={lon}")
    

def get_timezone(weather_data: dict) -> str:
    if 'timezone' in weather_data:
        offset_hours = weather_data['timezone'] / 3600
        return f"UTC{'+' if offset_hours >=0 else ''}{int(offset_hours)}"
    
    return "UTC"


def add_timezones_to_csv(
    csv_path: str,
    json_path: str,
    output_path: Optional[str] = None,
    overwrite: bool = False,
    backup: bool = True
) -> None:
    

    # validate output path
    if output_path is None:
        if not overwrite:
            raise ValueError("Must specify output_path or enable overwrite=True")
        output_path = csv_path
    
    # create backup if needed
    if overwrite and backup and os.path.exists(csv_path):
        backup_path = f"{csv_path}.bak"
        shutil.copy2(csv_path, backup_path)
        print(f"[INFO] Created backup at: {backup_path}")

    # load data
    with open(csv_path, 'r', encoding='utf-8') as csv_file:
        rows = list(csv.DictReader(csv_file))
    
    with open(json_path, 'r', encoding='utf-8') as json_file:
        weather_data = json.load(json_file)

    # process rows with matching
    
    matched = 0
    for row in rows:
        city_match = None
        for item in weather_data:
            if item.get('city', '').lower() == row.get('city', '').lower():
                if 'lat' in item and 'lon' in item and 'lat' in row and 'lon' in row:
                    coord_diff = abs(float(item['lat']) - abs(float(row['lat']))) + \
                                 abs(float(item['lon']) - abs(float(row['lon'])))
                    if coord_diff > 1.0:  # threshold for coordinate mismatch
                        print(f"[WARNING] Possible mismatch for {row.get('city', '')}: "
                              f"Coordinates differ by {coord_diff:.2f} degrees")
                        continue
                city_match = item
                matched += 1
                break
        
        city_data = city_match.get('data', {})
        if not city_data:
            print(f"[WARNING] No weather data found for city: {row.get('city', '')}")
        
        row['timezone'] = get_timezone(city_data) if city_match else 'UTC'

    print(f"[INFO] Successfully matched {matched}/{len(rows)} cities")

    # write output
    with open(output_path, 'w', encoding='utf-8', newline='') as out_file:
        writer = csv.DictWriter(out_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"[SUCCESS] Updated timezones written to: {output_path}")

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


        # conversion
        kelvin_temp = main.get('temp')
        temp_c = round(kelvin_temp - 273.15, 1) if kelvin_temp is not None else None
            
        kelvin_feels = main.get('feels_like')
        feels_like_c = round(kelvin_feels - 273.15, 1) if kelvin_feels is not None else None
            
        wind_speed_kmh = round(wind.get('speed') * 3.6, 1) if wind.get('speed') is not None else None
        visibility_km = round(data.get('visibility')/1000, 1) if data.get('visibility') else None

        tz_offset = data.get('timezone', 0) 
        timestamp = data.get('dt')
        
        if timestamp:
            tz_info = timezone(timedelta(seconds=tz_offset))
            local_dt = datetime.fromtimestamp(timestamp, tz=tz_info)
            time_local = local_dt.isoformat()
        else:
            time_local = None
        
        record = {
            **base_info,
            'temperature': temp_c,
            'feels_like': feels_like_c,
            'weather_main': weather.get('main'),
            'weather_description': weather.get('description'),
            'humidity': main.get('humidity'),
            'clouds': data.get('clouds', {}).get('all'),
            'pressure': main.get('pressure'),
            'wind_speed': wind_speed_kmh,
            'wind_deg': wind.get('deg'),
            'visibility': visibility_km,
            'rain_1h': rain.get('1h', 0),
            'timestamp': timestamp,
            'time': time_local
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
        city_data = data.get('city', {})
        tz_offset = city_data.get('timezone', 0) 
        
        for item in list:

            # extract fields with safe defaults
            weather = item.get('weather', [{}])[0] if item.get('weather') else {}
            main = item.get('main', {})
            wind = item.get('wind', {})
            rain = item.get('rain', {})

            # timestamp conversion
            kelvin_temp = main.get('temp')
            temp_c = round(kelvin_temp - 273.15, 1) if kelvin_temp is not None else None
                
            kelvin_feels = main.get('feels_like')
            feels_like_c = round(kelvin_feels - 273.15, 1) if kelvin_feels is not None else None
            
            pop_raw = item.get('pop')
            pop_percent = round(pop_raw * 100) if pop_raw is not None else None
                
            wind_speed_kmh = round(wind.get('speed') * 3.6, 1) if wind.get('speed') is not None else None
            visibility_km = round(item.get('visibility')/1000, 1) if item.get('visibility') else None
            
            timestamp = item.get('dt')
            if timestamp:
                tz_info = timezone(timedelta(seconds=tz_offset))
                local_dt = datetime.fromtimestamp(timestamp, tz=tz_info)
                time_local = local_dt.isoformat()
            else:
                time_local = None
            

            record = {
                **base_info,

                'temperature': temp_c,
                'feels_like': feels_like_c,
                'weather_main': weather.get('main'),
                'weather_description': weather.get('description'),
                'humidity': main.get('humidity'),
                'clouds': item.get('clouds', {}).get('all'),
                'pop': pop_percent,
                'pressure': main.get('pressure'),
                'wind_speed': wind_speed_kmh,
                'wind_deg': wind.get('deg'),
                'visibility': visibility_km,
                'rain_3h': rain.get('3h', 0),
                'timestamp': timestamp,
                'time': time_local 
            }
            transformed_data.append(record)

    logger.info(f"Transformed forecast data: {len(transformed_data)} records")
    return transformed_data

def load_timezone_mapping(csv_path: str) -> Dict[str, str]:
    timezone_mapping = {}
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row['city'].lower(), float(row['lat']), float(row['lon']))
            timezone_mapping[key] = row['timezone']
    return timezone_mapping

def transform_air_quality(raw_data: List[Dict[str, Any]],
    timezone_csv_path: str) -> List[Dict[str, Any]]:

    timezone_mapping = load_timezone_mapping(timezone_csv_path)
    logger.info(f"Transforming air quality data, {len(raw_data)} records")
    transformed_data = []
    
    for row in raw_data:
        # extract location data
        base_info = _transform_common_fields(row)
        city = base_info['city'].lower()
        lat = base_info['lat']
        lon = base_info['lon']

        tz_key = (city, lat, lon)
        tz_str = timezone_mapping.get(tz_key, 'UTC') # default UTC
        
        
        # extract air quality data
        aqi_data = row.get("data", {}).get("list", [{}])[0]  
        components = aqi_data.get("components", {})
        timestamp = aqi_data.get("dt")

        local_time = None
        if timestamp:
            try:
                if tz_str.startswith('UTC'):
                    offset_hours = int(tz_str[3:]) if tz_str[3:] else 0
                    tz_info = timezone(timedelta(hours=offset_hours))
                
                local_time = datetime.fromtimestamp(timestamp, tz=tz_info).isoformat()
            except Exception as e:
                logger.warning(f"Failed to parse timezone {tz_str} for {city}: {str(e)}")
                local_time = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
        
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
            "time": local_time
        }
        
        transformed_data.append(record)
    logger.info(f"Transformed air quality data: {len(transformed_data)} records")
    return transformed_data

def transform_sun_times_data(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    logger.info(f"Transforming air quality data, {len(raw_data)} records")
    transformed_data = []
    
    for row in raw_data:
        base_info = _transform_common_fields(row)
        data = row.get('data', {})
        sys = data.get('sys', {})

        tz_offset = data.get('timezone', 0) 
        sunset_timestamp = sys.get('sunset')
        sunrise_timestamp = sys.get('sunrise')

        if sunset_timestamp:
            tz_info = timezone(timedelta(seconds=tz_offset))
            sunset_dt = datetime.fromtimestamp(sunset_timestamp, tz=tz_info)
            sunset_local = sunset_dt.isoformat()
        else:
            sunset_dt = None
            sunset_local = None

        if sunrise_timestamp:
            tz_info = timezone(timedelta(seconds=tz_offset))
            sunrise_dt = datetime.fromtimestamp(sunrise_timestamp, tz=tz_info)
            sunrise_local = sunrise_dt.isoformat()
        else:
            sunrise_dt = None
            sunrise_local = None

        if sunrise_dt:
            date_str = sunrise_dt.date().isoformat()
        elif sunset_dt:
            date_str = sunset_dt.date().isoformat()
        else:
            date_str = None

        record = {
            **base_info,
            'date': date_str,
            'sunrise': sunrise_local,
            'sunset': sunset_local,
            'sunrise_stamp': sunrise_timestamp,
            'sunset_stamp': sunset_timestamp  
        }


        transformed_data.append(record)

    logger.info(f"Transformed sun times data: {len(transformed_data)} records")
    return transformed_data


def main():
    try:
        logger.info("Getting timezone data for transformation pipeline...")
        add_timezones_to_csv(
            csv_path='raw/geo_data.csv',
            json_path='raw/current_weather_2025-07-01T17-40.json',
            overwrite=True
        )

        logger.info("Starting data transformation pipeline...")
        processed_dir = "processed"
        os.makedirs(processed_dir, exist_ok=True)
        
        # weather data
        weather_file = "raw/current_weather_2025-07-01T17-40.json"
        weather_raw = load_json_file(weather_file)
        weather_transformed = transform_weather_data(weather_raw)
        weather_output = os.path.join(processed_dir, "current_weather_transformed.json")
        save_json_file(weather_transformed, weather_output)
        
        weather_file = "raw/current_weather_2025-07-01T17-40.json"
        weather_raw = load_json_file(weather_file)
        weather_transformed = transform_sun_times_data(weather_raw)
        weather_output = os.path.join(processed_dir, "sun_times_transformed.json")
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
        air_quality_transformed = transform_air_quality(air_quality_raw, "raw/geo_data.csv")
        air_quality_output = os.path.join(processed_dir, "air_quality_transformed.json")
        save_json_file(air_quality_transformed, air_quality_output)
        
        logger.info("Data transformation pipeline completed successfully.")
        
    except Exception as e:
        logger.exception(f"Pipeline failed with error: {str(e)}")


if __name__ == "__main__":
    main()