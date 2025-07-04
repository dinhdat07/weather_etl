# Weather Data Loader

A Python script for loading weather data into PostgreSQL database.

## Installation
```bash
pip install psycopg2-binary python-dotenv
```

## Usage

### 1. Single Record Insert
```bash
python load.py single-insert --table [TABLE_NAME] --input-file [FILE.json]
```
Example:
```bash
python load.py single-insert --table weather --input-file data/single_weather.json
```

### 2. Batch Insert
```bash
python load.py batch-insert --table [TABLE_NAME] --input-file [FILE.json] --batch-size [SIZE]
```
Example:
```bash
python load.py batch-insert --table forecast --input-file batch_forecasts.json --batch-size 2000
```

### 3. Maintenance Commands

#### Clean old forecasts:
```bash
python load.py maintenance --action clean_forecasts --retention-days [DAYS]
```
Example (keep 7 days):
```bash
python load.py maintenance --action clean_forecasts --retention-days 7
```

#### Database maintenance:
```bash
python load.py maintenance --action vacuum_analyze
```

## Available Tables
- `weather`
- `forecast` 
- `air_pollution`
- `suntimes`
```