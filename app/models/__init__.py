"""
Data models for MedDocReader application.
Defines the structure for documents, patients, and processing results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class ProcessingStatus(Enum):
    """Status of document processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class ConfidenceLevel(Enum):
    """Confidence levels for extracted data."""
    HIGH = "high"      # >= 0.8
    MEDIUM = "medium"  # 0.5 - 0.79
    LOW = "low"        # < 0.5


@dataclass
class ExtractedField:
    """Represents an extracted field with confidence score."""
    value: Optional[str] = None
    confidence: float = 0.0
    raw_text: Optional[str] = None
    
    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Get confidence level based on score."""
        if self.confidence >= 0.8:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    @property
    def needs_review(self) -> bool:
        """Check if field needs human review."""
        return self.confidence < 0.75


@dataclass
class PatientData:
    """Patient information extracted from documents."""
    name: ExtractedField = field(default_factory=ExtractedField)
    date_of_birth: ExtractedField = field(default_factory=ExtractedField)
    insurance_id: ExtractedField = field(default_factory=ExtractedField)
    address: ExtractedField = field(default_factory=ExtractedField)
    phone: ExtractedField = field(default_factory=ExtractedField)
    email: ExtractedField = field(default_factory=ExtractedField)
    
    def get_low_confidence_fields(self) -> Dict[str, ExtractedField]:
        """Get fields that need human review."""
        fields = {
            'name': self.name,
            'date_of_birth': self.date_of_birth,
            'insurance_id': self.insurance_id,
            'address': self.address,
            'phone': self.phone,
            'email': self.email
        }
        return {k: v for k, v in fields.items() if v.needs_review}


@dataclass
class Document:
    """Represents a medical document."""
    id: Optional[int] = None
    filename: str = ""
    file_path: str = ""
    file_size: int = 0
    mime_type: str = ""
    upload_date: datetime = field(default_factory=datetime.now)
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    extracted_text: str = ""
    patient_data: PatientData = field(default_factory=PatientData)
    processing_errors: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def needs_review(self) -> bool:
        """Check if document needs human review."""
        return (
            self.processing_status == ProcessingStatus.NEEDS_REVIEW or
            bool(self.patient_data.get_low_confidence_fields())
        )
    
    @property
    def is_processed(self) -> bool:
        """Check if document processing is complete."""
        return self.processing_status in [ProcessingStatus.COMPLETED, ProcessingStatus.NEEDS_REVIEW]


@dataclass
class ProcessingResult:
    """Result of document processing operation."""
    document_id: int
    success: bool
    extracted_data: Optional[PatientData] = None
    errors: list = field(default_factory=list)
    processing_time: float = 0.0
    confidence_score: float = 0.0
    
    @property
    def overall_confidence(self) -> float:
        """Calculate overall confidence score."""
        if not self.extracted_data:
            return 0.0
        
        fields = [
            self.extracted_data.name.confidence,
            self.extracted_data.date_of_birth.confidence,
            self.extracted_data.insurance_id.confidence,
            self.extracted_data.address.confidence,
            self.extracted_data.phone.confidence,
            self.extracted_data.email.confidence
        ]
        
        # Calculate average confidence, excluding None values
        valid_confidences = [c for c in fields if c > 0]
        return sum(valid_confidences) / len(valid_confidences) if valid_confidences else 0.0

