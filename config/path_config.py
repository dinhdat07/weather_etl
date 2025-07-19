from pathlib import Path
from typing import Dict
from airflow.models import Variable
import logging
from google.cloud import storage
import pandas as pd

logger = logging.getLogger("airflow.task")

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = Path(Variable.get("DATA_DIR", default_var="/opt/airflow/data"))
ENVIRONMENT = Variable.get("ENVIRONMENT", default_var="dev")

class PathConfig:
    def __init__(self):
        self.raw = DATA_DIR / "raw" / ENVIRONMENT
        self.processed = DATA_DIR / "processed" / ENVIRONMENT
        self.logs = DATA_DIR / "logs" / ENVIRONMENT
        self.gcs_prefix = f"{ENVIRONMENT}/data"
        
        # geo data paths
        self.cities_data = self.raw/ "cities.csv"
        self.geo_data = self.raw / "geo_data.csv"
        self.geo_data_with_tz = self.raw / "geo_data_with_tz.csv"
        
        # create directories if not exist
        for d in [self.raw_dir, self.processed_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    def get_weather_paths(self, timestamp: str) -> Dict[str, Path]:
        return {
            'current': self.raw / f"current_{timestamp}.json",
            'forecast': self.raw / f"forecast_{timestamp}.json",
            'air_pollution': self.raw / f"air_pollution_{timestamp}.json",
        }
    
    def get_transformed_paths(self, timestamp: str) -> Dict[str, Path]:
        return {
            'current': self.processed / f"current_transformed_{timestamp}.json",
            'forecast': self.processed / f"forecast_transformed_{timestamp}.json",
            'air_pollution': self.processed / f"air_quality_transformed_{timestamp}.json",
            'suntimes': self.processed / f"suntimes_transformed_{timestamp[:10]}.json",
        }