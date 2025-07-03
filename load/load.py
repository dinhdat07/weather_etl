import json
import psycopg2 as pg
from psycopg2 import sql, errors
import os
from dotenv import load_dotenv
from helpers.database_helpers import get_city_id
from helpers.json_helpers import load_json_file, save_json_file

from psycopg2.extras import execute_batch

from load.table_config import TABLE_CONFIGS
from sql_query import AIR_POLLUTION_INSERT_SQL, FORECAST_UPSERT_SQL, SUNTIMES_INSERT_SQL, WEATHER_INSERT_SQL
load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

def get_db_connection() -> pg.extensions.connection:
    try:
        return pg.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
    except pg.Error as e:
        raise ConnectionError(f"Failed to connect to database: {e}")
    
def create_weather_table(conn: pg.extensions.connection):
    queries = [
        sql.SQL("""
        CREATE TABLE IF NOT EXISTS weather_data (
            weather_id SERIAL PRIMARY KEY,
            city_id INTEGER NOT NULL REFERENCES cities(city_id) ON DELETE CASCADE,
            
            city_name VARCHAR(100) NOT NULL,
            country VARCHAR(2) NOT NULL,
                
            temperature NUMERIC(4, 1),
            feels_like NUMERIC(4, 1),
            weather_main VARCHAR(50),
            weather_description VARCHAR(100),
            humidity INTEGER CHECK (humidity BETWEEN 0 AND 100 OR humidity IS NULL),
            
            clouds INTEGER CHECK (clouds BETWEEN 0 AND 100),
            pressure INTEGER,
            wind_speed NUMERIC(5, 1),
            wind_deg INTEGER CHECK (wind_deg BETWEEN 0 AND 360),
            
            visibility NUMERIC(5, 1),
            rain_1h NUMERIC(5, 2),
            
            timestamp BIGINT,
            time TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT fk_city FOREIGN KEY(city_id) REFERENCES cities(city_id),
            CONSTRAINT uniq_weather_reading UNIQUE(city_id, time)
        );
        """),
        sql.SQL("""
        CREATE INDEX IF NOT EXISTS idx_weather_city ON weather_data (city_id);
        """),
        sql.SQL("""
        CREATE INDEX IF NOT EXISTS idx_weather_time ON weather_data (time);
        """),
        sql.SQL("""
        CREATE INDEX IF NOT EXISTS idx_weather_main ON weather_data (weather_main);
        """)
    ]
    
    with conn.cursor() as cursor:
        for query in queries:
            try:
                cursor.execute(query)
            except errors.DuplicateTable:
                conn.rollback()
                continue
        conn.commit()

def create_forecast_table(conn: pg.extensions.connection):
    queries = [
        sql.SQL("""
        CREATE TABLE IF NOT EXISTS forecast (
            forecast_id SERIAL PRIMARY KEY,
            city_id INTEGER NOT NULL REFERENCES cities(city_id) ON DELETE CASCADE,
            
            city_name VARCHAR(100) NOT NULL,
            country VARCHAR(2) NOT NULL,
            
            -- Weather data 
            temperature NUMERIC(4, 1),
            feels_like NUMERIC(4, 1),
            weather_main VARCHAR(50),
            weather_description VARCHAR(100),
            humidity INTEGER,
            clouds INTEGER,
            pop NUMERIC(5, 2),
            pressure INTEGER,
            wind_speed NUMERIC(5, 1),
            wind_deg INTEGER,
            visibility NUMERIC(6, 1),
            rain_3h NUMERIC(6, 2),
            
            -- Timestamps
            timestamp BIGINT NOT NULL,
            forecast_time TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CONSTRAINT fk_city FOREIGN KEY(city_id) REFERENCES cities(city_id),
            CONSTRAINT chk_pop_range CHECK (pop BETWEEN 0 AND 100),
            CONSTRAINT chk_wind_deg CHECK (wind_deg BETWEEN 0 AND 360),
            CONSTRAINT uniq_forecast UNIQUE(city_id, forecast_time)
        );
        """),
        
        sql.SQL("""
        CREATE INDEX IF NOT EXISTS idx_forecast_city_time 
        ON forecast (city_id, forecast_time);
        """),
        
        sql.SQL("""
        CREATE INDEX IF NOT EXISTS idx_forecast_weather 
        ON forecast (weather_main, forecast_time);
        """),
        
        sql.SQL("""
        CREATE INDEX IF NOT EXISTS idx_forecast_location 
        ON forecast (latitude, longitude);
        """)
    ]
    
    with conn.cursor() as cursor:
        for query in queries:
            try:
                cursor.execute(query)
            except errors.DuplicateTable:
                conn.rollback()
                continue
        conn.commit()

