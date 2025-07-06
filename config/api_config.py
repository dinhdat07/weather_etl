# configs/api_config.py
import os
from dotenv import load_dotenv

load_dotenv()

class APIConfig:
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    GEO_URL = "https://api.openweathermap.org/geo/1.0"
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    RATE_LIMIT_DELAY = 1  # seconds