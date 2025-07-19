from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.utils import timezone
from airflow.providers.postgres.hooks.postgres import PostgresHook
import logging
from google.cloud import storage
import pandas as pd

from config.path_config import PathConfig
from utils.gcs_utils import download_blob, upload_blob

logger = logging.getLogger("airflow.task")

default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}

@dag(
    dag_id='weather_data_pipeline_prod',
    default_args=default_args,
    description='Production-grade weather data ETL pipeline',
    schedule='0 */3 * * *',  # every 3 hours
    start_date=timezone.datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=['weather', 'production'],
)
def weather_data_pipeline():

    # ---------- Tasks ----------
    @task(task_id='geo_lookup')
    def geo_lookup() -> str:
        paths = PathConfig()
        timestamp = timezone.utcnow().strftime("%Y-%m-%dT%H-%M")

        bucket_name = Variable.get("GCS_BUCKET")

        cities_blob = f"{paths.gcs_prefix}/config/cities.csv"
        geo_output_blob = f"{paths.gcs_prefix}/outputs/geo_data.csv"
        local_geo_data = paths.geo_data
        
        try:
            logger.info("Starting geo lookup...")
            from extraction.geo_lookup import GeoLookup
            
            geo = GeoLookup(
                bucket_name=bucket_name,
                cities_blob=cities_blob,
                geo_blob=geo_output_blob,
                local_geo_path=local_geo_data
            )

            geo.run()

            return timestamp
        except Exception as e:
            logger.exception("Geo lookup failed: ", e)
            raise



    @task(task_id='extract_weather_data')
    def extract_weather_data(timestamp: str) -> Dict[str, str]:
        paths = PathConfig()
        weather_paths = paths.get_weather_paths(timestamp)
        
        try:
            logger.info("Starting weather data extraction...")
            
            from extraction.weather_fetcher import WeatherFetcher
            
            geo_file = paths.raw / "geo_data.csv"
            weather_fetcher = WeatherFetcher(
                geo_data=str(geo_file),
                output_dir=str(paths.raw)  
            )
            
            # fetching data in parallel requires async setup
            weather_fetcher.run(str(weather_paths['current']), 'current')
            weather_fetcher.run(str(weather_paths['forecast']), 'forecast')
            weather_fetcher.run(str(weather_paths['air_pollution']), 'air_pollution')
            
            logger.info(f"Weather data extracted to {paths.raw}")
            return {
                'timestamp': timestamp,
                'current': str(weather_paths['current']),
                'forecast': str(weather_paths['forecast']),
                'air_pollution': str(weather_paths['air_pollution']),
            }
            
        except Exception as e:
            logger.exception("Weather data extraction failed")
            raise


        

    @task(task_id='add_timezones')
    def add_timezones(extraction_result: Dict[str, str]) -> Dict[str, str]:
        paths = PathConfig()
        
        try:
            logger.info("Adding timezone information...")
            
            from processing.utils.timezone_utils import add_timezones_to_csv
            
            add_timezones_to_csv(
                csv_path=str(paths.geo_data),
                json_path=extraction_result['current'],
                output_path=str(paths.geo_data_with_tz)
            )
            
            logger.info(f"Timezone data added to {paths.geo_data_with_tz}")
            return extraction_result  # pass through the same data
            
        except Exception as e:
            logger.exception("Failed to add timezones")
            raise

    @task(task_id='transform_current_weather')
    def transform_current_weather(data_paths: Dict[str, str]) -> str:
        """Task to transform current weather data"""
        paths = PathConfig()
        timestamp = data_paths['timestamp']
        transformed_paths = paths.get_transformed_paths(timestamp)
        
        try:
            logger.info("Transforming current weather data...")
            
            from helpers.json_helper import load_json_file, save_json_file
            from processing.transformer.weather_transformer import WeatherTransformer
            
            raw_data = load_json_file(data_paths['current'])
            transformer = WeatherTransformer()
            transformed_data = transformer.transform(raw_data)
            
            save_json_file(transformed_data, transformed_paths['current'])
            
            logger.info(f"Current weather transformed to {transformed_paths['current']}")
            return str(transformed_paths['current'])
            
        except Exception as e:
            logger.exception("Current weather transformation failed")
            raise

    @task(task_id='transform_forecast')
    def transform_forecast(data_paths: Dict[str, str]) -> str:
        paths = PathConfig()
        timestamp = data_paths['timestamp']
        transformed_paths = paths.get_transformed_paths(timestamp)
        
        try:
            logger.info("Transforming forecast data...")
            
            from helpers.json_helper import load_json_file, save_json_file
            from processing.transformer.forecast_transformer import ForecastTransformer
            
            raw_data = load_json_file(data_paths['forecast'])
            transformer = ForecastTransformer()
            transformed_data = transformer.transform(raw_data)
            
            save_json_file(transformed_data, transformed_paths['forecast'])
            
            logger.info(f"Forecast transformed to {transformed_paths['forecast']}")
            return str(transformed_paths['forecast'])
            
        except Exception as e:
            logger.exception("Forecast transformation failed")
            raise

    @task(task_id='transform_air_quality')
    def transform_air_quality(data_paths: Dict[str, str]) -> str:
        paths = PathConfig()
        timestamp = data_paths['timestamp']
        transformed_paths = paths.get_transformed_paths(timestamp)
        
        try:
            logger.info("Transforming air quality data...")
            
            from helpers.json_helper import load_json_file, save_json_file
            from processing.transformer.air_quality_transformer import AirQualityTransformer
            
            raw_data = load_json_file(data_paths['air_pollution'])
            transformer = AirQualityTransformer(timezone_csv_path=str(paths.geo_data_with_tz))
            transformed_data = transformer.transform(raw_data)
            
            save_json_file(transformed_data, transformed_paths['air_pollution'])
            
            logger.info(f"Air quality transformed to {transformed_paths['air_pollution']}")
            return str(transformed_paths['air_pollution'])
            
        except Exception as e:
            logger.exception("Air quality transformation failed")
            raise

    @task(task_id='transform_suntimes', trigger_rule='none_failed')
    def transform_suntimes(data_paths: Dict[str, str]) -> Optional[str]:
        paths = PathConfig()
        date_str = data_paths['timestamp'][:10]  # YYYY-MM-DD
        
        # only run between midnight and 3 AM
        if datetime.now().hour >= 3:
            logger.info("Skipping suntimes transformation - not in time window")
            return None
        
        try:
            logger.info("Transforming suntimes data...")
            
            from helpers.json_helper import load_json_file, save_json_file
            from processing.transformer.suntimes_transformer import SunTimesTransformer
            
            raw_data = load_json_file(data_paths['current'])
            transformer = SunTimesTransformer()
            transformed_data = transformer.transform(raw_data)
            
            output_path = paths.get_transformed_paths(date_str)['suntimes']
            save_json_file(transformed_data, output_path)
            
            logger.info(f"Suntimes transformed to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.exception("Suntimes transformation failed")
            raise


    @task(task_id='create_tables')
    def create_tables():
        hook = PostgresHook(postgres_conn_id="weather_db")
        conn = None
        try:
            conn = hook.get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name IN ('cities', 'weather_data', 'forecast', 'suntimes', 'air_pollution')
            """)
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            # execute creation queries for missing tables
            from storage.database.sql.creation import CREATION_QUERIES
            for table_name, queries in CREATION_QUERIES.items():
                if table_name not in existing_tables:
                    logger.info(f"Creating table {table_name}...")
                    for query in queries:
                        try:
                            cursor.execute(query)
                            conn.commit()
                        except Exception as e:
                            conn.rollback()
                            logger.warning(f"Table {table_name} might already exist, skip creating...")
            
            logger.info("Database tables verified/created")
        except Exception as e:
            logger.exception("Failed to create tables")
            raise
        finally:
            if conn:
                conn.close()

    @task(task_id='sync_cities')
    def sync_cities():
        try:
            hook = PostgresHook(postgres_conn_id="weather_db")
            conn = hook.get_conn()
            paths = PathConfig()
            df = pd.read_csv(paths.geo_data_with_tz)

            with conn.cursor() as cur:
                for _, row in df.iterrows():
                    cur.execute("""
                        INSERT INTO cities (city_name, country, latitude, longitude, vi_name, timezone)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (city_name, country, latitude, longitude)
                        DO UPDATE SET
                            vi_name = EXCLUDED.vi_name,
                            timezone = EXCLUDED.timezone;
                    """, (row.city, row.country, row.lat, row.lon, row.get('vi_name'), row.get('timezone')))
                conn.commit()

            logger.info("Synced cities into database.")
        except Exception as e:
            logger.exception("Syncing cities failed")
            raise
        finally:
            if conn:
                conn.close()

    @task(
        task_id='load_data',
        retries=3,
        retry_delay=timedelta(minutes=2),
        execution_timeout=timedelta(minutes=45)
    )
    def load_data(
        current_path: str,
        forecast_path: str,
        air_quality_path: str,
        suntimes_path: Optional[str] = None
    ) -> Dict[str, int]:
    
        try:
            logger.info("Initializing database connection...")
            
            from helpers.json_helper import load_json_file
            from storage.database.operations import DatabaseOperations

            
            hook = PostgresHook(postgres_conn_id="weather_db")
            conn = hook.get_conn()

            _validate_tables_exist(conn, ['cities', 'weather_data', 'forecast', 'air_pollution', 'suntimes'])
            db_ops = DatabaseOperations(conn)
            
            # process in batches
            def safe_batch_insert(data: List[Dict], table: str) -> int:
                if not data:
                    return 0
                try:
                    batch_size = 1000
                    for i in range(0, len(data), batch_size):
                        db_ops.bulk_insert(table, data[i:i+batch_size])
                    return len(data)
                except Exception as e:
                    logger.error(f"Batch insert failed for {table}: {str(e)}")
                    raise
            
            # load current weather
            results = {}
            # Current weather
            current_data = load_json_file(current_path)
            results['current'] = safe_batch_insert(current_data, 'weather_data')
            
            # Forecast
            forecast_data = load_json_file(forecast_path)
            results['forecast'] = safe_batch_insert(forecast_data, 'forecast')
            
            # Air quality
            air_quality_data = load_json_file(air_quality_path)
            results['air_quality'] = safe_batch_insert(air_quality_data, 'air_pollution')
            
            # Suntimes (optional)
            if suntimes_path:
                suntimes_data = load_json_file(suntimes_path)
                results['suntimes'] = safe_batch_insert(suntimes_data, 'suntimes')
            
            # Maintenance
            results['cleaned'] = db_ops.clean_old_forecasts(retention_days=3)
            
            logger.info(
                f"Load completed: {results['current']} current, "
                f"{results['forecast']} forecast, "
                f"{results.get('suntimes', 0)} suntimes | "
                f"Cleaned {results['cleaned']} old records"
            )

            return results
            
        except Exception as e:
            logger.exception("Data loading failed")
            raise
        finally:
            if 'conn' in locals() and conn:
                conn.close()
                logger.info("Database connection closed")
            
    
    def _validate_tables_exist(conn, required_tables: List[str]):
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = ANY(%s)
            """, (required_tables,))
            
            existing_tables = {row[0] for row in cursor.fetchall()}
            missing_tables = set(required_tables) - existing_tables
            
            if missing_tables:
                raise RuntimeError(f"Missing tables: {missing_tables}. Run schema creation first.")


    # ---------- Task Dependencies ----------
    tables_created = create_tables()
    timestamp = geo_lookup()
    
    # Extract weather data in parallel with geo lookup
    weather_data = extract_weather_data(timestamp)
    
    # Add timezones after both geo lookup and weather extraction complete
    with_timezones = add_timezones(weather_data)

    cities_synced = sync_cities()
    cities_synced.set_upstream(with_timezones)
    
    # Transform all data types in parallel
    current_transformed = transform_current_weather(with_timezones)
    forecast_transformed = transform_forecast(with_timezones)
    air_quality_transformed = transform_air_quality(with_timezones)
    suntimes_transformed = transform_suntimes(with_timezones)
    

    # Load all transformed data
    load_results = load_data(
        current_path=current_transformed,
        forecast_path=forecast_transformed,
        air_quality_path=air_quality_transformed,
        suntimes_path=suntimes_transformed
    )

# Instantiate the DAG
weather_dag = weather_data_pipeline()