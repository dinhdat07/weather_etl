# src/processing/utils/time_utils.py
from datetime import datetime, timezone, timedelta
from typing import Optional, Union

def convert_timestamp(
    timestamp: Optional[Union[int, float]],
    tz_offset: int = 0
) -> Optional[str]:
    
    if not timestamp:
        return None
    tz_info = timezone(timedelta(seconds=tz_offset))
    return datetime.fromtimestamp(timestamp, tz=tz_info).isoformat()
