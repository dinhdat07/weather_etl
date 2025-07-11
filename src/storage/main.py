import os
import logging
from pathlib import Path

from src.storage.database.connector import DatabaseConnector
from src.storage.database.operations import DatabaseOperations
from src.storage.database.schema_manager import SchemaManager
from src.helpers.json_helper import load_json_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("loader_pipeline.log")
    ]
)

def main():
    project_root = Path(__file__).parent.parent.parent
    processed_dir = project_root / "data" / "processed"

    try:
        conn = DatabaseConnector.get_connection()
        SchemaManager.create_tables(conn)

        db_ops = DatabaseOperations(conn)

        # insert current weather
        current_data = load_json_file(processed_dir / "current_transformed.json")
        results = db_ops.bulk_insert("weather", current_data)
        logging.info(f"Inserted current weather data: {results}")

        # insert forecast
        forecast_data = load_json_file(processed_dir / "forecast_transformed.json")
        results = db_ops.bulk_insert("forecast", forecast_data)
        logging.info(f"Inserted forecast data: {results}")

        # insert air quality
        aq_data = load_json_file(processed_dir / "air_quality_transformed.json")
        results = db_ops.bulk_insert("air_pollution", aq_data)
        logging.info(f"Inserted air quality data: {results}")

        # insert sun times
        sun_data = load_json_file(processed_dir / "suntimes_transformed.json")
        results = db_ops.bulk_insert("suntimes", sun_data)
        logging.info(f"Inserted suntimes data: {results}")

        # clean old forecasts
        deleted = db_ops.clean_old_forecasts(retention_days=3)
        logging.info(f"Cleaned old forecasts: {deleted} records")

    except Exception as e:
        logging.exception(f"Loader pipeline failed: {e}")
    finally:
        conn.close()
        logging.info("Closed database connection.")

if __name__ == "__main__":
    main()
