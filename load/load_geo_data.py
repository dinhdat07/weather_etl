import csv
from typing import NoReturn
import psycopg2 as pg
from dotenv import load_dotenv
import os
from psycopg2 import sql, errors

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

def create_cities_table(conn: pg.extensions.connection) -> None:
    queries = [
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
    ]
    
    with conn.cursor() as cursor:
        for query in queries:
            try:
                cursor.execute(query)
            except errors.DuplicateTable:
                pass # table/ index exists
        conn.commit()



def load_geo_data(conn: pg.extensions.connection, csv_path: str = 'raw/geo_data.csv') -> None:
    with conn.cursor() as cursor:
        try:
            with open(csv_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    cursor.execute(
                        sql.SQL("""
                            INSERT INTO cities 
                            (city_name, country, latitude, longitude, vi_name, timezone)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (city_name, country, latitude, longitude) 
                                DO UPDATE SET vi_name = EXCLUDED.vi_name,
                                timezone = EXCLUDED.timezone;
                        """),
                        (
                            row['city'],
                            row['country'],
                            float(row['lat']),
                            float(row['lon']),
                            row['vi_name'],
                            row['timezone']

                        )
                    )
            conn.commit()
        except (FileNotFoundError, csv.Error) as e:
            conn.rollback()
            raise ValueError(f"CSV processing failed: {e}")
        except pg.Error as e:
            conn.rollback()
            raise RuntimeError(f"Database operation failed: {e}")
        
def main() -> NoReturn:
    try:
        conn = get_db_connection()
        create_cities_table(conn)
        load_geo_data(conn)
        print("Geo data loaded to database successfully!")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    main()