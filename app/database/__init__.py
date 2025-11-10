"""
Database connection and management for MedDocReader.
Handles PostgreSQL connections and provides database utilities.
"""

import psycopg2
import psycopg2.extras
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
from app.config import db_config


logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self):
        self.connection_string = db_config.connection_string
        self._connection: Optional[psycopg2.extensions.connection] = None
    
    def connect(self) -> psycopg2.extensions.connection:
        """Establish database connection."""
        try:
            if self._connection is None or self._connection.closed:
                self._connection = psycopg2.connect(
                    self.connection_string,
                    cursor_factory=psycopg2.extras.RealDictCursor
                )
                logger.info("Database connection established successfully.")
            return self._connection
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def disconnect(self):
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("Database connection closed.")
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows."""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def health_check(self) -> bool:
        """Check if database is accessible."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


def init_database():
    """Initialize database tables if they don't exist."""
    create_tables_sql = """
    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(255) NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        mime_type VARCHAR(100),
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processing_status VARCHAR(20) DEFAULT 'pending',
        extracted_text TEXT,
        processing_errors TEXT[],
        metadata JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS patients (
        id SERIAL PRIMARY KEY,
        document_id INTEGER REFERENCES documents(id),
        name VARCHAR(255),
        name_confidence FLOAT,
        date_of_birth DATE,
        dob_confidence FLOAT,
        insurance_id VARCHAR(100),
        insurance_confidence FLOAT,
        address TEXT,
        address_confidence FLOAT,
        phone VARCHAR(20),
        phone_confidence FLOAT,
        email VARCHAR(255),
        email_confidence FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS processing_logs (
        id SERIAL PRIMARY KEY,
        document_id INTEGER REFERENCES documents(id),
        status VARCHAR(20) NOT NULL,
        message TEXT,
        processing_time FLOAT,
        confidence_score FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(processing_status);
    CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date);
    CREATE INDEX IF NOT EXISTS idx_patients_document_id ON patients(document_id);
    """
    
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(create_tables_sql)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        raise

