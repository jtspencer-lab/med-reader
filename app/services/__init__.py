"""
Service layer for MedDocReader application.
Contains business logic for document processing, NLP analysis, and data management.
"""

import os
import time
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import spacy

from app.config import azure_config, nlp_config, config
from app.models import Document, PatientData, ExtractedField, ProcessingStatus, ProcessingResult
from app.database.repositories import DocumentRepository, PatientRepository, ProcessingLogRepository


logger = logging.getLogger(__name__)


class AzureFormRecognizerService:
    """Service for Azure Form Recognizer operations."""
    
    def __init__(self):
        self.client = DocumentAnalysisClient(
            endpoint=azure_config.form_recognizer_endpoint,
            credential=AzureKeyCredential(azure_config.form_recognizer_key)
        )
    
    def extract_text_from_document(self, file_path: str) -> Optional[str]:
        """Extract text from document using Azure Form Recognizer."""
        try:
            with open(file_path, "rb") as f:
                poller = self.client.begin_analyze_document("prebuilt-document", document=f)
                result = poller.result()
                
                # Combine all text lines from all pages
                text_lines = []
                for page in result.pages:
                    for line in page.lines:
                        text_lines.append(line.content)
                
                extracted_text = " ".join(text_lines)
                logger.info(f"Successfully extracted text from {file_path}")
                return extracted_text
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return None


