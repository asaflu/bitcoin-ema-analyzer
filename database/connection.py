"""
Database connection management supporting both SQLite and PostgreSQL.
Automatically detects environment and uses appropriate database.
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Try to import PostgreSQL and Streamlit (optional)
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

from config import DATABASE_PATH, DB_PRAGMAS


class DatabaseConnection:
    """
    Universal database connection factory.
    Supports both SQLite (local) and PostgreSQL (cloud).
    """

    def __init__(self, db_path=None):
        """
        Initialize database connection factory.
        Auto-detects database type from environment.
        """
        self.db_path = Path(db_path) if db_path else DATABASE_PATH
        self.db_type = self._detect_database_type()
        self.postgres_url = self._get_postgres_url()

    def _detect_database_type(self):
        """Detect which database to use."""
        # Check Streamlit secrets first
        if STREAMLIT_AVAILABLE:
            try:
                if hasattr(st, 'secrets') and 'database' in st.secrets:
                    if 'url' in st.secrets['database']:
                        return 'postgresql'
            except:
                pass

        # Check environment variable
        if os.getenv('DATABASE_URL'):
            return 'postgresql'

        # Check if PostgreSQL config exists
        if os.getenv('POSTGRES_HOST'):
            return 'postgresql'

        # Default to SQLite
        return 'sqlite'

    def _get_postgres_url(self):
        """Get PostgreSQL connection URL from various sources."""
        # Try Streamlit secrets
        if STREAMLIT_AVAILABLE:
            try:
                if hasattr(st, 'secrets') and 'database' in st.secrets:
                    if 'url' in st.secrets['database']:
                        return st.secrets['database']['url']
            except:
                pass

        # Try environment variable
        if os.getenv('DATABASE_URL'):
            return os.getenv('DATABASE_URL')

        # Try individual PostgreSQL env vars
        if os.getenv('POSTGRES_HOST'):
            host = os.getenv('POSTGRES_HOST')
            port = os.getenv('POSTGRES_PORT', '5432')
            database = os.getenv('POSTGRES_DATABASE', 'bitcoin')
            user = os.getenv('POSTGRES_USER')
            password = os.getenv('POSTGRES_PASSWORD')
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"

        return None

    def get_connection(self):
        """
        Create and configure a database connection.
        Returns appropriate connection based on detected database type.
        """
        if self.db_type == 'postgresql':
            if not POSTGRES_AVAILABLE:
                raise ImportError("psycopg2 not installed. Install with: pip install psycopg2-binary")

            if not self.postgres_url:
                raise ValueError("PostgreSQL URL not found in environment or Streamlit secrets")

            return psycopg2.connect(self.postgres_url)

        else:  # sqlite
            conn = sqlite3.connect(str(self.db_path))

            # Apply pragma optimizations for SQLite
            cursor = conn.cursor()
            for pragma, value in DB_PRAGMAS.items():
                cursor.execute(f"PRAGMA {pragma} = {value}")
            cursor.execute("PRAGMA foreign_keys = ON")

            return conn

    @contextmanager
    def connection(self):
        """
        Context manager for database connections.
        Works with both SQLite and PostgreSQL.
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
        """Context manager for database cursor."""
        with self.connection() as conn:
            cursor = conn.cursor()
            yield cursor

    def get_db_info(self):
        """Get information about current database configuration."""
        return {
            'type': self.db_type,
            'path': str(self.db_path) if self.db_type == 'sqlite' else None,
            'url': self.postgres_url if self.db_type == 'postgresql' else None,
            'postgres_available': POSTGRES_AVAILABLE,
            'streamlit_available': STREAMLIT_AVAILABLE
        }


# Global connection factory instance
db = DatabaseConnection()
