import psycopg2 as pg
from psycopg2 import sql, errors
import os
from dotenv import load_dotenv
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
            CONSTRAINT fk_city FOREIGN KEY(city_id) REFERENCES cities(city_id)
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
            
            -- Location fields (denormalized for query performance)
            city_name VARCHAR(100) NOT NULL,
            country VARCHAR(2) NOT NULL,
            
            -- Weather data (exact match with JSON structure)
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
            
            -- Location fields (denormalized for performance)
            city_name VARCHAR(100) NOT NULL,
            country VARCHAR(2) NOT NULL,
            
            -- Air quality indexes
            aqi INTEGER NOT NULL CHECK (aqi BETWEEN 1 AND 5),
            
            -- Pollution components (μg/m³)
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
    
def create_suntimes_table(conn):
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

