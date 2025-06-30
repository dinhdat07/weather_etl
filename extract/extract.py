import dotenv
import os
import csv
import pandas as pd
import requests

dotenv.load_dotenv()
api_key = os.getenv("OPENWEATHER_API_KEY")
cities_input_path = "extract/cities.csv"

def curr_weather_api_url(lat: float, lon: float):
    return f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"

def forcast_5d3h_api_url(lat: float, lon: float):
    return f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}"

def air_pollution_api_url(lat: float, lon: float):
    return f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"

def geocoding_api_url(city: str, country: str):
    return f"https://api.openweathermap.org/geo/1.0/direct?q={city},{country}&limit=1&appid={api_key}"


def geo_lookup():
    df = pd.read_csv(cities_input_path, encoding='utf-8')
    
    coor_data = [['city', 'country', 'lat', 'lon', 'vi_name']]
    for row in df.itertuples():
        city = row.city
        country = row.country
        url = geocoding_api_url(city, country)

        print(f"Fetching geo data for {city}, {country} to {url}")
        response = requests.get(url)
        data = response.json()
        if len(data) == 0:
            print(f"[ERROR] No data found for {city}, {country}")
            continue;

        for item in data:
            if item.get("lat") and item.get("lon"):
                lat = item["lat"]
                lon = item["lon"]
                vi_name = item.get("local_names", {}).get("vi")
                coor_city = {'city': city, 'country': country, 'lat': lat, 'lon': lon, 'vi_name': vi_name}
                print(f"Found geo data for {city}, {country}: lat={lat}, lon={lon}")
                coor_data.append(coor_city)
                break
            else:
                print(f"[ERROR] No lat/lon found for {city}, {country}, checking next result...")
        
    file_path = 'extract/geo_data.csv'
    write_header = not os.path.exists(file_path)
    output_df = pd.DataFrame(coor_data[1:], columns=coor_data[0])
    print(f"Writing geo data to {file_path}...")
    output_df.to_csv(file_path, mode='a', header=write_header, index=False, encoding='utf-8')
            
geo_lookup()