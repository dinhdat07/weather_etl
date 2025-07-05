from typing import Dict

def get_timezone_from_offset(offset_seconds: int) -> str:
    if not offset_seconds:
        return "UTC"
    offset_hours = offset_seconds / 3600
    return f"UTC{'+' if offset_hours >=0 else ''}{int(offset_hours)}"

def get_timezone(weather_data: dict) -> str:
    if 'timezone' in weather_data:
        return get_timezone_from_offset(weather_data['timezone'])
    return "UTC"