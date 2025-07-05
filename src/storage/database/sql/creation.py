from psycopg2 import sql

CREATION_QUERIES = {
        'cities': [
            sql.SQL("""
            CREATE TABLE IF NOT EXISTS cities (
                city_id SERIAL PRIMARY KEY,
                city_name VARCHAR(100) NOT NULL,
                country VARCHAR(2) NOT NULL,
                latitude NUMERIC(9, 6) NOT NULL,
                longitude NUMERIC(9, 6) NOT NULL,
                vi_name VARCHAR(100),
                timezone VARCHAR(50),
                UNIQUE (city_name, country, latitude, longitude)
            );
            """),
            sql.SQL("CREATE INDEX IF NOT EXISTS idx_cities_country ON cities (country);"),
            sql.SQL("CREATE INDEX IF NOT EXISTS idx_cities_coordinates ON cities (latitude, longitude);"),
            sql.SQL("CREATE INDEX IF NOT EXISTS idx_cities_timezone ON cities (timezone);")
        ],

        'weather_data':[
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
            """),
        ],
        
        'forecast':  [
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
        ],

        'suntimes': [
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
        ],

        'air_pollution' :  [
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
    }