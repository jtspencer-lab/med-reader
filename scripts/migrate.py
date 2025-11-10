"""
Migration script to help transition from old structure to new structure.
This script demonstrates how to use the new organized code.
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services import DocumentProcessingService
from app.database import init_database
from app.config import config


def migrate_old_code():
    """Demonstrate how to use the new organized code structure."""
    
    print("MedDocReader - Migration to New Structure")
    print("=" * 50)
    
    # Initialize database
    print("1. Initializing database...")
    try:
        init_database()
        print("   ✓ Database initialized successfully")
    except Exception as e:
        print(f"   ✗ Database initialization failed: {e}")
        return False
    
    # Initialize processing service
    print("2. Initializing processing service...")
    try:
        processing_service = DocumentProcessingService()
        print("   ✓ Processing service initialized successfully")
    except Exception as e:
        print(f"   ✗ Service initialization failed: {e}")
        return False
    
    # Check for old files
    print("3. Checking for old files...")
    old_files = ["Src/DocReader.py", "Src/AzureDocReader.py", "Src/MedDocReader.py", "Src/DocumentWebUI.py"]
    
    for old_file in old_files:
        if os.path.exists(old_file):
            print(f"   ⚠ Found old file: {old_file}")
        else:
            print(f"   ✓ Old file not found: {old_file}")
    
    print("\n4. New structure benefits:")
    print("   ✓ Separated concerns (models, services, database, web)")
    print("   ✓ Configuration management")
    print("   ✓ Proper error handling and logging")
    print("   ✓ Database connection management")
    print("   ✓ RESTful API endpoints")
    print("   ✓ Web interface with templates")
    print("   ✓ Docker support")
    print("   ✓ Testing framework")
    
    print("\n5. Usage examples:")
    print("   # Process a single document:")
    print("   result = processing_service.process_document('path/to/document.pdf')")
    print("   ")
    print("   # Process batch of documents:")
    print("   results = processing_service.process_batch('path/to/folder')")
    print("   ")
    print("   # Get documents needing review:")
    print("   documents = processing_service.get_documents_needing_review()")
    
    print("\n6. Next steps:")
    print("   ✓ Update your .env file with proper configuration")
    print("   ✓ Run: python app/main.py")
    print("   ✓ Access web interface at http://localhost:8000")
    print("   ✓ Remove old files when ready")
    
    return True


if __name__ == "__main__":
    success = migrate_old_code()
    if success:
        print("\n✓ Migration guide completed successfully!")
    else:
        print("\n✗ Migration encountered errors. Please check configuration.")