def create_air_pollution_table(conn: pg.extensions.connection):
    queries = [
        sql.SQL("""
        CREATE TABLE IF NOT EXISTS air_pollution (
            pollution_id SERIAL PRIMARY KEY,
            city_id INTEGER NOT NULL REFERENCES cities(city_id) ON DELETE CASCADE,
            
            city_name VARCHAR(100) NOT NULL,
            country VARCHAR(2) NOT NULL,
            
            aqi INTEGER NOT NULL CHECK (aqi BETWEEN 1 AND 5),
        
            -- pollution components (μg/m³)
            co NUMERIC(6, 2),
            no NUMERIC(6, 2),
            no2 NUMERIC(6, 2),
            o3 NUMERIC(6, 2),
            so2 NUMERIC(6, 2),
            pm2_5 NUMERIC(6, 2),
            pm10 NUMERIC(6, 2),
            nh3 NUMERIC(6, 2),
            
            -- Timestamps
            timestamp BIGINT NOT NULL,
            measurement_time TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CONSTRAINT fk_city_pollution FOREIGN KEY(city_id) REFERENCES cities(city_id),
            CONSTRAINT uniq_pollution_reading UNIQUE(city_id, measurement_time)
        );
        """),
        
        sql.SQL("""
        CREATE INDEX IF NOT EXISTS idx_pollution_city_time 
        ON air_pollution (city_id, measurement_time);
        """),
        
        sql.SQL("""
        CREATE INDEX IF NOT EXISTS idx_pollution_aqi 
        ON air_pollution (aqi, measurement_time);
        """),
        
        sql.SQL("""
        CREATE INDEX IF NOT EXISTS idx_pollution_pm 
        ON air_pollution (pm2_5, pm10, measurement_time);
        """),
        
        sql.SQL("""
        CREATE INDEX IF NOT EXISTS idx_pollution_location 
        ON air_pollution (latitude, longitude);
        """)
    ]
    
    with conn.cursor() as cursor:
        for query in queries:
            try:
                cursor.execute(query)
            except errors.DuplicateTable:
                conn.rollback()
                continue
        conn.commit()
    
def create_suntimes_table(conn: pg.extensions.connection):
    queries = [
        sql.SQL("""
        CREATE TABLE IF NOT EXISTS suntimes (
            suntime_id SERIAL PRIMARY KEY,
            city_id INTEGER NOT NULL REFERENCES cities(city_id) ON DELETE CASCADE,
                
            city_name VARCHAR(100) NOT NULL,
            country VARCHAR(2) NOT NULL,
                
            date DATE NOT NULL,
            sunrise TIMESTAMP WITH TIME ZONE NOT NULL,
            sunrise_unix BIGINT NOT NULL,
            sunset TIMESTAMP WITH TIME ZONE NOT NULL,
            sunset_unix BIGINT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT unique_city_date UNIQUE (city_id, date),
            CONSTRAINT valid_sun_times CHECK (sunrise_unix < sunset_unix)
        );
        """),
        sql.SQL("CREATE INDEX IF NOT EXISTS idx_suntimes_city ON suntimes (city_id);"),
        sql.SQL("CREATE INDEX IF NOT EXISTS idx_suntimes_date ON suntimes (date);"),
        sql.SQL("""
        CREATE INDEX IF NOT EXISTS idx_suntimes_unix 
        ON suntimes (sunrise_unix, sunset_unix);
        """)
    ]
    
    with conn.cursor() as cursor:
        for query in queries:
            try:
                cursor.execute(query)
            except errors.DuplicateTable:
                conn.rollback()
                continue
        conn.commit()


