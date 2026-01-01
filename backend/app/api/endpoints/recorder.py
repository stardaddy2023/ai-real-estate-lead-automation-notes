"""
Pima County Recorder API Endpoints

Exposes recorder document search, download, and extraction functionality
to the frontend via FastAPI endpoints.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path
import asyncio
import os
import sys

# Add mcp_servers path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "mcp_servers" / "recorder"))
from session import RecorderSession

router = APIRouter()

# Singleton session manager
_session: Optional[RecorderSession] = None
_session_lock = asyncio.Lock()


class SessionStatus(BaseModel):
    initialized: bool
    needs_captcha: bool
    ready: bool
    message: str


class DocumentResult(BaseModel):
    doc_id: str
    doc_number: str
    doc_type: str
    record_date: str


class SearchResponse(BaseModel):
    results: List[DocumentResult]
    total: int
    doc_type: str


class DownloadResponse(BaseModel):
    success: bool
    doc_id: str
    file_path: Optional[str] = None
    error: Optional[str] = None


class ExtractResponse(BaseModel):
    success: bool
    doc_id: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


async def get_session() -> RecorderSession:
    """Get or create the singleton recorder session."""
    global _session
    async with _session_lock:
        if _session is None:
            _session = RecorderSession()
        return _session


@router.get("/status", response_model=SessionStatus)
async def get_status():
    """Get current recorder session status."""
    global _session
    # Don't use lock here - just check current state
    is_initialized = _session is not None and _session.initialized
    
    return SessionStatus(
        initialized=is_initialized,
        needs_captcha=False,
        ready=is_initialized,
        message="Session ready" if is_initialized else "Session not initialized. Click Search to initialize."
    )


@router.post("/initialize")
async def initialize_session():
    """
    Initialize the browser session.
    Note: This will open a browser window that requires manual CAPTCHA solving.
    Call /status to check when the session is ready.
    """
    session = await get_session()
    
    if session.initialized:
        return {"success": True, "message": "Session already initialized"}
    
    # Start initialization in background (browser will open)
    success = await session.initialize()
    
    if success:
        return {"success": True, "message": "Session initialized successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to initialize session")


@router.delete("/session")
async def close_session():
    """Close the browser session."""
    global _session
    async with _session_lock:
        if _session and _session.initialized:
            await _session.close()
        _session = None
    return {"success": True, "message": "Session closed"}


# Document type mapping for search
DOC_TYPE_MAP = {
    "lis": "LIS PENDENS",
    "nots": "NOTICE SALE",
    "sub": "SUBSTITUTION TRUSTEE",
    "federal": "FEDERAL LIEN",
    "city": "CITY LIEN",
    "lien": "LIEN",
    "mechanic": "MECHANICS LIEN",
    "notice": "NOTICE LIEN",
    "judgment": "JUDGMENT",
    "absjudge": "ABSTRACT JUDGMENT",
    "divorce": "DISSOLUTION MARRIAGE",
    "probate": "AFFIDAVIT SUCCESSION",
}


@router.get("/search/{doc_type}", response_model=SearchResponse)
async def search_documents(doc_type: str, limit: int = 100):
    """
    Search for documents by type.
    Will auto-initialize browser session if not already initialized.
    
    doc_type options: lis, nots, sub, federal, city, lien, mechanic, notice, judgment, absjudge, divorce, probate
    """
    if doc_type not in DOC_TYPE_MAP:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid doc_type. Must be one of: {', '.join(DOC_TYPE_MAP.keys())}"
        )
    
    session = await get_session()
    
    # Auto-initialize if needed
    if not session.initialized:
        success = await session.initialize()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to initialize browser session. Please try again.")
    
    doc_type_full = DOC_TYPE_MAP[doc_type]
    results = await session.search_by_doc_type(doc_type_full, limit=limit)
    
    return SearchResponse(
        results=[
            DocumentResult(
                doc_id=r.get("doc_id", ""),
                doc_number=r.get("doc_number", ""),
                doc_type=r.get("doc_type", ""),
                record_date=r.get("record_date", "")
            )
            for r in results
        ],
        total=len(results),
        doc_type=doc_type_full
    )


@router.post("/download/{doc_id}", response_model=DownloadResponse)
async def download_document(doc_id: str):
    """Download a document PDF by its doc_id."""
    session = await get_session()
    
    if not session.initialized:
        raise HTTPException(status_code=400, detail="Session not initialized. Call /initialize first.")
    
    file_path = await session.download_document(doc_id.upper())
    
    if file_path:
        return DownloadResponse(success=True, doc_id=doc_id, file_path=file_path)
    else:
        return DownloadResponse(success=False, doc_id=doc_id, error="Download failed")


@router.get("/file/{doc_id}")
async def get_downloaded_file(doc_id: str):
    """Serve a previously downloaded PDF file."""
    downloads_dir = Path(__file__).parent.parent.parent.parent / "mcp_servers" / "recorder" / "downloads"
    pdf_path = downloads_dir / f"{doc_id.upper()}.pdf"
    
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {doc_id}.pdf")
    
    return FileResponse(
        path=str(pdf_path),
        filename=f"{doc_id.upper()}.pdf",
        media_type="application/pdf"
    )


@router.post("/extract/{doc_id}", response_model=ExtractResponse)
async def extract_document(doc_id: str):
    """
    Extract structured data from a downloaded PDF using Vertex AI.
    The PDF must already be downloaded.
    """
    downloads_dir = Path(__file__).parent.parent.parent.parent / "mcp_servers" / "recorder" / "downloads"
    pdf_path = downloads_dir / f"{doc_id.upper()}.pdf"
    
    if not pdf_path.exists():
        # Try images folder
        images_path = downloads_dir / f"{doc_id.upper()}_images"
        if images_path.exists():
            pdf_path = images_path
        else:
            raise HTTPException(status_code=404, detail=f"File not found: {doc_id}.pdf")
    
    session = await get_session()
    data = await session.extract_with_vertex_ai(str(pdf_path))
    
    if "error" in data:
        return ExtractResponse(success=False, doc_id=doc_id, error=data["error"])
    
    return ExtractResponse(success=True, doc_id=doc_id, data=data)


@router.get("/downloads")
async def list_downloads():
    """List all downloaded documents."""
    downloads_dir = Path(__file__).parent.parent.parent.parent / "mcp_servers" / "recorder" / "downloads"
    
    if not downloads_dir.exists():
        return {"files": []}
    
    files = []
    for f in downloads_dir.iterdir():
        if f.is_file() and f.suffix == ".pdf":
            files.append({
                "doc_id": f.stem,
                "filename": f.name,
                "size_bytes": f.stat().st_size
            })
        elif f.is_dir() and f.name.endswith("_images"):
            files.append({
                "doc_id": f.name.replace("_images", ""),
                "filename": f.name,
                "type": "images"
            })
    
    return {"files": files, "total": len(files)}
