import logging
import os
from pathlib import Path
from ..helpers.json_helper import load_json_file, save_json_file
from ..processing.transformer.air_quality_transformer import AirQualityTransformer
from ..processing.transformer.forecast_transformer import ForecastTransformer
from ..processing.transformer.suntimes_transformer import SunTimesTransformer
from ..processing.transformer.weather_transformer import WeatherTransformer
from ..processing.utils.timezone_utils import add_timezones_to_csv


def main():
    try:
        # set up paths using Path from pathlib
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / "data"
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"
        
        # create processed directory if it doesn't exist
        processed_dir.mkdir(parents=True, exist_ok=True)

        # 1. prepare transformer and data
        geo_data_path = raw_dir / "geo_data.csv"
        weather_data_path = raw_dir / "current_2025-07-08T17-26.json"
        geo_data_with_tz_path = raw_dir / "geo_data_with_tz.csv"

        add_timezones_to_csv(
            csv_path=str(geo_data_path),
            json_path=str(weather_data_path),
            output_path=str(geo_data_with_tz_path)
        )
        
        weather_transformer = WeatherTransformer()
        forecast_transformer = ForecastTransformer()
        air_quality_transformer = AirQualityTransformer(timezone_csv_path=str(geo_data_with_tz_path))
        suntimes_transformer = SunTimesTransformer()



        logging.info("Starting data transformation pipeline...")
        
        # process weather data
        weather_raw = load_json_file(weather_data_path)
        weather_transformed = weather_transformer.transform(weather_raw)
        save_json_file(
            weather_transformed,
            processed_dir / "current_transformed.json"
        )

        # 5. Process forecast data
        forecast_file = raw_dir / "forecast_2025-07-08T17-26.json"
        forecast_transformed = forecast_transformer.transform(
            load_json_file(forecast_file)
        )
        save_json_file(
            forecast_transformed,
            processed_dir / "forecast_transformed.json"
        )

        # 6. Process air quality data
        air_quality_transformed = air_quality_transformer.transform(
            load_json_file(raw_dir / "air_pollution_2025-07-08T17-26.json")
        )
        save_json_file(
            air_quality_transformed,
            processed_dir / "air_quality_transformed.json"
        )

        # 4. Process sun times data (from same weather file)
        suntimes_transformed = suntimes_transformer.transform(weather_raw)
        save_json_file(
            suntimes_transformed,
            processed_dir / "suntimes_transformed.json"
        )


        # 6. Process air quality data
        air_quality_transformed = air_quality_transformer.transform(
            load_json_file(raw_dir / "air_pollution_2025-07-08T17-26.json")
        )
        save_json_file(
            air_quality_transformed,
            processed_dir / "air_quality_transformed.json"
        )

        logging.info("Data transformation pipeline completed successfully.")

    except Exception as e:
        logging.exception(f"Pipeline failed with error: {str(e)}")
        raise  


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('pipeline.log'),
            logging.StreamHandler()
        ]
    )
    
    main()