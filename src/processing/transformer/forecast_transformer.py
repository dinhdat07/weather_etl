from typing import Any, Dict, List
from .base_transformer import BaseTransformer
from ..utils.time_utils import convert_timestamp
from ..utils.unit_conversion import (
    kelvin_to_celsius,
    ms_to_kmh,
    meters_to_km
)
from ..utils.time_utils import convert_timestamp

class ForecastTransformer(BaseTransformer):
    def transform(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.logger.info(f"Transforming {len(raw_data)} forecast records")
        transformed = []
        for row in raw_data:
            base_info = self._transform_common_fields(row)
            data = row.get('data', {})
            list = data.get('list', [])
            tz_offset = data.get('city', {}).get('timezone', 0) 

            for item in list:
                transformed.append(self._transform_forecast_item(base_info, item, tz_offset))
        return transformed
    
    def _transform_forecast_item(self, base_info: Dict, item: Dict, tz_offset: int) -> Dict: 
        return {
            **base_info,
            **self._extract_weather_data(item),
            **self._extract_time_data(item, tz_offset)
        }
    
    def _extract_weather_data(self, item: Dict) -> Dict:
        weather = item.get('weather', [{}])[0] if item.get('weather') else {}
        main = item.get('main', {})
        wind = item.get('wind', {})
        rain = item.get('rain', {})
        pop_raw = item.get('pop')
        pop_percent = round(pop_raw * 100) if pop_raw is not None else None
        
        return {
            'temperature': kelvin_to_celsius(main.get('temp')),
            'feels_like': kelvin_to_celsius(main.get('feels_like')),
            'weather_main': weather.get('main'),
            'weather_description': weather.get('description'),
            'humidity': main.get('humidity'),
            'clouds': item.get('clouds', {}).get('all'),
            'pop': pop_percent,
            'pressure': main.get('pressure'),
            'wind_speed': ms_to_kmh(wind.get('speed')),
            'wind_deg': wind.get('deg'),
            'visibility': meters_to_km(item.get('visibility')),
            'rain_3h': rain.get('3h', 0),
        }
    
    def _extract_time_data(self, data: Dict, tz_offset: int) -> Dict:
        return {
            'timestamp': data.get('dt'),
            'time': convert_timestamp(
                timestamp=data.get('dt'),
                tz_offset=tz_offset
            )
        }
            
            
            
