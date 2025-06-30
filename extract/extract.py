from time import sleep
from typing import Callable, Dict, List, Optional
import dotenv
import os
import csv
import pandas as pd
import requests
from datetime import datetime
import json

dotenv.load_dotenv()
api_key = os.getenv("OPENWEATHER_API_KEY")
cities_input_path = "raw/cities.csv"
geo_data_path = 'raw/geo_data.csv'

def curr_weather_api_url(lat: float, lon: float):
    return f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"

def forcast_5d3h_api_url(lat: float, lon: float):
    return f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}"

def air_pollution_api_url(lat: float, lon: float):
    return f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"

def geocoding_api_url(city: str, country: str):
    return f"https://api.openweathermap.org/geo/1.0/direct?q={city},{country}&limit=1&appid={api_key}"


def geo_lookup():
    try:
        df = pd.read_csv(cities_input_path, encoding='utf-8')
        if not {'city', 'country'}.issubset(df.columns):
            raise ValueError("Input CSV must contain 'city' and 'country' columns.")
    except Exception as e:
        print(f"[ERROR] Failed to read input file: {str(e)}")
        return

    
    # output data
    coor_data: List[Dict[str, Optional[str]]] = []
    existing_cities = set()
    is_geo_exist = not os.path.exists(geo_data_path)

    # load existing data to avoid duplicates
    if is_geo_exist:
        existing_df = pd.read_csv(geo_data_path, encoding='utf-8')
        existing_cities = set(zip(existing_df['city'], existing_df['country']))

        
    for row in df.itertuples():
        city = row.city, country = row.country

        # skip if already processed
        if (city, country) in existing_cities:
            print(f"Skipping {city}, {country} (already exists in output).")
            continue

        url = f"{geocoding_api_url}?q={city},{country}&limit=1&appid={api_key}"
        print(f"Fetching geo data for {city}, {country}...")

        try: 
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if not data == 0:
                print(f"[ERROR] No data found for {city}, {country}")
                continue

            first_result = data[0]
            lat, lon = first_result.get("lat"), first_result.get("lon")
            vi_name = first_result.get("local_names", {}).get("vi")

            if lat is None or lon is None:
                print(f"[WARNING] Missing lat/lon for {city}, {country}.")
                continue

            print(f"Found geo data for {city}, {country}: lat={lat}, lon={lon}")
            coor_data.append({'city': city, 
                         'country': country, 
                         'lat': lat, 
                         'lon': lon, 
                         'vi_name': vi_name})
        
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Request failed for {city}, {country}: {str(e)}")
        except (KeyError, IndexError, ValueError) as e:
            print(f"[ERROR] Invalid API response for {city}, {country}: {str(e)}")
        
        sleep(1) # respect rate limit
    

    if coor_data:
        output_df = pd.DataFrame(coor_data)
        print(f"Writing geo data to {geo_data_path}...")
        output_df.to_csv(geo_data_path, mode='a', header= not is_geo_exist, index=False, encoding='utf-8')
        print(f"Saved {len(coor_data)} new records to {geo_data_path}")
    else:
        print("No new geodata fetched.")

            

def fetch_weather_info(
    api_func: Callable[[float, float], str],
    output_filename: str,
    output_dir: str = "raw",
) -> Optional[str]:
    
    try:
        df =  pd.read_csv(geo_data_path, encoding='utf-8')
        if not {'city', 'lat', 'lon'}.issubset(df.columns):
            raise ValueError("CSV must contain 'city', 'lat', 'lon' columns.")
    except Exception as e:
        print(f"[ERROR] Failed to read {geo_data_path}: {str(e)}")
        return None
    
    weather_info = []
    for row in df.itertuples():
        city, lat, lon = row.city, row.lat, row.lon
        url = api_func(lat, lon)

        try: 
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("cod") != 200:
                print(f"[Error] API error for {city} (lat={lat}, lon={lon}): {data.get('message', 'Unknown error')}")
                continue

            weather_info.append({
                    "city": city,
                    "lat": lat,
                    "lon": lon,
                    "data": data
                })
            print(f"Fetched data for {city}")
            
        except requests.exceptions.RequestException as e:
            print(f"[Error] Request failed for {city} (lat={lat}, lon={lon}): {str(e)}")
        except json.JSONDecodeError:
            print(f"[Error] Invalid JSON response for {city} (lat={lat}, lon={lon})")
        
        sleep(1)  # respect rate limit
    
    if not weather_info:
        print("No weather data fetched for {output_filename}.")
        return None
    

    
    try:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M")
        output_path = f"{output_dir}/{output_filename}_{timestamp}.json"

        with open(output_path, mode='+w', encoding='utf-8') as f:
            json.dump(weather_info, f, ensure_ascii=False, indent=4)
        
        print(f"Saved {len(weather_info)} records to {output_path}")

    except Exception as e:
        print(f"[ERROR] Failed to save file: {str(e)}")
        return None



