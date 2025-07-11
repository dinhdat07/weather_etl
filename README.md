# ⛅ Weather ETL Pipeline

## Overview
This project implements a **production-grade ETL pipeline** using **Apache Airflow**, **PostgreSQL**, and **Docker** to collect, process, and store weather data from the OpenWeatherMap API.

<p align="center">
  <img width="300" height="134" alt="image" src="https://github.com/user-attachments/assets/420c03f4-2233-4f2e-b099-f0cea3e5a562" />
</p>

The pipeline is designed with modular and scalable architecture, enabling reliable scheduling, transformation, and loading of data such as:
- **Current weather**
- **Weather forecasts (5 days/ 3 hours)**
- **Air quality**
- **Sunrise/Sunset times**

Geo-coordinates are mapped with timezone metadata and cached efficiently to avoid unnecessary API calls.

## Features
- Runs automatically every **3 hours** using cron
- Geo lookup with **timezone enrichment**
- Data transformation with custom logic
- Data stored in **normalized PostgreSQL** tables
- Auto-sync city records with UPSERT logic
- Forecast retention cleaning (every run)
- Modular DAG task design with retry + timeout handling


## Tech Stack
| Component     | Tool                          |
|--------------|-------------------------------|
| Scheduler     | Apache Airflow                |
| Data Storage  | PostgreSQL                    |
| Containerization | Docker + Docker Compose   |
| Programming   | Python 3.12                   |
| APIs          | OpenWeatherMap                |
| Data Helpers  | Pandas, JSON, timezonefinder  |


## DAG Details
The main DAG is defined in `weather_etl_pipeline.py` using the Airflow `@dag` decorator. It orchestrates a complex ETL flow as follows:

### ➤ `create_tables`
Initializes required PostgreSQL tables (`cities`, `weather_data`, `forecast`, `air_pollution`, `suntimes`) if missing. Designed to be idempotent.

### ➤ `geo_lookup`
Reads `cities.csv` and performs geo-lookup (latitude/longitude) using external APIs. Saves enriched file to `geo_data.csv`.

### ➤ `extract_weather_data`
Pulls real-time weather info (current, forecast, air pollution) from OpenWeatherMap for each city. Output is stored in timestamped JSON files.

### ➤ `add_timezones`
Uses `timezonefinder` to enrich `geo_data.csv` into `geo_data_with_tz.csv` by adding timezone field for each city.

### ➤ `sync_cities`
Reads `geo_data_with_tz.csv` and syncs city metadata into the `cities` table using UPSERT logic to avoid duplication.

### ➤ Transform Tasks
These tasks run in **parallel**:
- `transform_current_weather`: Cleans and flattens current weather data
- `transform_forecast`: Normalizes multi-day forecast records
- `transform_air_quality`: Extracts pollutant info with timestamp & city context
- `transform_suntimes`: Extracts sunrise/sunset times (only runs at midnight window)

## DAG Flow (Logical View)
<img width="1665" height="942" alt="weather_data_pipeline_prod-graph" src="https://github.com/user-attachments/assets/c164357b-e6f4-4d7d-be60-985b7b6d57fa" />

## Docker Setup
```bash
git clone https://github.com/yourname/weather-etl.git
cd weather-etl
cp .env.example .env
# Set OpenWeatherMap API key, DATA_DIR, ENVIRONMENT, etc.
docker-compose up --build
```
Then visit the Airflow UI at: [http://localhost:8080](http://localhost:8080)
Below is an example screenshot of the Airflow UI managing the Weather ETL pipeline:

<img width="2832" height="1522" alt="image" src="https://github.com/user-attachments/assets/a4970ad4-189d-4236-ad9c-6c00d89b2a44" />

## Airflow Variables & Connections
Set the following from Airflow UI → Admin → Variables:
- `DATA_DIR`: `/opt/airflow/data`
- `ENVIRONMENT`: `dev`

Connections:
- `weather_db`: PostgreSQL connection to `weather_db`

## Sample Data
Although the pipeline dynamically writes data to folders based on the ENVIRONMENT Airflow variable (e.g., data/raw/dev/ or data/processed/prod/), this repository includes a sample data/ folder with representative files for reference:
- data/raw/: Contains example input files such as cities.csv, geo_data.csv, geo_data_with_tz.csv and weather JSONs (current_*.json, forecast_*.json, etc.)
- data/processed/: Contains transformed outputs like current_transformed_*.json, forecast_transformed_*.json, air_quality_transformed_*.json, suntimes_transformed_*.json

These files help visualize the pipeline's input and output formats without needing to run the full ETL process.

City data is enriched with country, timezone, and Vietnamese name, then cached to geo_data_with_tz.csv. This file is used to upsert city metadata into the cities table in PostgreSQL.


Database Schema
This project creates and populates five main normalized tables in PostgreSQL:
- cities: Location metadata (name, country, lat/lon, timezone, Vietnamese name)
- weather_data: Current weather conditions
- forecast: Short-term weather forecasts (e.g., 3-hour intervals)
- air_pollution: Air quality measurements (PM2.5, CO, etc.)
- suntimes: Sunrise and sunset time records
The schema is created automatically during the first DAG run via the create_tables task.

You can view the full table structures via pgAdmin or reference the image below:
<img width="2229" height="2561" alt="Untitled" src="https://github.com/user-attachments/assets/87c52902-7785-4bd3-8b24-2d308d0bd564" />


## Notes
- **Idempotent design**: avoids re-inserting duplicate city/weather rows
- **Data integrity**: uses `ON CONFLICT DO UPDATE` for city syncing
- **Timezone awareness**: each row includes localized time

## 🧑‍💻 Author
**Đạt Đình**  
2nd Year @ UET, Data Engineering Track  
Email: dinhdatnguyen0710@example.com

## 📜 License
MIT License — Free to use and modify

---
Feel free to fork ⭐, contribute 🛠️, or give feedback 💬!




