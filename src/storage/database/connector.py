import psycopg2 as pg
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnector:
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT') 

    @staticmethod
    def get_connection() -> pg.extensions.connection:
        try:
            return pg.connect(
                dbname=DatabaseConnector.DB_NAME,
                user=DatabaseConnector.DB_USER,
                password=DatabaseConnector.DB_PASSWORD,
                host=DatabaseConnector.DB_HOST,
                port=DatabaseConnector.DB_PORT
            )
        except pg.Error as e:
            raise ConnectionError(f"Database connection failed: {str(e)}")