from typing import Optional

def kelvin_to_celsius(temp_k: Optional[float]) -> Optional[float]:
    return round(temp_k - 273.15, 1) if temp_k is not None else None

def ms_to_kmh(speed_ms: Optional[float]) -> Optional[float]:
    return round(speed_ms * 3.6, 1) if speed_ms is not None else None

def meters_to_km(visibility_m: Optional[int]) -> Optional[float]:
    return round(visibility_m/1000, 1) if visibility_m else None