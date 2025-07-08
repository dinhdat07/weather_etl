from time import sleep
from datetime import datetime
import os
import json
from typing import Dict, List, Optional
import pandas as pd


import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from config.api_config import APIConfig
from src.extraction.api_clients.weather_client import WeatherClient
from src.extraction.utils import APIUtils

class WeatherFetcher:
    def __init__(self, geo_data: str = "data/raw/geo_data.csv", output_dir: str = "data/raw"):
        self.geo_data = geo_data
        self.output_dir = output_dir
    
    def _read_geo_data(self) -> Optional[pd.DataFrame]:
        try:
            df = pd.read_csv(self.geo_data)
            required_cols = {"city", "lat", "lon", "country"}
            if not required_cols.issubset(df.columns):
                raise ValueError(f"Missing columns in geo data: {required_cols}")
            return df
        except Exception as e:
            print(f"[WeatherFetcher] Error reading geo file: {e}")
            return None

    def _save_results(self, data: List[Dict], filename: str) -> None:
        path = os.path.join(self.output_dir, filename)
        os.makedirs(self.output_dir, exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[WeatherFetcher] Saved {len(data)} records to {path}")
        except Exception as e:
            print(f"[WeatherFetcher] Failed to save file: {e}")

    def run(self, filename: str, fetch_type: str = "current"):
        df = self._read_geo_data()
        if df is None:
            return
        
        results = []
        for _, row in df.iterrows():
            lat, lon = row["lat"], row["lon"]
            city, country = row["city"], row["country"]

            if fetch_type == "current":
                data = WeatherClient.current_weather(lat, lon)
            elif fetch_type == "forecast":
                data = WeatherClient.forecast(lat, lon)
            elif fetch_type == "air_pollution":
                data = WeatherClient.air_pollution(lat, lon)
            else:
                print(f"[WeatherFetcher] Unknown fetch_type: {fetch_type}")
                return

            if data and APIUtils.is_api_success(data):
                results.append({
                    "city": city,
                    "country": country,
                    "lat": lat,
                    "lon": lon,
                    "data": data
                })
                print(f"[WeatherFetcher] fetched {city}")
            else:
                print(f"[WeatherFetcher] failed {city}")
            sleep(APIConfig.RATE_LIMIT_DELAY)
        
        if results:
            self._save_results(results, filename)
        else:
            print("[WeatherFetcher] no data fetched.")
        
