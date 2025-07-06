import os
import sys
from typing import List, Dict
import psycopg2 as pg
from psycopg2 import sql
from psycopg2.extras import execute_values
import logging


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from src.storage.database.sql.models import TABLE_CONFIGS
from src.processing.data_processor import DataProcessor
from src.storage.cache.city_cache import CityCache

logger = logging.getLogger(__name__)

class DatabaseOperations:
    def __init__(self, conn):
        self.conn = conn
    
    def _validate_table_config(self, table_type: str) -> dict:
        if table_type not in TABLE_CONFIGS:
            raise ValueError(f"Unsupported table type: {table_type}")
        return TABLE_CONFIGS[table_type]

    def bulk_insert(self, table_type: str, data_list: List[Dict], batch_size: int = 100) -> Dict:
        
        config = self._validate_table_config(table_type)
        city_cache = CityCache(self.conn)
        processor = DataProcessor(config, city_cache)
        
        try:
            processed_data, results = processor.prepare_data(data_list)
            if processed_data:
                self._execute_bulk_insert(config['sql'], processed_data, batch_size, results)
                results["inserted"] = len(processed_data)
                results["skipped"] = results["total"] - results["processed"]
            return results
        except Exception as e:
            self.conn.rollback()
            logger.exception("Bulk insert failed")
            raise RuntimeError(f"Bulk insert operation failed: {str(e)}")
    
    def _execute_bulk_insert(self, sql: str, data: List[List], batch_size: int, results: Dict):
        with self.conn.cursor() as cursor:
            execute_values(
                cursor,
                sql,
                data,
                page_size=batch_size
            )
            self.conn.commit()
            logger.info(f"Inserted {len(data)} records")

    def clean_old_forecasts(self, retention_days: int = 3) -> int:
        query = sql.SQL("""
        DELETE FROM forecast 
        WHERE forecast_time < NOW() - INTERVAL %s
        RETURNING 1;
        """)
        
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(query, (f"{retention_days} days",))
                deleted_count = cursor.rowcount
                self.conn.commit()
                return deleted_count
            except pg.Error as e:
                self.conn.rollback()
                raise RuntimeError(f"Failed to clean old forecasts: {e}")