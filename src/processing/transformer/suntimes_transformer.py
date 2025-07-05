from typing import Any, Dict, List
from datetime import date, datetime, timedelta, timezone
from .base_transformer import BaseTransformer
from ..utils.time_utils import convert_timestamp

class SunTimesTransformer(BaseTransformer):
    def transform(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.logger.info(f"Transforming {len(raw_data)} sun times records")
        return [self._transform_record(row) for row in raw_data]
    
    def _transform_record(self, row: Dict) -> Dict:
        base_info = self._transform_common_fields(row)
        data = row.get('data', {})
        sys_data = data.get('sys', {})
        
        return {
            **base_info,
            **self._extract_date_info(sys_data, data.get('timezone', 0))
            **self._extract_sun_times(sys_data),
        }
    
    def _extract_sun_times(self, sys_data: Dict) -> Dict:
        sunrise_ts = sys_data.get('sunrise')
        sunset_ts = sys_data.get('sunset')
        
        return {
            'sunrise': convert_timestamp(sunrise_ts, sys_data.get('timezone', 0)),
            'sunset': convert_timestamp(sunset_ts, sys_data.get('timezone', 0)),
            'sunrise_stamp': sunrise_ts,
            'sunset_stamp': sunset_ts,
        }
    
    def _extract_date_info(self, sys_data: Dict, tz_offset: int) -> Dict:
        ts = sys_data.get('sunrise') or sys_data.get('sunset')
        if not ts:
            return {'date': None}
        
        dt = datetime.fromtimestamp(ts, timezone(timedelta(seconds=tz_offset)))
        return {'date': dt.date().isoformat()}

