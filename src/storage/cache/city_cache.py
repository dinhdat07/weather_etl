from typing import Dict, Tuple, List

class CityCache:
    def __init__(self, conn):
        self.conn = conn
        self.cache = self._load_cities()
    
    def get_city_id(self, city_name: str, country: str, lat: float, lon: float) -> int:
        key = (city_name.lower(), country.lower())
        if key not in self.cache:
            raise ValueError(f"City not found in cache: {city_name}, {country}")
            
        for cached_lat, cached_lon, city_id in self.cache[key]:
            if self._coordinates_match(lat, lon, cached_lat, cached_lon):
                return city_id
        raise ValueError(f"No matching coordinates for {city_name}")

    def _load_cities(self) -> Dict[Tuple[str, str], List[Tuple[float, float, int]]]:
        cache = {}
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT city_id, city_name, country, latitude, longitude 
                FROM cities
            """)
            for row in cursor:
                key = (row[1].lower(), row[2].lower())
                cache.setdefault(key, []).append((float(row[3]), float(row[4]), row[0]))
        return cache

    @staticmethod
    def _coordinates_match(lat1: float, lon1: float, lat2: float, lon2: float, 
                          tolerance: float = 0.001) -> bool:
        return abs(lat1 - lat2) < tolerance and abs(lon1 - lon2) < tolerance