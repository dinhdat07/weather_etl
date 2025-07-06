import os
from typing import Any, Dict, List, Optional
from .base_transformer import BaseTransformer

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.processing.utils.time_utils import convert_timestamp_str_offset
from src.processing.utils.file_utils import load_timezone_mapping

class AirQualityTransformer(BaseTransformer):
    def __init__(self, timezone_csv_path: str):
        super().__init__()
        self.timezone_mapping = load_timezone_mapping(timezone_csv_path)
    
    def transform(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.logger.info(f"Transforming {len(raw_data)} air quality records")
        return [self._transform_record(row) for row in raw_data]
    
    def _transform_record(self, row: Dict) -> Dict:
        base_info = self._transform_common_fields(row)
        aqi_data = self._extract_aqi_data(row)
        
        return {
            **base_info,
            **aqi_data,
            **self._extract_time_data(
                timestamp=aqi_data.get('timestamp'),
                city=base_info['city'],
                lat=base_info['lat'],
                lon=base_info['lon']
            )
        }
    
    def _extract_aqi_data(self, row: Dict) -> Dict:
        """Extract all AQI related metrics"""
        aqi_entry = row.get("data", {}).get("list", [{}])[0]
        components = aqi_entry.get("components", {})
        
        return {
            "aqi": aqi_entry.get("main", {}).get("aqi"),
            "co": components.get("co"),
            "no": components.get("no"),
            "no2": components.get("no2"),
            "o3": components.get("o3"),
            "so2": components.get("so2"),
            "pm2_5": components.get("pm2_5"),
            "pm10": components.get("pm10"),
            "nh3": components.get("nh3"),
            "timestamp": aqi_entry.get("dt")
        }
    
    def _extract_time_data(self, 
                         timestamp: Optional[int],
                         city: str,
                         lat: float,
                         lon: float) -> Dict:
        if not timestamp:
            return {'time': None}
        
        tz_key = (city.lower(), lat, lon)
        tz_str = self.timezone_mapping.get(tz_key, 'UTC')
        
        try:
            return {
                'time': convert_timestamp_str_offset(timestamp, tz_str)
            }
        except Exception as e:
            self.logger.warning(
                f"Timezone conversion failed for {city} ({tz_str}): {str(e)}. "
                "Falling back to UTC"
            )
            return {
                'time': convert_timestamp_str_offset(timestamp, 'UTC+0')
            }