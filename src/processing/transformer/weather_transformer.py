import os
from typing import Any, Dict, List

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from src.processing.transformer.base_transformer import BaseTransformer
from src.processing.utils.unit_conversion import (
    kelvin_to_celsius,
    ms_to_kmh,
    meters_to_km
)
from src.processing.utils.time_utils import convert_timestamp

class WeatherTransformer(BaseTransformer):
    def transform(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.logger.info(f"Transforming {len(raw_data)} weather records")
        return [self._transform_record(row) for row in raw_data]
    
    def _transform_record(self, row: Dict) -> Dict:
        base_info = self._transform_common_fields(row)
        data = row.get('data', {})

        
        return {
            **base_info,
            **self._extract_weather_data(data),
            **self._extract_time_data(data),
        }
    
    def _extract_weather_data(self, data: Dict) -> Dict:
        main = data.get('main', {})
        wind = data.get('wind', {})
        rain = data.get('rain', {})
        weather = data.get('weather', [{}])[0] if data.get('weather') else {}
        
        return {
            'temperature': kelvin_to_celsius(main.get('temp')),
            'feels_like': kelvin_to_celsius(main.get('feels_like')),
            'weather_main': weather.get('main'),
            'weather_description': weather.get('description'),
            'humidity': main.get('humidity'),
            'clouds': data.get('clouds', {}).get('all'),
            'pressure': main.get('pressure'),
            'wind_speed': ms_to_kmh(wind.get('speed')),
            'wind_deg': wind.get('deg'),
            'visibility': meters_to_km(data.get('visibility')),
            'rain_1h': rain.get('1h', 0),

        }
    
    def _extract_time_data(self, data: Dict) -> Dict:
        return {
            'timestamp': data.get('dt'),
            'time': convert_timestamp(
                timestamp=data.get('dt'),
                tz_offset=data.get('timezone', 0)
            )
        }
        
    