def single_insert_record(
    conn: pg.extensions.connection,
    table_type: str,
    data: dict,
    extra_params: dict = None
) -> int:

    if table_type not in TABLE_CONFIGS:
        raise ValueError(f"Unknown table type: {table_type}")
    
    config = TABLE_CONFIGS[table_type]
    params = []
    
    try:
        
        if not all(field in data for field in ['city_name', 'country', 'lat', 'lon']):
                raise ValueError("Missing required fields to get city_id")
            
        with conn.cursor() as cursor:
            city_id = get_city_id(
                cursor,
                city_name=data['city_name'],
                country=data['country'],
                lat=data['lat'],
                lon=data['lon']
            )
            # add it to data
            data['city_id'] = city_id

        # validate and prepare parameters
        for field in config['fields_order']:
            if field in data:
                params.append(data[field])
            elif field in config['required']:
                raise ValueError(f"Missing required field: {field}")
            else:
                params.append(None) 
            
        # add extra parameters if provided
        if extra_params:
            params.extend(extra_params.values())
        
        # execute query
        with conn.cursor() as cursor:
            cursor.execute(config['sql'], params)
            return 1 if cursor.rowcount > 0 else 0
            
    except pg.Error as e:
        conn.rollback()
        raise RuntimeError(f"Failed to insert {table_type} data: {str(e)}")
    except Exception as e:
        raise ValueError(f"Invalid data for {table_type}: {str(e)}")


def bulk_insert_records(
    conn: pg.extensions.connection,
    table_type: str,
    data_list: list[dict],
    batch_size: int = 100
) -> dict:
    
    if table_type not in TABLE_CONFIGS:
        raise ValueError(f"Unsupported table type: {table_type}")
    
    config = TABLE_CONFIGS[table_type]
    results = {
        "total": len(data_list),
        "processed": 0,
        "inserted": 0,
        "skipped": 0,
        "errors": []
    }

    city_cache = {}
    with conn.cursor() as cursor:
        # preload all cities
        cursor.execute("SELECT city_id, city_name, country, latitude, longitude FROM cities")
        for row in cursor:
            key = (row[1], row[2], round(row[3], 4), round(row[4], 4))  # rounding to 4 decimal places (~11m precision)
            city_cache[key] = row[0]
    
    # prepare validated data
    validated_data = []
    for idx, data in enumerate(data_list):
        try:
            required_fields = ['city_name', 'country', 'lat', 'lon']
            if not all(field in data for field in required_fields):
                raise ValueError("Missing required fields to get city_id")
            
            cache_key = (
                data['city_name'],
                data['country'],
                round(data['lat'], 4),
                round(data['lon'], 4)
            )
            
            if cache_key not in city_cache:
                raise ValueError(f"city_id not found for: {cache_key}")
            
            data['city_id'] = city_cache[cache_key]

            params = []
            for field in config['fields_order']:
                if field in data: 
                    params.append(data[field])
                elif field in config['required']:
                    raise ValueError(f"Missing required field: {field}")
                else:
                    params.append(None)
            
            validated_data.append(params)
            results["processed"] += 1
            
        except Exception as e:
            results["errors"].append({
                "record_index": idx,
                "record_id": data.get('city_id', 'unknown'),
                "error": str(e)
            })
            continue
    
    # execute batch insert if we have valid data
    if validated_data:
        with conn.cursor() as cursor:
            try:
                from psycopg2.extras import execute_values
                execute_values(
                    cursor,
                    config['sql'],
                    validated_data,
                    page_size=batch_size
                )
                inserted = cursor.rowcount
                results["inserted"] = inserted
                results["skipped"] = len(validated_data) - inserted
                conn.commit()
            except pg.Error as e:
                conn.rollback()
                results["errors"].append({
                    "error": f"Database operation failed: {str(e)}"
                })
    
    return results


def clean_old_forecasts(
    conn: pg.extensions.connection,
    retention_days: int = 3
) -> int:

    query = sql.SQL("""
    DELETE FROM forecast 
    WHERE forecast_time < NOW() - INTERVAL %s
    RETURNING 1;
    """)
    
    with conn.cursor() as cursor:
        try:
            cursor.execute(query, (f"{retention_days} days",))
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
        except pg.Error as e:
            conn.rollback()
            raise RuntimeError(f"Failed to clean old forecasts: {e}")

