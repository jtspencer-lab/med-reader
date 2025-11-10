"""
Main application entry point for MedDocReader.
Initializes the application and sets up logging.
"""

import logging
import sys
from pathlib import Path

from app.config import config
from app.database import init_database
from app.web.routes import app


def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def create_app():
    """Create and configure the FastAPI application."""
    # Setup logging
    setup_logging()
    
    # Initialize database
    init_database()
    
    # Create necessary directories
    Path("uploads").mkdir(exist_ok=True)
    Path("app/web/templates").mkdir(parents=True, exist_ok=True)
    Path("app/web/static").mkdir(parents=True, exist_ok=True)
    
    return app


if __name__ == "__main__":
    app_instance = create_app()
    
    import uvicorn
    uvicorn.run(
        app_instance,
        host=config.host,
        port=config.port,
        reload=config.debug
    )

