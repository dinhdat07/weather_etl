import io
import os
from time import sleep
import pandas as pd
import sys

from utils.gcs_utils import (
    check_blob_exists,
    download_blob_as_string,
    download_blob_to_file,
    upload_blob_from_file,
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from config.api_config import APIConfig
from src.extraction.api_clients.weather_client import WeatherClient


class GeoLookup:
    def __init__(self, bucket_name: str, cities_blob: str, geo_blob: str, local_geo_path: str = "data/raw/geo_data.csv"):
        self.bucket_name = bucket_name
        self.cities_blob = cities_blob
        self.geo_blob = geo_blob
        self.local_geo_path = local_geo_path

    def _load_existing(self):
        if not check_blob_exists(self.bucket_name, self.geo_blob):
            return set(), pd.DataFrame(columns=["city", "country", "lat", "lon", "vi_name"])

        if not os.path.exists(self.local_geo_path):
            print(f"[GeoLookup] Downloading geo data from GCS to {self.local_geo_path}")
            download_blob_to_file(self.bucket_name, self.geo_blob, self.local_geo_path)

        try:
            df = pd.read_csv(self.local_geo_path)
            return set(zip(df["city"], df["country"])), df
        except Exception as e:
            print(f"[GeoLookup] Error reading local geo_data.csv: {e}")
            return set(), pd.DataFrame(columns=["city", "country", "lat", "lon", "vi_name"])

    def _save(self, df_full: pd.DataFrame):
        try:
            os.makedirs(os.path.dirname(self.local_geo_path), exist_ok=True)
            df_full.to_csv(self.local_geo_path, index=False, encoding="utf-8")
            print(f"[GeoLookup] Saved to local: {self.local_geo_path}")

            upload_blob_from_file(self.bucket_name, self.geo_blob, self.local_geo_path)
            print(f"[GeoLookup] Uploaded updated geo data to GCS")
        except Exception as e:
            print(f"[GeoLookup] Failed to save/upload geo_data.csv: {e}")

    def run(self):
        try:
            csv_str = download_blob_as_string(self.bucket_name, self.cities_blob)
            df = pd.read_csv(io.StringIO(csv_str))
            assert {"city", "country"}.issubset(df.columns)
        except Exception as e:
            print(f"[GeoLookup] Error reading input cities list: {e}")
            return

        existing_set, existing_df = self._load_existing()
        new_records = []

        for _, row in df.iterrows():
            city, country = row['city'], row['country']
            if (city, country) in existing_set:
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
            df_new = pd.DataFrame(new_records)
            df_full = pd.concat([existing_df, df_new], ignore_index=True)
            self._save(df_full)
            print(f"[GeoLookup] Added {len(new_records)} new cities.")
        else:
            print("[GeoLookup] No new data.")
