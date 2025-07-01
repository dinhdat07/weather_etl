# File: src/database_helpers.py
from typing import Optional

def get_city_id(cursor, city_name: str, country: str, lat: float, lon: float) -> Optional[int]:
    cursor.execute("""
        SELECT city_id FROM cities
        WHERE city_name = %s AND country = %s
        AND ABS(latitude - %s) < 0.0001 AND ABS(longitude - %s) < 0.0001;
    """, (city_name, country, lat, lon))
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"City not found: {city_name} (lat={lat}, lon={lon})")
    return result[0]
