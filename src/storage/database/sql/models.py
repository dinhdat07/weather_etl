import os
import sys


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
from src.storage.database.sql.insertion import INSERT_QUERIES


TABLE_CONFIGS = {
    'weather': {
        'sql': INSERT_QUERIES['WEATHER']['insert'],
        'fields_order': [
            'city_id', 'city', 'country',
            'temperature', 'feels_like', 'weather_main', 'weather_description',
            'humidity', 'clouds', 'pressure', 'wind_speed', 'wind_deg',
            'visibility', 'rain_1h', 'timestamp', 'time'
        ],
        'required': {
            'lookup': ['city', 'country', 'lat', 'lon'],
            'insert': ['city_id', 'timestamp', 'time']
        },
        'optional': [
            'temperature', 'feels_like', 'weather_main', 'weather_description',
            'humidity', 'clouds', 'pressure', 'wind_speed', 'wind_deg',
            'visibility', 'rain_1h'
        ]
    },
    'air_quality': {
        'sql': INSERT_QUERIES['AIR_POLLUTION']['insert'],
        'fields_order': [
            'city_id', 'city', 'country',
            'aqi', 'co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3',
            'timestamp', 'time'
        ],
        'required': {
            'lookup': ['city', 'country', 'lat', 'lon'],
            'insert': ['city_id', 'aqi', 'timestamp', 'time']
        },
        'optional': ['co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3']
    },
    'suntimes': {
        'sql': INSERT_QUERIES['SUNTIMES']['insert'],
        'fields_order': [
            'city_id', 'city', 'country',
            'date', 'sunrise', 'sunrise_stamp', 'sunset', 'sunset_stamp'
        ],
        'required': {
            'lookup': ['city', 'country', 'lat', 'lon'],
            'insert': [
                'city_id', 'date', 'sunrise', 'sunrise_stamp', 'sunset', 'sunset_stamp'
            ]
        },
        'optional': []
    },
    'forecast': {
        'sql': INSERT_QUERIES['FORECAST']['upsert'],
        'fields_order': [
            'city_id', 'city', 'country',
            'temperature', 'feels_like', 'weather_main', 'weather_description',
            'humidity', 'clouds', 'pop', 'pressure', 'wind_speed', 'wind_deg',
            'visibility', 'rain_3h', 'timestamp', 'time'
        ],
        'required': {
            'lookup': ['city', 'country', 'lat', 'lon'],
            'insert': ['city_id', 'timestamp', 'time']
        },
        'optional': [
            'temperature', 'feels_like', 'weather_main', 'weather_description',
            'humidity', 'clouds', 'pop', 'pressure', 'wind_speed', 'wind_deg',
            'visibility', 'rain_3h'
        ]
    }
}
