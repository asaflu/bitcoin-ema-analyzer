"""
Database connection management with context managers.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from config import DATABASE_PATH, DB_PRAGMAS


class DatabaseConnection:
    """
    Database connection factory with optimized settings.
    """

    def __init__(self, db_path=None):
        """
        Initialize database connection factory.

        Args:
            db_path: Path to SQLite database file (default: from config)
        """
        self.db_path = Path(db_path) if db_path else DATABASE_PATH

    def get_connection(self):
        """
        Create and configure a database connection.

        Returns:
            sqlite3.Connection with optimized pragmas
        """
        conn = sqlite3.connect(str(self.db_path))

        # Apply pragma optimizations
        cursor = conn.cursor()
        for pragma, value in DB_PRAGMAS.items():
            cursor.execute(f"PRAGMA {pragma} = {value}")

        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        return conn

    @contextmanager
    def connection(self):
        """
        Context manager for database connections.
        Automatically commits on success and rolls back on error.

        Yields:
            sqlite3.Connection
        """
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @contextmanager
    def cursor(self):
        """
        Context manager for database cursor.
        Automatically handles connection lifecycle.

        Yields:
            sqlite3.Cursor
        """
        with self.connection() as conn:
            yield conn.cursor()


# Global connection factory instance
db = DatabaseConnection()
