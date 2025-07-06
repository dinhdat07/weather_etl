from typing import Dict, Tuple
import csv


def load_timezone_mapping(csv_path: str) -> Dict[Tuple[str, float, float], str]:
    timezone_mapping = {}
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row['city'].lower(), float(row['lat']), float(row['lon']))
            timezone_mapping[key] = row['timezone']
    return timezone_mapping
