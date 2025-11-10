"""
Web interface routes for MedDocReader application.
Provides FastAPI endpoints for document upload, review, and management.
"""

from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import os
import logging

from app.config import config
from app.services import DocumentProcessingService
from app.models import ProcessingStatus
from app.database.repositories import DocumentRepository, PatientRepository


logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MedDocReader",
    description="Medical Document Processing System",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="app/web/templates")

# Initialize services
processing_service = DocumentProcessingService()
document_repo = DocumentRepository()
patient_repo = PatientRepository()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard showing processing status and documents needing review."""
    try:
        # Get documents needing review
        documents_needing_review = processing_service.get_documents_needing_review()
        
        # Get recent documents
        recent_documents = document_repo.get_by_status(ProcessingStatus.COMPLETED)[:10]
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "documents_needing_review": documents_needing_review,
            "recent_documents": recent_documents
        })
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Document upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...)
):
    """Handle document upload and processing."""
    try:
        # Validate file type
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in config.supported_formats:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported formats: {config.supported_formats}"
            )
        
        # Save uploaded file
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process document
        result = processing_service.process_document(file_path)
        
        if result.success:
            return RedirectResponse(url=f"/document/{result.document_id}", status_code=303)
        else:
            raise HTTPException(status_code=500, detail=f"Processing failed: {result.errors}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/document/{document_id}", response_class=HTMLResponse)
async def view_document(request: Request, document_id: int):
    """View document details and extracted data."""
    try:
        document = document_repo.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        patient_data = patient_repo.get_by_document_id(document_id)
        
        return templates.TemplateResponse("document_detail.html", {
            "request": request,
            "document": document,
            "patient_data": patient_data
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/review", response_class=HTMLResponse)
async def review_page(request: Request):
    """Page showing all documents needing review."""
    try:
        documents = processing_service.get_documents_needing_review()
        return templates.TemplateResponse("review.html", {
            "request": request,
            "documents": documents
        })
    except Exception as e:
        logger.error(f"Error loading review page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/review/{document_id}", response_class=HTMLResponse)
async def review_document(request: Request, document_id: int):
    """Review and edit document data."""
    try:
        document = document_repo.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        patient_data = patient_repo.get_by_document_id(document_id)
        
        return templates.TemplateResponse("review_edit.html", {
            "request": request,
            "document": document,
            "patient_data": patient_data
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading review page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/review/{document_id}")
async def update_reviewed_data(
    document_id: int,
    name: str = Form(...),
    date_of_birth: str = Form(...),
    insurance_id: str = Form(...),
    address: str = Form(""),
    phone: str = Form(""),
    email: str = Form("")
):
    """Update reviewed patient data."""
    try:
        from app.models import PatientData, ExtractedField
        
        # Create updated patient data with high confidence
        updated_data = PatientData(
            name=ExtractedField(value=name, confidence=1.0),
            date_of_birth=ExtractedField(value=date_of_birth, confidence=1.0),
            insurance_id=ExtractedField(value=insurance_id, confidence=1.0),
            address=ExtractedField(value=address, confidence=1.0),
            phone=ExtractedField(value=phone, confidence=1.0),
            email=ExtractedField(value=email, confidence=1.0)
        )
        
        success = processing_service.update_patient_data(document_id, updated_data)
        
        if success:
            return RedirectResponse(url="/", status_code=303)
        else:
            raise HTTPException(status_code=500, detail="Failed to update patient data")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating reviewed data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/documents", response_class=JSONResponse)
async def api_get_documents():
    """API endpoint to get all documents."""
    try:
        documents = document_repo.get_by_status(ProcessingStatus.COMPLETED)
        return {"documents": [{"id": d.id, "filename": d.filename, "upload_date": d.upload_date} for d in documents]}
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/documents/{document_id}", response_class=JSONResponse)
async def api_get_document(document_id: int):
    """API endpoint to get specific document data."""
    try:
        document = document_repo.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        patient_data = patient_repo.get_by_document_id(document_id)
        
        return {
            "document": {
                "id": document.id,
                "filename": document.filename,
                "status": document.processing_status.value,
                "upload_date": document.upload_date
            },
            "patient_data": {
                "name": patient_data.name.value if patient_data else None,
                "date_of_birth": patient_data.date_of_birth.value if patient_data else None,
                "insurance_id": patient_data.insurance_id.value if patient_data else None
            } if patient_data else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/process-batch")
async def api_process_batch(folder_path: str = Form(...)):
    """API endpoint to process a batch of documents."""
    try:
        results = processing_service.process_batch(folder_path)
        return {
            "success": True,
            "processed_count": len(results),
            "successful_count": sum(1 for r in results if r.success),
            "results": [{"success": r.success, "errors": r.errors} for r in results]
        }
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.host, port=config.port)

