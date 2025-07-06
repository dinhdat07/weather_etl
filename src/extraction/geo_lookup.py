from time import sleep
import pandas as pd
import os


import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from config.api_config import APIConfig
from src.extraction.api_clients.weather_client import WeatherClient


class GeoLookup:
    def __init__(self, cities_input: str = "data/raw/cities.csv", geo_output: str = "data/raw/geo_data.csv"):
        self.cities_input = cities_input
        self.geo_output = geo_output
    
    def _load_existing(self):
        if not os.path.exists(self.geo_output):
            return set()
        df = pd.read_csv(self.geo_output)
        return set(zip(df["city"], df["country"]))

    def _save(self, records):
        df = pd.DataFrame(records)
        mode = "a" if os.path.exists(self.geo_output) else "w"
        header = not os.path.exists(self.geo_output)
        df.to_csv(self.geo_output, mode=mode, header=header, index=False, encoding="utf-8")
    
    def run(self):
        try:
            df = pd.read_csv(self.cities_input)
            assert {"city", "country"}.issubset(df.columns)
        except Exception as e:
            print(f"[GeoLookup] Error reading input: {e}")
            return
        
        existing = self._load_existing()
        new_records = []

        for _, row in df.iterrows():
            city, country = row['city'], row['country']
            if (city, country) in existing:
                print(f"[GeoLookup] Skipping {city},{country}")
                continue
            geo = WeatherClient.geocoding(city, country)
            if not geo or len(geo) == 0:
                print(f"[GeoLookup] No data for {city},{country}")
                continue
            item = geo[0]
            new_records.append({
                "city": city,
                "country": country,
                "lat": item.get("lat"),
                "lon": item.get("lon"),
                "vi_name": item.get("local_names", {}).get("vi")
            })
            sleep(APIConfig.RATE_LIMIT_DELAY)

        if new_records:
            self._save(new_records)
            print(f"[GeoLookup] Added {len(new_records)} new cities.")
        else:
            print("[GeoLookup] No new data.")


