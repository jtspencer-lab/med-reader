"""
Repository pattern for data access operations.
Provides clean separation between business logic and data persistence.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.database import db_manager
from app.models import Document, PatientData, ProcessingStatus, ExtractedField


logger = logging.getLogger(__name__)


class DocumentRepository:
    """Repository for document-related database operations."""
    
    def create(self, document: Document) -> int:
        """Create a new document record."""
        query = """
        INSERT INTO documents (filename, file_path, file_size, mime_type, 
                             processing_status, extracted_text, processing_errors, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        params = (
            document.filename,
            document.file_path,
            document.file_size,
            document.mime_type,
            document.processing_status.value,
            document.extracted_text,
            document.processing_errors,
            document.metadata
        )
        
        result = db_manager.execute_query(query, params)
        return result[0]['id'] if result else None
    
    def get_by_id(self, document_id: int) -> Optional[Document]:
        """Get document by ID."""
        query = "SELECT * FROM documents WHERE id = %s"
        result = db_manager.execute_query(query, (document_id,))
        
        if not result:
            return None
        
        row = result[0]
        return self._row_to_document(row)
    
    def get_by_status(self, status: ProcessingStatus) -> List[Document]:
        """Get documents by processing status."""
        query = "SELECT * FROM documents WHERE processing_status = %s ORDER BY upload_date DESC"
        results = db_manager.execute_query(query, (status.value,))
        return [self._row_to_document(row) for row in results]
    
    def get_needing_review(self) -> List[Document]:
        """Get documents that need human review."""
        query = """
        SELECT d.* FROM documents d
        LEFT JOIN patients p ON d.id = p.document_id
        WHERE d.processing_status = 'needs_review'
        OR (p.name_confidence < 0.75 OR p.dob_confidence < 0.75 OR p.insurance_confidence < 0.75)
        ORDER BY d.upload_date DESC
        """
        results = db_manager.execute_query(query)
        return [self._row_to_document(row) for row in results]
    
    def update_status(self, document_id: int, status: ProcessingStatus, 
                     extracted_text: str = None, errors: List[str] = None) -> bool:
        """Update document processing status."""
        query = """
        UPDATE documents 
        SET processing_status = %s, extracted_text = %s, processing_errors = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        params = (status.value, extracted_text, errors, document_id)
        affected_rows = db_manager.execute_update(query, params)
        return affected_rows > 0
    
    def delete(self, document_id: int) -> bool:
        """Delete document and related records."""
        # Delete patient data first (foreign key constraint)
        patient_repo = PatientRepository()
        patient_repo.delete_by_document_id(document_id)
        
        # Delete document
        query = "DELETE FROM documents WHERE id = %s"
        affected_rows = db_manager.execute_update(query, (document_id,))
        return affected_rows > 0
    
    def _row_to_document(self, row: Dict[str, Any]) -> Document:
        """Convert database row to Document object."""
        return Document(
            id=row['id'],
            filename=row['filename'],
            file_path=row['file_path'],
            file_size=row['file_size'],
            mime_type=row['mime_type'],
            upload_date=row['upload_date'],
            processing_status=ProcessingStatus(row['processing_status']),
            extracted_text=row['extracted_text'] or "",
            processing_errors=row['processing_errors'] or [],
            metadata=row['metadata'] or {}
        )


class PatientRepository:
    """Repository for patient data operations."""
    
    def create(self, document_id: int, patient_data: PatientData) -> int:
        """Create patient record from extracted data."""
        query = """
        INSERT INTO patients (document_id, name, name_confidence, date_of_birth, dob_confidence,
                             insurance_id, insurance_confidence, address, address_confidence,
                             phone, phone_confidence, email, email_confidence)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        params = (
            document_id,
            patient_data.name.value,
            patient_data.name.confidence,
            patient_data.date_of_birth.value,
            patient_data.date_of_birth.confidence,
            patient_data.insurance_id.value,
            patient_data.insurance_id.confidence,
            patient_data.address.value,
            patient_data.address.confidence,
            patient_data.phone.value,
            patient_data.phone.confidence,
            patient_data.email.value,
            patient_data.email.confidence
        )
        
        result = db_manager.execute_query(query, params)
        return result[0]['id'] if result else None
    
    def get_by_document_id(self, document_id: int) -> Optional[PatientData]:
        """Get patient data by document ID."""
        query = "SELECT * FROM patients WHERE document_id = %s"
        result = db_manager.execute_query(query, (document_id,))
        
        if not result:
            return None
        
        row = result[0]
        return self._row_to_patient_data(row)
    
    def update(self, document_id: int, patient_data: PatientData) -> bool:
        """Update patient data."""
        query = """
        UPDATE patients 
        SET name = %s, name_confidence = %s, date_of_birth = %s, dob_confidence = %s,
            insurance_id = %s, insurance_confidence = %s, address = %s, address_confidence = %s,
            phone = %s, phone_confidence = %s, email = %s, email_confidence = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE document_id = %s
        """
        params = (
            patient_data.name.value,
            patient_data.name.confidence,
            patient_data.date_of_birth.value,
            patient_data.date_of_birth.confidence,
            patient_data.insurance_id.value,
            patient_data.insurance_id.confidence,
            patient_data.address.value,
            patient_data.address.confidence,
            patient_data.phone.value,
            patient_data.phone.confidence,
            patient_data.email.value,
            patient_data.email.confidence,
            document_id
        )
        
        affected_rows = db_manager.execute_update(query, params)
        return affected_rows > 0
    
    def delete_by_document_id(self, document_id: int) -> bool:
        """Delete patient data by document ID."""
        query = "DELETE FROM patients WHERE document_id = %s"
        affected_rows = db_manager.execute_update(query, (document_id,))
        return affected_rows > 0
    
    def _row_to_patient_data(self, row: Dict[str, Any]) -> PatientData:
        """Convert database row to PatientData object."""
        return PatientData(
            name=ExtractedField(
                value=row['name'],
                confidence=row['name_confidence'] or 0.0
            ),
            date_of_birth=ExtractedField(
                value=row['date_of_birth'],
                confidence=row['dob_confidence'] or 0.0
            ),
            insurance_id=ExtractedField(
                value=row['insurance_id'],
                confidence=row['insurance_confidence'] or 0.0
            ),
            address=ExtractedField(
                value=row['address'],
                confidence=row['address_confidence'] or 0.0
            ),
            phone=ExtractedField(
                value=row['phone'],
                confidence=row['phone_confidence'] or 0.0
            ),
            email=ExtractedField(
                value=row['email'],
                confidence=row['email_confidence'] or 0.0
            )
        )


class ProcessingLogRepository:
    """Repository for processing log operations."""
    
    def create_log(self, document_id: int, status: str, message: str = None,
                  processing_time: float = 0.0, confidence_score: float = 0.0) -> int:
        """Create a processing log entry."""
        query = """
        INSERT INTO processing_logs (document_id, status, message, processing_time, confidence_score)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """
        params = (document_id, status, message, processing_time, confidence_score)
        result = db_manager.execute_query(query, params)
        return result[0]['id'] if result else None
    
    def get_logs_by_document(self, document_id: int) -> List[Dict[str, Any]]:
        """Get processing logs for a document."""
        query = """
        SELECT * FROM processing_logs 
        WHERE document_id = %s 
        ORDER BY created_at DESC
        """
        return db_manager.execute_query(query, (document_id,))

