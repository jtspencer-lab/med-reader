"""
Utility functions and helpers for MedDocReader application.
Common functions used across the application.
"""

import re
import os
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FileUtils:
    """Utility functions for file operations."""
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes."""
        try:
            return os.path.getsize(file_path)
        except OSError as e:
            logger.error(f"Error getting file size for {file_path}: {e}")
            return 0
    
    @staticmethod
    def is_supported_format(file_path: str, supported_formats: tuple) -> bool:
        """Check if file format is supported."""
        extension = Path(file_path).suffix.lower()
        return extension in supported_formats
    
    @staticmethod
    def create_directory(path: str) -> bool:
        """Create directory if it doesn't exist."""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")
            return False
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """Get a safe filename by removing/replacing invalid characters."""
        # Remove or replace invalid characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove multiple underscores
        safe_name = re.sub(r'_+', '_', safe_name)
        return safe_name.strip('_')


class TextUtils:
    """Utility functions for text processing."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    @staticmethod
    def extract_numbers(text: str) -> List[str]:
        """Extract all numbers from text."""
        return re.findall(r'\d+', text)
    
    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """Extract email addresses from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text, re.IGNORECASE)
    
    @staticmethod
    def extract_phones(text: str) -> List[str]:
        """Extract phone numbers from text."""
        phone_patterns = [
            r'\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})',
            r'(\d{3})[-.\s]?(\d{3})[-.\s]?(\d{4})',
            r'\+?1?[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})'
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 3:
                    phones.append(f"({match[0]}) {match[1]}-{match[2]}")
        
        return list(set(phones))  # Remove duplicates
    
    @staticmethod
    def extract_dates(text: str) -> List[str]:
        """Extract date patterns from text."""
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            r'\d{1,2}\s+\w+\s+\d{4}',
            r'\w+\s+\d{1,2},?\s+\d{4}'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))  # Remove duplicates


class ValidationUtils:
    """Utility functions for data validation."""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format."""
        if not email:
            return False
        
        email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Validate phone number format."""
        if not phone:
            return False
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        return len(digits) == 10 or len(digits) == 11
    
    @staticmethod
    def is_valid_date(date_str: str) -> bool:
        """Validate date format."""
        if not date_str:
            return False
        
        # Try to parse common date formats
        date_patterns = [
            r'^\d{1,2}/\d{1,2}/\d{2,4}$',
            r'^\d{4}-\d{1,2}-\d{1,2}$',
            r'^\d{1,2}-\d{1,2}-\d{2,4}$'
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, date_str):
                return True
        
        return False
    
    @staticmethod
    def is_valid_insurance_id(insurance_id: str) -> bool:
        """Validate insurance ID format."""
        if not insurance_id:
            return False
        
        # Basic validation - alphanumeric with possible hyphens
        pattern = r'^[A-Za-z0-9\-]+$'
        return bool(re.match(pattern, insurance_id)) and len(insurance_id) >= 3


class ResponseUtils:
    """Utility functions for API responses."""
    
    @staticmethod
    def success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
        """Create a success response."""
        response = {"success": True, "message": message}
        if data is not None:
            response["data"] = data
        return response
    
    @staticmethod
    def error_response(message: str, error_code: str = None, details: Any = None) -> Dict[str, Any]:
        """Create an error response."""
        response = {"success": False, "message": message}
        if error_code:
            response["error_code"] = error_code
        if details:
            response["details"] = details
        return response
    
    @staticmethod
    def paginated_response(data: List[Any], page: int, per_page: int, total: int) -> Dict[str, Any]:
        """Create a paginated response."""
        return {
            "success": True,
            "data": data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        }


class LoggingUtils:
    """Utility functions for logging."""
    
    @staticmethod
    def log_processing_start(document_id: int, filename: str):
        """Log the start of document processing."""
        logger.info(f"Starting processing for document {document_id}: {filename}")
    
    @staticmethod
    def log_processing_complete(document_id: int, filename: str, processing_time: float):
        """Log the completion of document processing."""
        logger.info(f"Completed processing for document {document_id}: {filename} (took {processing_time:.2f}s)")
    
    @staticmethod
    def log_processing_error(document_id: int, filename: str, error: str):
        """Log processing errors."""
        logger.error(f"Error processing document {document_id} ({filename}): {error}")
    
    @staticmethod
    def log_confidence_issues(document_id: int, low_confidence_fields: List[str]):
        """Log confidence issues for review."""
        logger.warning(f"Document {document_id} has low confidence fields: {', '.join(low_confidence_fields)}")

