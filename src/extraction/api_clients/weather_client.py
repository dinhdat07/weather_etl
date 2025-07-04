import requests
from requests.adapters import HTTPAdapter, Retry
from dotenv import load_dotenv
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from configs.api_config import APIConfig

load_dotenv()


class WeatherClient:
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    @classmethod
    def geocoding(cls, city: str, country: str):
        url = f"{APIConfig.GEO_URL}/direct?q={city},{country}&limit=1&appid={APIConfig.API_KEY}"
        return cls._request(url)

    @classmethod
    def current_weather(cls, lat: float, lon: float):
        url = f"{APIConfig.BASE_URL}/weather?lat={lat}&lon={lon}&appid={APIConfig.API_KEY}"
        return cls._request(url)

    @classmethod
    def forecast(cls, lat: float, lon: float):
        url = f"{APIConfig.BASE_URL}/forecast?lat={lat}&lon={lon}&appid={APIConfig.API_KEY}"
        return cls._request(url)

    @classmethod
    def air_pollution(cls, lat: float, lon: float):
        url = f"{APIConfig.BASE_URL}/air_pollution?lat={lat}&lon={lon}&appid={APIConfig.API_KEY}"
        return cls._request(url)

    @classmethod
    def _request(cls, url: str):
        try:
            resp = cls.session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[WeatherClient] request failed: {e}")
            return None
