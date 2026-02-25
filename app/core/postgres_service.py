import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

load_dotenv()


class PostgresService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PostgresService, cls).__new__(cls)
            cls._instance._initialize_pool()
        return cls._instance

    def _initialize_pool(self):
        """create connection pool"""
        self.db_config = {
            "host": os.environ.get("DB_HOST", "localhost"),
            "port": os.environ.get("DB_PORT", 5433),
            "database": os.environ.get("DB_NAME", "property_db"),
            "user": os.environ.get("DB_USER", "property_user"),
            "password": os.environ.get("DB_PASSWORD", ""),
        }

    @contextmanager
    def get_connection(self):
        """Context manager for managing connections"""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
            yield conn
        except Exception as e:
            print(f"Connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def insert(self, table: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Insert new record"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['%s'] * len(data))
                query = f"""
                    INSERT INTO {table} ({columns})
                    VALUES ({placeholders})
                    RETURNING *
                """
                cursor.execute(query, list(data.values()))
                result = cursor.fetchall()
                conn.commit()
                return result

    def select(self, table: str, columns: str = "*", filters: Dict[str, Any] = None,
               limit: int = None, offset: int = None, order_by: str = None) -> List[Dict[str, Any]]:
        """read new records"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                where_clause = ""
                params = []
                if filters:
                    conditions = [f"{k} = %s" for k in filters.keys()]
                    params = list(filters.values())
                    where_clause = "WHERE " + " AND ".join(conditions)

                query = f"SELECT {columns} FROM {table} {where_clause}"
                if order_by:
                    query += f" ORDER BY {order_by}"
                if limit is not None:
                    query += f" LIMIT {limit}"
                    if offset is not None:
                        query += f" OFFSET {offset}"

                cursor.execute(query, params)
                return cursor.fetchall()

    def update(self, table: str, property_id: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Update record"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
                query = f"""
                    UPDATE {table}
                    SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING *
                """
                params = list(data.values()) + [property_id]
                cursor.execute(query, params)
                result = cursor.fetchall()
                conn.commit()
                return result

    def delete(self, table: str, property_id: str) -> bool:
        """Delete record"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                query = f"DELETE FROM {table} WHERE id = %s"
                cursor.execute(query, (property_id,))
                conn.commit()
                return cursor.rowcount > 0

    def execute_raw(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute raw query"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                if query.strip().upper().startswith("SELECT"):
                    return cursor.fetchall()
                conn.commit()
                return []

    def test_connection(self) -> bool:
        """Test database connection"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 AS ok;")
                result = cursor.fetchone()
                return result["ok"] == 1


# create instance from postgres service
postgres_service = PostgresService()
