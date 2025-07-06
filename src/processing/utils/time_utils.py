from datetime import datetime, timezone, timedelta
import re
from typing import Optional, Union

def convert_timestamp(
    timestamp: Optional[Union[int, float]],
    tz_offset: int = 0
) -> Optional[str]:
    
    if not timestamp:
        return None
    tz_info = timezone(timedelta(seconds=tz_offset))
    return datetime.fromtimestamp(timestamp, tz=tz_info).isoformat()

def convert_timestamp_str_offset(
    timestamp: Optional[Union[int, float]],
    tz_offset: str = "UTC+0"
) -> Optional[str]:
    
    if not timestamp:
        return None
    
    match = re.match(r"UTC([+-]\d+)", tz_offset)
    if not match:
        raise ValueError(f"Invalid timezone format: {tz_offset}")
    
    hours_offset = int(match.group(1))
    tz_info = timezone(timedelta(hours=hours_offset))
    return datetime.fromtimestamp(timestamp, tz=tz_info).isoformat()