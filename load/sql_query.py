# Weather data SQL
WEATHER_INSERT_SQL = """
INSERT INTO weather_data (
    city_id, city_name, country,
    temperature, feels_like, weather_main, weather_description,
    humidity, clouds, pressure, wind_speed, wind_deg,
    visibility, rain_1h, timestamp, time
) VALUES %s
ON CONFLICT (city_id, time) DO NOTHING;
"""

# Air pollution SQL
AIR_POLLUTION_INSERT_SQL = """
INSERT INTO air_pollution (
    city_id, city_name, country,
    aqi, co, no, no2, o3, so2, pm2_5, pm10, nh3,
    timestamp, measurement_time
) VALUES %s
ON CONFLICT (city_id, measurement_time) DO NOTHING;
"""

# Sun times SQL
SUNTIMES_INSERT_SQL = """
INSERT INTO suntimes (
    city_id, city_name, country,
    date, sunrise, sunrise_unix, sunset, sunset_unix
) VALUES %s
ON CONFLICT (city_id, date) DO NOTHING;
"""

# Forecast SQL
FORECAST_UPSERT_SQL = """
INSERT INTO forecast (
    city_id, city_name, country,
    temperature, feels_like, weather_main, weather_description,
    humidity, clouds, pop, pressure, wind_speed, wind_deg,
    visibility, rain_3h, timestamp, forecast_time
) VALUES %s
ON CONFLICT (city_id, forecast_time) 
DO UPDATE SET
    temperature = EXCLUDED.temperature,
    feels_like = EXCLUDED.feels_like,
    weather_main = EXCLUDED.weather_main,
    weather_description = EXCLUDED.weather_description,
    humidity = EXCLUDED.humidity,
    clouds = EXCLUDED.clouds,
    pop = EXCLUDED.pop,
    pressure = EXCLUDED.pressure,
    wind_speed = EXCLUDED.wind_speed,
    wind_deg = EXCLUDED.wind_deg,
    visibility = EXCLUDED.visibility,
    rain_3h = EXCLUDED.rain_3h,
    timestamp = EXCLUDED.timestamp,
    updated_at = CURRENT_TIMESTAMP;
"""