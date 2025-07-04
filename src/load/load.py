import json
import psycopg2 as pg
from psycopg2 import sql, errors
import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Optional
from datetime import datetime
import argparse

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from helpers.database_helpers import get_city_id
from helpers.json_helpers import load_json_file, save_json_file

from table_config import TABLE_CONFIGS
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
            sunrise_stamp BIGINT NOT NULL,
            sunset TIMESTAMP WITH TIME ZONE NOT NULL,
            sunset_stamp BIGINT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT unique_city_date UNIQUE (city_id, date),
            CONSTRAINT valid_sun_times CHECK (sunrise_stamp < sunset_stamp)
        );
        """),
        sql.SQL("CREATE INDEX IF NOT EXISTS idx_suntimes_city ON suntimes (city_id);"),
        sql.SQL("CREATE INDEX IF NOT EXISTS idx_suntimes_date ON suntimes (date);"),
        sql.SQL("""
        CREATE INDEX IF NOT EXISTS idx_suntimes_stamp 
        ON suntimes (sunrise_stamp, sunset_stamp);
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
        
        if not all(field in data for field in ['city', 'country', 'lat', 'lon']):
                raise ValueError("Missing required fields to get city_id")
            
        with conn.cursor() as cursor:
            city_id = get_city_id(
                cursor,
                city_name=data['city'],
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
            key = (row[1], row[2])
            lat = float(row[3])
            lon = float(row[4])
            city_cache.setdefault(key, []).append( (lat, lon, row[0]) )
    

    # prepare validated data
    validated_data = []
    for idx, data in enumerate(data_list):
        try:
            
            required_fields = ['city', 'country', 'lat', 'lon']
            
            if not all(field in data for field in required_fields):
                raise ValueError("Missing required fields to get city_id")
            
            city_key = (data['city'], data['country'])
            if city_key not in city_cache:
                raise ValueError(f"city {city_key} not found in cache")

            # approximate match (within 0.001 degrees ~ 100m)
            matched_city_id = None
            for cached_lat, cached_lon, city_id in city_cache[city_key]:
                if abs(cached_lat - data['lat']) < 0.001 and abs(cached_lon - data['lon']) < 0.001:
                    matched_city_id = city_id
                    break

            if not matched_city_id:
                raise ValueError(
                    f"city_id not found within tolerance 0.001 for: "
                    f"{city_key} at lat={data['lat']}, lon={data['lon']}"
                )

            data['city_id'] = matched_city_id
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
    
    print(len(validated_data))
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



def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data_pipeline.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='Load Weather Data')
    
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Single insert command
    single_parser = subparsers.add_parser('single-insert')
    single_parser.add_argument('--table', required=True, 
                             choices=['weather', 'forecast', 'air_pollution', 'suntimes'],
                             help='Target table')
    single_parser.add_argument('--input-file', required=True,
                             help='Path to JSON input file')
    
    # Batch insert command
    batch_parser = subparsers.add_parser('batch-insert')
    batch_parser.add_argument('--table', required=True,
                            choices=['weather', 'forecast', 'air_pollution', 'suntimes'],
                            help='Target table')
    batch_parser.add_argument('--input-file', required=True,
                            help='Path to JSON input file')
    batch_parser.add_argument('--batch-size', type=int, default=1000,
                            help='Batch size for bulk insert')
    
    # Maintenance command
    maint_parser = subparsers.add_parser('maintenance')
    maint_parser.add_argument('--action', required=True,
                            choices=['clean_forecasts', 'vacuum_analyze'],
                            help='Maintenance action')
    maint_parser.add_argument('--retention-days', type=int, default=3,
                            help='Days to retain for forecast data')
    
    return parser.parse_args()

def validate_data(table_type: str, data: Dict) -> bool:
    config = TABLE_CONFIGS.get(table_type)
    if not config:
        raise ValueError(f"Invalid table type: {table_type}")
    
    missing_required = [f for f in config['required'] if f not in data]
    if missing_required:
        raise ValueError(f"Missing required fields: {missing_required}")
    
    return True

def process_single_record(conn, table_type: str, record: Dict) -> bool:
    try:
        validate_data(table_type, record)
        return single_insert_record(conn, table_type, record) == 1
    except Exception as e:
        logging.error(f"Failed to process record: {e}", exc_info=True)
        return False