class NLPService:
    """Service for NLP processing using spaCy."""
    
    def __init__(self):
        try:
            self.nlp = spacy.load(nlp_config.model_name)
            logger.info(f"SpaCy model '{nlp_config.model_name}' loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SpaCy model: {e}")
            raise
    
    def extract_patient_data(self, text: str) -> PatientData:
        """Extract patient information from text using NLP."""
        try:
            doc = self.nlp(text)
            patient_data = PatientData()
            
            # Extract entities
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    patient_data.name = ExtractedField(
                        value=ent.text.strip(),
                        confidence=0.8,
                        raw_text=ent.text
                    )
                elif ent.label_ == "DATE":
                    # Clean date format
                    cleaned_date = self._clean_date(ent.text)
                    patient_data.date_of_birth = ExtractedField(
                        value=cleaned_date,
                        confidence=0.7,
                        raw_text=ent.text
                    )
            
            # Extract insurance information using pattern matching
            insurance_info = self._extract_insurance_info(text)
            if insurance_info:
                patient_data.insurance_id = ExtractedField(
                    value=insurance_info,
                    confidence=0.6,
                    raw_text=insurance_info
                )
            
            # Extract contact information
            phone = self._extract_phone(text)
            if phone:
                patient_data.phone = ExtractedField(
                    value=phone,
                    confidence=0.7,
                    raw_text=phone
                )
            
            email = self._extract_email(text)
            if email:
                patient_data.email = ExtractedField(
                    value=email,
                    confidence=0.9,
                    raw_text=email
                )
            
            logger.info("Successfully extracted patient data using NLP")
            return patient_data
            
        except Exception as e:
            logger.error(f"Error during NLP processing: {e}")
            return PatientData()
    
    def _clean_date(self, date_text: str) -> str:
        """Clean and format date text."""
        import re
        # Remove non-numeric characters except hyphens and slashes
        cleaned = re.sub(r"[^0-9\-/]", "", date_text)
        return cleaned
    
    def _extract_insurance_info(self, text: str) -> Optional[str]:
        """Extract insurance information using pattern matching."""
        import re
        patterns = [
            r"insurance\s*[#:]?\s*([A-Z0-9\-]+)",
            r"policy\s*[#:]?\s*([A-Z0-9\-]+)",
            r"member\s*id\s*[#:]?\s*([A-Z0-9\-]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number using pattern matching."""
        import re
        phone_pattern = r"\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})"
        match = re.search(phone_pattern, text)
        if match:
            return f"({match.group(1)}) {match.group(2)}-{match.group(3)}"
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address using pattern matching."""
        import re
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        match = re.search(email_pattern, text)
        return match.group(0) if match else None


class DocumentProcessingService:
    """Main service for document processing workflow."""
    
    def __init__(self):
        self.azure_service = AzureFormRecognizerService()
        self.nlp_service = NLPService()
        self.document_repo = DocumentRepository()
        self.patient_repo = PatientRepository()
        self.log_repo = ProcessingLogRepository()
    
    def process_document(self, file_path: str) -> ProcessingResult:
        """Process a single document through the complete workflow."""
        start_time = time.time()
        
        try:
            # Create document record
            document = self._create_document_from_file(file_path)
            document_id = self.document_repo.create(document)
            document.id = document_id
            
            # Update status to processing
            self.document_repo.update_status(document_id, ProcessingStatus.PROCESSING)
            self.log_repo.create_log(document_id, "processing", "Started document processing")
            
            # Extract text using Azure Form Recognizer
            extracted_text = self.azure_service.extract_text_from_document(file_path)
            if not extracted_text or extracted_text.strip() == "":
                raise Exception("No text extracted from document")
            
            # Update document with extracted text
            self.document_repo.update_status(
                document_id, 
                ProcessingStatus.PROCESSING, 
                extracted_text=extracted_text
            )
            
            # Extract patient data using NLP
            patient_data = self.nlp_service.extract_patient_data(extracted_text)
            
            # Save patient data
            self.patient_repo.create(document_id, patient_data)
            
            # Determine final status
            processing_time = time.time() - start_time
            confidence_score = self._calculate_overall_confidence(patient_data)
            
            if patient_data.get_low_confidence_fields():
                final_status = ProcessingStatus.NEEDS_REVIEW
                message = "Document processed but needs human review for low-confidence fields"
            else:
                final_status = ProcessingStatus.COMPLETED
                message = "Document processed successfully"
            
            # Update final status
            self.document_repo.update_status(document_id, final_status, extracted_text)
            self.log_repo.create_log(
                document_id, 
                final_status.value, 
                message, 
                processing_time, 
                confidence_score
            )
            
            return ProcessingResult(
                document_id=document_id,
                success=True,
                extracted_data=patient_data,
                processing_time=processing_time,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_message = f"Error processing document: {str(e)}"
            logger.error(error_message)
            
            if document_id:
                self.document_repo.update_status(
                    document_id, 
                    ProcessingStatus.FAILED, 
                    errors=[error_message]
                )
                self.log_repo.create_log(document_id, "failed", error_message, processing_time)
            
            return ProcessingResult(
                document_id=document_id or 0,
                success=False,
                errors=[error_message],
                processing_time=processing_time
            )
    
    def process_batch(self, folder_path: str) -> List[ProcessingResult]:
        """Process multiple documents from a folder."""
        results = []
        folder = Path(folder_path)
        
        if not folder.exists():
            raise ValueError(f"Folder path does not exist: {folder_path}")
        
        # Get all supported files
        supported_files = []
        for ext in config.supported_formats:
            supported_files.extend(folder.glob(f"*{ext}"))
            supported_files.extend(folder.glob(f"*{ext.upper()}"))
        
        logger.info(f"Found {len(supported_files)} files to process")
        
        for file_path in supported_files:
            try:
                result = self.process_document(str(file_path))
                results.append(result)
                logger.info(f"Processed {file_path.name}: {result.success}")
            except Exception as e:
                logger.error(f"Failed to process {file_path.name}: {e}")
                results.append(ProcessingResult(
                    document_id=0,
                    success=False,
                    errors=[str(e)]
                ))
        
        return results
    
    def get_documents_needing_review(self) -> List[Document]:
        """Get all documents that need human review."""
        return self.document_repo.get_needing_review()
    
    def update_patient_data(self, document_id: int, patient_data: PatientData) -> bool:
        """Update patient data after human review."""
        try:
            success = self.patient_repo.update(document_id, patient_data)
            if success:
                # Update document status to completed
                self.document_repo.update_status(document_id, ProcessingStatus.COMPLETED)
                self.log_repo.create_log(
                    document_id, 
                    "completed", 
                    "Patient data updated after human review"
                )
            return success
        except Exception as e:
            logger.error(f"Error updating patient data: {e}")
            return False
    
    def _create_document_from_file(self, file_path: str) -> Document:
        """Create Document object from file."""
        path = Path(file_path)
        stat = path.stat()
        
        return Document(
            filename=path.name,
            file_path=str(path.absolute()),
            file_size=stat.st_size,
            mime_type=self._get_mime_type(path.suffix),
            processing_status=ProcessingStatus.PENDING
        )
    
    def _get_mime_type(self, extension: str) -> str:
        """Get MIME type from file extension."""
        mime_types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.tiff': 'image/tiff'
        }
        return mime_types.get(extension.lower(), 'application/octet-stream')
    
    def _calculate_overall_confidence(self, patient_data: PatientData) -> float:
        """Calculate overall confidence score for patient data."""
        fields = [
            patient_data.name.confidence,
            patient_data.date_of_birth.confidence,
            patient_data.insurance_id.confidence,
            patient_data.address.confidence,
            patient_data.phone.confidence,
            patient_data.email.confidence
        ]
        
        # Calculate average confidence, excluding zero values
        valid_confidences = [c for c in fields if c > 0]
        return sum(valid_confidences) / len(valid_confidences) if valid_confidences else 0.0

