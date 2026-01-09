import os
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def _build_connection_string() -> str:
    server = os.getenv('SQL_SERVER')
    database = os.getenv('SQL_DATABASE')
    username = os.getenv('SQL_USERNAME')
    password = os.getenv('SQL_PASSWORD')
    encrypt = os.getenv('SQL_ENCRYPT', 'true')
    driver = os.getenv('SQL_DRIVER', 'ODBC Driver 18 for SQL Server')
    return (
        f"mssql+pyodbc://{username}:{password}@{server}:1433/{database}?"
        f"driver={driver.replace(' ', '+')}&Encrypt={encrypt}&TrustServerCertificate=no"
    )


_ENGINE: Optional[Engine] = None


def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        try:
            _ENGINE = create_engine(_build_connection_string(), pool_pre_ping=True)
        except Exception as e:
            # Lazy initialization - only create engine when actually needed
            # This prevents crashes during module import
            import logging
            logging.warning(f"Failed to create SQL engine: {e}")
            raise
    return _ENGINE


def query_all(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]


def execute(sql: str, params: Optional[Dict[str, Any]] = None) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})



