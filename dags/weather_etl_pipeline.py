from datetime import datetime, timedelta
from pathlib import Path
import logging
import sys
from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.utils.dates import days_ago

project_root = Path(__file__).parent.parent  
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

# logger configuration
def get_logger():
    """Configure and return a logger"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    file_handler = logging.FileHandler(log_dir / "weather_etl.log")
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger

logger = get_logger()

# default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def get_data_paths():
    """Get standardized data paths"""
    data_dir = Path(Variable.get("data_dir", default_var="/opt/airflow/data"))
    return {
        'raw': data_dir / "raw",
        'processed': data_dir / "processed",
        'geo_data': data_dir / "raw" / "geo_data.csv",
        'geo_data_with_tz': data_dir / "raw" / "geo_data_with_tz.csv"
    }

@dag(
    dag_id='weather_data_pipeline',
    default_args=default_args,
    description='A pipeline for weather data extraction, transformation and loading',
    schedule_interval='0 */3 * * *',  # every 3 hours
    start_date=days_ago(1),
    catchup=False,
    tags=['weather', 'etl'],
)
def weather_data_pipeline():

    @task(task_id='extract_data')
    def extract():
        """Extract data from APIs"""
        try:
            from extraction.geo_lookup import GeoLookup
            from extraction.weather_fetcher import WeatherFetcher
            
            paths = get_data_paths()
            paths['raw'].mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M")
            
            # run geo lookup
            geo = GeoLookup()
            geo.run()
            
            # fetch weather data
            weather_fetcher = WeatherFetcher()
            file_paths = {
                'current': str(paths['raw'] / f"current_{timestamp}.json"),
                'forecast': str(paths['raw'] / f"forecast_{timestamp}.json"),
                'air_pollution': str(paths['raw'] / f"air_pollution_{timestamp}.json"),
                'timestamp': timestamp
            }
            
            weather_fetcher.run('current', filename=file_paths['current'])
            weather_fetcher.run('forecast', filename=file_paths['forecast'])
            weather_fetcher.run('air_pollution', filename=file_paths['air_pollution'])
            
            logger.info(f"Extracted data saved with timestamp: {timestamp}")
            return file_paths
            
        except Exception as e:
            logger.exception("Extraction failed")
            raise

    @task(task_id='transform_data')
    def transform(file_paths: dict):
        """Transform raw data into processed format"""
        try:
            from helpers.json_helper import load_json_file, save_json_file
            from processing.transformer.air_quality_transformer import AirQualityTransformer
            from processing.transformer.forecast_transformer import ForecastTransformer
            from processing.transformer.suntimes_transformer import SunTimesTransformer
            from processing.transformer.weather_transformer import WeatherTransformer
            from processing.utils.timezone_utils import add_timezones_to_csv
            
            paths = get_data_paths()
            paths['processed'].mkdir(parents=True, exist_ok=True)
            timestamp = file_paths['timestamp']
            
            # Add timezones to geo data
            add_timezones_to_csv(
                csv_path=str(paths['geo_data']),
                json_path=file_paths['current'],
                output_path=str(paths['geo_data_with_tz'])
            )
            
            # Initialize transformers
            weather_transformer = WeatherTransformer()
            forecast_transformer = ForecastTransformer()
            air_quality_transformer = AirQualityTransformer(
                timezone_csv_path=str(paths['geo_data_with_tz'])
            )
            suntimes_transformer = SunTimesTransformer()

            logger.info("Starting data transformation pipeline...")
            transformed_files = {}
            
            # Current weather
            weather_raw = load_json_file(file_paths['current'])
            weather_transformed = weather_transformer.transform(weather_raw)
            current_output = paths['processed'] / f"current_transformed_{timestamp}.json"
            save_json_file(weather_transformed, current_output)
            transformed_files['current'] = str(current_output)
            
            # Forecast
            forecast_transformed = forecast_transformer.transform(
                load_json_file(file_paths['forecast'])
            )
            forecast_output = paths['processed'] / f"forecast_transformed_{timestamp}.json"
            save_json_file(forecast_transformed, forecast_output)
            transformed_files['forecast'] = str(forecast_output)
            
            # Air quality
            air_quality_transformed = air_quality_transformer.transform(
                load_json_file(file_paths['air_pollution'])
            )
            air_quality_output = paths['processed'] / f"air_quality_transformed_{timestamp}.json"
            save_json_file(air_quality_transformed, air_quality_output)
            transformed_files['air_quality'] = str(air_quality_output)
            
            # Sun times (only at midnight)
            if datetime.now().hour == 0:
                suntimes_transformed = suntimes_transformer.transform(weather_raw)
                suntimes_output = paths['processed'] / f"suntimes_transformed_{datetime.now().strftime('%Y-%m-%d')}.json"
                save_json_file(suntimes_transformed, suntimes_output)
                transformed_files['suntimes'] = str(suntimes_output)
            
            logger.info("Data transformation pipeline completed successfully.")
            return transformed_files
            
        except Exception as e:
            logger.exception(f"Transform failed: {str(e)}")
            raise

    @task(task_id='load_data')
    def load(transformed_files: dict):
        """Load processed data into database"""
        try:
            from storage.database.connector import DatabaseConnector
            from storage.database.operations import DatabaseOperations
            from storage.database.schema_manager import SchemaManager
            from helpers.json_helper import load_json_file
            
            conn = DatabaseConnector.get_connection()
            SchemaManager.create_tables(conn)
            db_ops = DatabaseOperations(conn)
            
            # load current weather
            current_data = load_json_file(transformed_files['current'])
            db_ops.bulk_insert("weather", current_data)
            logger.info("Inserted current weather data")
            
            # load forecast
            forecast_data = load_json_file(transformed_files['forecast'])
            db_ops.bulk_insert("forecast", forecast_data)
            logger.info("Inserted forecast data")
            
            # load air quality
            aq_data = load_json_file(transformed_files['air_quality'])
            db_ops.bulk_insert("air_quality", aq_data)
            logger.info("Inserted air quality data")
            
            # load suntimes if available
            if 'suntimes' in transformed_files:
                sun_data = load_json_file(transformed_files['suntimes'])
                db_ops.bulk_insert("suntimes", sun_data)
                logger.info("Inserted suntimes data")
            
            # clean old forecasts
            deleted = db_ops.clean_old_forecasts(retention_days=3)
            logger.info(f"Cleaned {deleted} old forecast records")
            
            return {"status": "success", "records_processed": len(current_data)}
            
        except Exception as e:
            logger.exception(f"Load failed: {str(e)}")
            raise
        finally:
            conn.close()
            logger.info("Closed database connection.")

    # task dependencies
    file_paths = extract()
    transformed_files = transform(file_paths)
    load(transformed_files)

# instantiate the DAG
weather_dag = weather_data_pipeline()