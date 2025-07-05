from ..sql.insertion import INSERT_QUERIES


TABLE_CONFIGS = {
    'weather': {
        'sql': INSERT_QUERIES['WEATHER'],
        'fields_order': [
            'city_id', 'city', 'country',
            'temperature', 'feels_like', 'weather_main', 'weather_description',
            'humidity', 'clouds', 'pressure', 'wind_speed', 'wind_deg',
            'visibility', 'rain_1h', 'timestamp', 'time'
        ],
        'required': ['city_id', 'city', 'country', 'timestamp', 'time', 'lat', 'lon'],
        'optional': [
            'temperature', 'feels_like', 'weather_main', 'weather_description',
            'humidity', 'clouds', 'pressure', 'wind_speed', 'wind_deg',
            'visibility', 'rain_1h'
        ]
    },
    'air_pollution': {
        'sql': INSERT_QUERIES['AIR_POLLUTION'],
        'fields_order': [
            'city_id', 'city', 'country',
            'aqi', 'co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3',
            'timestamp', 'time'
        ],
        'required': ['city_id', 'city', 'country', 'aqi', 'timestamp', 'time', 'lat', 'lon'],
        'optional': ['co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3']
    },
    'suntimes': {
        'sql': INSERT_QUERIES['SUNTIMES'],
        'fields_order': [
            'city_id', 'city', 'country',
            'date', 'sunrise', 'sunrise_stamp', 'sunset', 'sunset_stamp'
        ],
        'required': [
            'city_id', 'city', 'country',
            'date', 'sunrise', 'sunrise_stamp', 'sunset', 'sunset_stamp', 'lat', 'lon'
        ],
        'optional': []
    },
    'forecast': {
        'sql': INSERT_QUERIES['FORECAST'],
        'fields_order': [
            'city_id', 'city', 'country',
            'temperature', 'feels_like', 'weather_main', 'weather_description',
            'humidity', 'clouds', 'pop', 'pressure', 'wind_speed', 'wind_deg',
            'visibility', 'rain_3h', 'timestamp', 'time'
        ],
        'required': ['city_id', 'city', 'country', 'timestamp', 'time', 'lat', 'lon'],
        'optional': [
            'temperature', 'feels_like', 'weather_main', 'weather_description',
            'humidity', 'clouds', 'pop', 'pressure', 'wind_speed', 'wind_deg',
            'visibility', 'rain_3h'
        ]
    }
}