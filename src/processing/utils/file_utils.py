from ast import Dict
import csv


def load_timezone_mapping(csv_path: str) -> Dict[str, str]:
    timezone_mapping = {}
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row['city'].lower(), float(row['lat']), float(row['lon']))
            timezone_mapping[key] = row['timezone']
    return timezone_mapping