def process_batch_records(conn, table_type: str, records: List[Dict], batch_size: int = 100) -> Dict:
    start_time = datetime.now()
    result = {
        'table': table_type,
        'total_records': len(records),
        'processed': 0,
        'succeeded': 0,
        'failed': 0,
        'start_time': start_time,
        'duration_seconds': 0
    }
    
    try:
        batch_result = bulk_insert_records(conn, table_type, records, batch_size)
        result.update({
            'processed': batch_result['processed'],
            'succeeded': batch_result['inserted'],
            'failed': batch_result['skipped'],
            'errors': batch_result['errors'][:10] 
        })
    except Exception as e:
        logging.error(f"Batch processing failed: {e}", exc_info=True)
        result['error'] = str(e)
    finally:
        result['duration_seconds'] = (datetime.now() - start_time).total_seconds()
    
    return result

def run_maintenance(conn, action: str, retention_days: int = 3) -> Dict:
    result = {'action': action, 'success': False}
    
    try:
        if action == 'clean_forecasts':
            deleted = clean_old_forecasts(conn, retention_days)
            result.update({
                'deleted_records': deleted,
                'retention_days': retention_days,
                'success': True
            })
            logging.info(f"Cleaned {deleted} forecast records older than {retention_days} days")
            
        elif action == 'vacuum_analyze':
            with conn.cursor() as cursor:
                cursor.execute("VACUUM ANALYZE")
                result['success'] = True
                logging.info("Database maintenance (VACUUM ANALYZE) completed")
    
    except Exception as e:
        logging.error(f"Maintenance operation failed: {e}", exc_info=True)
        result['error'] = str(e)
    
    return result

def main():
    logger = configure_logging()
    args = parse_args()
    
    try:
        with get_db_connection() as conn:
            logger.info(f"Executing command: {args.command}")
            
            if args.command == 'single-insert':
                data = load_json_file(args.input_file)
                success = process_single_record(conn, args.table, data)
                logger.info(f"Single insert {'succeeded' if success else 'failed'}")

            elif args.command == 'batch-insert':
                records = load_json_file(args.input_file)
                if not isinstance(records, list):
                    raise ValueError("Batch input must be a list of records")
                
                result = process_batch_records(conn, args.table, records, args.batch_size)
                logger.info(
                    f"Batch insert completed - "
                    f"Processed: {result['processed']}, "
                    f"Succeeded: {result['succeeded']}, "
                    f"Failed: {result['failed']}, "
                    f"Duration: {result['duration_seconds']:.2f}s"
                )
                
                if result.get('errors'):
                    for error in result['errors']:
                        logger.error(f"Record error: {error}")

            elif args.command == 'maintenance':
                result = run_maintenance(conn, args.action, args.retention_days)
                if result['success']:
                    logger.info(f"Maintenance action '{args.action}' completed successfully")
                else:
                    logger.error(f"Maintenance failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    conn = get_db_connection()

    try:
        create_weather_table(conn)
        create_forecast_table(conn)
        create_air_pollution_table(conn)
        create_suntimes_table(conn)

        weather_batch = load_json_file('processed/current_weather_transformed.json')
        if weather_batch:
            weather_result = bulk_insert_records(
                conn, 
                'weather', 
                weather_batch, 
                batch_size=100
            )
            print(f"Weather: Inserted {weather_result['inserted']} records, {weather_result['skipped']} skipped, error: {weather_result['errors']}")

        pollution_batch = load_json_file('processed/air_quality_transformed.json')
        if pollution_batch:
            pollution_result = bulk_insert_records(
                conn,
                'air_pollution',
                pollution_batch,
                batch_size=100
            )
            print(f"Air Pollution: Inserted {pollution_result['inserted']} records, {pollution_result['skipped']} skipped, error: {pollution_result['errors']}")

        suntimes_batch = load_json_file('processed/sun_times_transformed.json')
        if suntimes_batch:
            suntimes_result = bulk_insert_records(
                conn,
                'suntimes',
                suntimes_batch,
                batch_size=10
            )
            print(f"Suntimes: Inserted {suntimes_result['inserted']} records, {suntimes_result['skipped']} skipped, error: {suntimes_result['errors']}")

        forecast_batch = load_json_file('processed/forecast_transformed.json')
        if forecast_batch:
            forecast_result = bulk_insert_records(
                conn,
                'forecast',
                forecast_batch,
                batch_size=400
            )
            print(f"Forecast: Inserted or Updated: {forecast_result['processed']} records, error: {forecast_result['errors']}")

    finally:
        conn.close()