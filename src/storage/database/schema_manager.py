import os
import sys
from psycopg2 import errors
from typing import List
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from src.storage.database.sql.creation import CREATION_QUERIES

logger = logging.getLogger(__name__)

class SchemaManager:
    TABLE_CREATION_QUERIES = CREATION_QUERIES

    @classmethod
    def create_tables(cls, conn):
        """Create all required tables"""
        for table_name, queries in cls.TABLE_CREATION_QUERIES.items():
            cls._execute_queries(conn, queries, f"Creating {table_name} table")

    @staticmethod
    def _execute_queries(conn, queries: List, context: str = ""):
        with conn.cursor() as cursor:
            for query in queries:
                try:
                    cursor.execute(query)
                except errors.DuplicateTable:
                    conn.rollback()
                    continue
            conn.commit()
        logger.info(f"Successfully executed {context}")