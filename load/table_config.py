from sql_query import AIR_POLLUTION_INSERT_SQL, FORECAST_UPSERT_SQL, SUNTIMES_INSERT_SQL, WEATHER_INSERT_SQL


TABLE_CONFIGS = {
    'weather': {
        'sql': WEATHER_INSERT_SQL,
        'fields_order': [
            'city_id', 'city', 'country',
            'temperature', 'feels_like', 'weather_main', 'weather_description',
            'humidity', 'clouds', 'pressure', 'wind_speed', 'wind_deg',
            'visibility', 'rain_1h', 'timestamp', 'time'
        ],
        'required': ['city_id', 'city', 'country', 'timestamp', 'time'],
        'optional': [
            'temperature', 'feels_like', 'weather_main', 'weather_description',
            'humidity', 'clouds', 'pressure', 'wind_speed', 'wind_deg',
            'visibility', 'rain_1h'
        ]
    },
    'air_pollution': {
        'sql': AIR_POLLUTION_INSERT_SQL,
        'fields_order': [
            'city_id', 'city', 'country',
            'aqi', 'co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3',
            'timestamp', 'time'
        ],
        'required': ['city_id', 'city', 'country', 'aqi', 'timestamp', 'time'],
        'optional': ['co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3']
    },
    'suntimes': {
        'sql': SUNTIMES_INSERT_SQL,
        'fields_order': [
            'city_id', 'city', 'country',
            'date', 'sunrise', 'sunrise_stamp', 'sunset', 'sunset_stamp'
        ],
        'required': [
            'city_id', 'city', 'country',
            'date', 'sunrise', 'sunrise_stamp', 'sunset', 'sunset_stamp'
        ],
        'optional': []
    },
    'forecast': {
        'sql': FORECAST_UPSERT_SQL,
        'fields_order': [
            'city_id', 'city', 'country',
            'temperature', 'feels_like', 'weather_main', 'weather_description',
            'humidity', 'clouds', 'pop', 'pressure', 'wind_speed', 'wind_deg',
            'visibility', 'rain_3h', 'timestamp', 'time'
        ],
        'required': ['city_id', 'city', 'country', 'timestamp', 'time'],
        'optional': [
            'temperature', 'feels_like', 'weather_main', 'weather_description',
            'humidity', 'clouds', 'pop', 'pressure', 'wind_speed', 'wind_deg',
            'visibility', 'rain_3h'
        ]
    }
}