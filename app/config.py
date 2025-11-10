"""
Configuration management for MedDocReader application.
Handles environment variables and application settings.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    name: str = os.getenv('DB_NAME', 'healthcare_db')
    user: str = os.getenv('DB_USER', 'db_user')
    password: str = os.getenv('DB_PASSWORD', 'db_pass')
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass
class AzureConfig:
    """Azure services configuration."""
    form_recognizer_endpoint: str = os.getenv(
        'AZURE_FORM_RECOGNIZER_ENDPOINT', 
        'https://<your-form-recognizer-endpoint>.cognitiveservices.azure.com/'
    )
    form_recognizer_key: str = os.getenv('AZURE_FORM_RECOGNIZER_KEY', '<your-form-recognizer-key>')
    blob_connection_string: str = os.getenv('AZURE_BLOB_CONNECTION_STRING', '<your-blob-connection-string>')


@dataclass
class NLPConfig:
    """NLP processing configuration."""
    model_name: str = os.getenv('SPACY_MODEL', 'en_core_web_sm')
    confidence_threshold: float = float(os.getenv('CONFIDENCE_THRESHOLD', '0.75'))


@dataclass
class AppConfig:
    """Main application configuration."""
    debug: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    secret_key: str = os.getenv('SECRET_KEY', 'your-secret-key-here')
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_file: str = os.getenv('LOG_FILE', 'processing.log')
    
    # File processing settings
    supported_formats: tuple = ('.jpg', '.jpeg', '.png', '.tiff', '.pdf')
    batch_size: int = int(os.getenv('BATCH_SIZE', '10'))
    
    # Web interface settings
    host: str = os.getenv('HOST', '0.0.0.0')
    port: int = int(os.getenv('PORT', '8000'))


# Global configuration instance
config = AppConfig()
db_config = DatabaseConfig()
azure_config = AzureConfig()
nlp_config = NLPConfig()

