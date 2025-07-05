import os
import shutil
import csv
import json
from typing import Optional, List, Dict

def get_timezone_from_offset(offset_seconds: int) -> str:
    if not offset_seconds:
        return "UTC"
    offset_hours = offset_seconds / 3600
    return f"UTC{'+' if offset_hours >=0 else ''}{int(offset_hours)}"

def get_timezone(weather_data: dict) -> str:
    if 'timezone' in weather_data:
        return get_timezone_from_offset(weather_data['timezone'])
    return "UTC"


def add_timezones_to_csv(
    csv_path: str,
    json_path: str,
    output_path: Optional[str] = None,
    overwrite: bool = False,
    backup: bool = True,
    coord_threshold: float = 1.0
) -> None:

    # validate paths
    if output_path is None and not overwrite:
        raise ValueError("Must specify output_path or enable overwrite=True")
    output_path = output_path or csv_path
    
    # create backup
    if overwrite and backup and os.path.exists(csv_path):
        backup_path = f"{csv_path}.bak"
        shutil.copy2(csv_path, backup_path)
        print(f"[INFO] Created backup at: {backup_path}")

    # process data
    rows, weather_data = _load_data_files(csv_path, json_path)
    processed_rows = _process_timezones(rows, weather_data, coord_threshold)
    _write_output(output_path, processed_rows)

def _load_data_files(csv_path: str, json_path: str) -> tuple:
    with open(csv_path, 'r', encoding='utf-8') as csv_file:
        rows = list(csv.DictReader(csv_file))
    with open(json_path, 'r', encoding='utf-8') as json_file:
        weather_data = json.load(json_file)
    return rows, weather_data

def _process_timezones(
    rows: List[Dict],
    weather_data: List[Dict],
    coord_threshold: float
) -> List[Dict]:
    matched = 0
    for row in rows:
        city_match = _find_city_match(row, weather_data, coord_threshold)
        row['timezone'] = get_timezone(city_match.get('data', {})) if city_match else 'UTC'
        matched += 1 if city_match else 0
    
    print(f"[INFO] Successfully matched {matched}/{len(rows)} cities")
    return rows

def _find_city_match(
    row: Dict,
    weather_data: List[Dict],
    threshold: float
) -> Optional[Dict]:
    for item in weather_data:
        if item.get('city', '').lower() != row.get('city', '').lower():
            continue
            
        if not all(k in item and k in row for k in ('lat', 'lon')):
            continue
            
        coord_diff = abs(float(item['lat']) - float(row['lat'])) + \
                     abs(float(item['lon']) - float(row['lon']))
    
        if coord_diff > threshold:
            print(f"[WARNING] Possible mismatch for {row.get('city', '')}: "
                  f"Coordinates differ by {coord_diff:.2f} degrees")
            continue        
        return item
    return None

def _write_output(output_path: str, rows: List[Dict]) -> None:
    with open(output_path, 'w', encoding='utf-8', newline='') as out_file:
        writer = csv.DictWriter(out_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"[SUCCESS] Updated timezones written to: {output_path}")