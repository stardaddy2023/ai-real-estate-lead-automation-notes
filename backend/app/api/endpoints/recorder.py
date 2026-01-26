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
    book_page: Optional[str] = None
    related_docs: Optional[List[Dict[str, str]]] = None


class SearchResponse(BaseModel):
    results: List[DocumentResult]
    total: int
    doc_type: str


class DownloadResponse(BaseModel):
    success: bool
    doc_id: str
    file_path: Optional[str] = None
    error: Optional[str] = None


class BulkLookupRequest(BaseModel):
    """Request for bulk recorder lookup."""
    leads: List[dict]  # List of {owner_name, address} objects


class LeadRecorderResult(BaseModel):
    """Recorder results for a single lead."""
    address: str
    owner_name: str
    documents: List[DocumentResult]
    doc_count: int
    has_deed_of_trust: bool = False
    has_lis_pendens: bool = False
    has_notice_sale: bool = False
    has_lien: bool = False
    has_judgment: bool = False
    has_reconveyance: bool = False
    last_deed_date: Optional[str] = None
    error: Optional[str] = None


class BulkLookupResponse(BaseModel):
    """Response from bulk recorder lookup."""
    results: List[LeadRecorderResult]
    total_processed: int
    total_success: int
    total_errors: int


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
    """Get current recorder session status, including cookie info."""
    global _session
    session = await get_session()
    
    is_initialized = session.initialized
    cookies_info = session.get_cookies_status()
    
    if is_initialized:
        message = "Session ready (headless mode)" if session._headless_mode else "Session ready"
    elif cookies_info.get("exists"):
        message = f"Cookies available ({cookies_info.get('age_hours', 0):.1f}h old). Click Initialize to try them."
    else:
        message = "No session or cookies. Click Initialize to solve CAPTCHA."
    
    return SessionStatus(
        initialized=is_initialized,
        needs_captcha=not is_initialized and not cookies_info.get("exists"),
        ready=is_initialized,
        message=message
    )


@router.get("/cookies/status")
async def get_cookies_status():
    """Get status of saved cookies."""
    session = await get_session()
    return session.get_cookies_status()


@router.post("/cookies/refresh")
async def refresh_cookies():
    """Force a manual CAPTCHA flow to get fresh cookies."""
    session = await get_session()
    success = await session.refresh_cookies()
    if success:
        return {"success": True, "message": "Cookies refreshed successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to refresh cookies")


@router.post("/initialize")
async def initialize_session():
    """
    Initialize the browser session.
    Will try to use saved cookies first (headless, instant).
    Falls back to manual CAPTCHA if cookies don't work.
    """
    session = await get_session()
    
    if session.initialized:
        return {"success": True, "message": "Session already initialized"}
    
    success = await session.initialize()
    
    if success:
        mode = "headless with saved cookies" if session._headless_mode else "manual CAPTCHA"
        return {"success": True, "message": f"Session initialized via {mode}"}
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
    
    # Check if session is initialized - DON'T auto-init during search (blocks for CAPTCHA)
    if not session.initialized:
        raise HTTPException(
            status_code=503, 
            detail="Recorder session not active. Please open the Recorder page first to solve the CAPTCHA."
        )
    
    doc_type_full = DOC_TYPE_MAP[doc_type]
    results = await session.search_by_doc_type(doc_type_full, limit=limit)
    
    # Check for error in results
    if results and "error" in results[0]:
        error_msg = results[0]["error"]
        if "Session not initialized" in error_msg or "browser closed" in error_msg:
            raise HTTPException(status_code=503, detail=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    
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


@router.get("/search/sequence/{seq_num}", response_model=SearchResponse)
async def search_by_sequence(seq_num: str):
    """
    Search for a document by its sequence number.
    Will auto-initialize browser session if not already initialized.
    """
    session = await get_session()
    
    # Auto-initialize if needed
    if not session.initialized:
        success = await session.initialize()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to initialize browser session. Please try again.")
    
    results = await session.search_by_sequence(seq_num)
    
    # Check for error in results
    if results and "error" in results[0]:
        error_msg = results[0]["error"]
        if "Session not initialized" in error_msg or "browser closed" in error_msg:
            raise HTTPException(status_code=503, detail=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    
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
        doc_type="SEQUENCE_SEARCH"
    )


@router.get("/search/name/{name}", response_model=SearchResponse)
async def search_by_name(
    name: str, 
    search_type: str = "grantor", 
    deed_only: bool = True, 
    limit: int = 50,
    # Anchor parameters for smart filtering
    anchor_seq: Optional[str] = None,
    anchor_docket: Optional[str] = None,
    anchor_page: Optional[str] = None,
    anchor_date: Optional[str] = None
):
    """
    Search for documents by Grantor or Grantee name.
    
    V2 Strategy:
    1. If anchor_seq provided: Search by sequence first to get exact deed and its date
    2. Then search by name + date to find all related docs for that owner on that date
    3. Return combined, deduplicated results
    """
    session = await get_session()
    
    if not session.initialized:
        raise HTTPException(
            status_code=503, 
            detail="Recorder session not active. Please open the Recorder page first to solve the CAPTCHA."
        )
    
    all_results = []
    anchor_date_from_seq = None
    
    # Step 1/2: If we have a sequence number, search for it first
    if anchor_seq:
        print(f"[Recorder API] Step 1/2: Searching by sequence {anchor_seq}", flush=True)
        seq_results = await session.search_by_sequence(anchor_seq)
        
        if seq_results and "error" not in seq_results[0]:
            for doc in seq_results:
                all_results.append(doc)
                # Extract the recording date from the anchor document
                if doc.get("record_date") and not anchor_date_from_seq:
                    anchor_date_from_seq = doc.get("record_date")
                    print(f"[Recorder API] Found anchor date: {anchor_date_from_seq}", flush=True)
    
    # Step 3: Search by name + date 
    # Use the date from seq search, or fall back to provided anchor_date
    target_date = anchor_date_from_seq or anchor_date
    
    if target_date:
        print(f"[Recorder API] Step 3: Searching by name '{name}' on date {target_date}", flush=True)
        name_date_results = await session.search_by_name_and_date(
            name=name,
            record_date=target_date,
            search_type=search_type,
            limit=limit
        )
        
        if name_date_results and "error" not in name_date_results[0]:
            for doc in name_date_results:
                all_results.append(doc)
    else:
        # No date available - fall back to regular name search with limit
        print(f"[Recorder API] No date available, falling back to name search for '{name}'", flush=True)
        fallback_results = await session.search_by_name(
            name=name, 
            search_type=search_type, 
            deed_types_only=deed_only, 
            limit=20  # Limit fallback to avoid too many unrelated results
        )
        if fallback_results and "error" not in fallback_results[0]:
            all_results = fallback_results
    
    # Deduplicate by doc_number
    seen_doc_numbers = set()
    unique_results = []
    for doc in all_results:
        doc_num = doc.get("doc_number")
        if doc_num and doc_num not in seen_doc_numbers:
            seen_doc_numbers.add(doc_num)
            unique_results.append(doc)
    
    print(f"[Recorder API] Returning {len(unique_results)} unique documents", flush=True)
    
    return SearchResponse(
        results=[
            DocumentResult(
                doc_id=r.get("doc_id", ""),
                doc_number=r.get("doc_number", ""),
                doc_type=r.get("doc_type", ""),
                record_date=r.get("record_date", ""),
                book_page=r.get("book_page"),
                related_docs=r.get("related_docs")
            )
            for r in unique_results
        ],
        total=len(unique_results),
        doc_type=f"SMART_SEARCH_{search_type.upper()}"
    )


@router.post("/bulk-lookup", response_model=BulkLookupResponse)
async def bulk_lookup(request: BulkLookupRequest):
    """
    Bulk recorder lookup for multiple leads.
    Searches by owner name (grantee) for each lead.
    Rate limited to avoid overloading the recorder site.
    """
    session = await get_session()
    
    if not session.initialized:
        raise HTTPException(
            status_code=503, 
            detail="Recorder session not active. Please open the Recorder page first."
        )
    
    results = []
    total_success = 0
    total_errors = 0
    
    for i, lead in enumerate(request.leads):
        owner_name = lead.get("owner_name", "")
        address = lead.get("address", "")
        
        if not owner_name:
            results.append(LeadRecorderResult(
                address=address,
                owner_name=owner_name,
                documents=[],
                doc_count=0,
                error="No owner name provided"
            ))
            total_errors += 1
            continue
        
        try:
            # Search by owner name (grantee)
            docs = await session.search_by_name(owner_name, search_type="grantee", limit=20)
            
            if docs and "error" in docs[0]:
                results.append(LeadRecorderResult(
                    address=address,
                    owner_name=owner_name,
                    documents=[],
                    doc_count=0,
                    error=docs[0]["error"]
                ))
                total_errors += 1
                continue
            
            # Process document types and extract flags
            doc_results = []
            has_deed_of_trust = False
            has_lis_pendens = False
            has_notice_sale = False
            has_lien = False
            has_judgment = False
            has_reconveyance = False
            last_deed_date = None
            
            for doc in docs:
                doc_type = doc.get("doc_type", "").upper()
                
                doc_results.append(DocumentResult(
                    doc_id=doc.get("doc_id", ""),
                    doc_number=doc.get("doc_number", ""),
                    doc_type=doc.get("doc_type", ""),
                    record_date=doc.get("record_date", "")
                ))
                
                # Detect document type flags
                if "DEED OF TRUST" in doc_type or "TRUST DEED" in doc_type:
                    has_deed_of_trust = True
                if "LIS PENDENS" in doc_type:
                    has_lis_pendens = True
                if "NOTICE" in doc_type and "SALE" in doc_type:
                    has_notice_sale = True
                if "LIEN" in doc_type:
                    has_lien = True
                if "JUDGMENT" in doc_type:
                    has_judgment = True
                if "RECONVEYANCE" in doc_type:
                    has_reconveyance = True
                
                # Track last deed date (WARRANTY DEED, QUIT CLAIM DEED, etc.)
                if "DEED" in doc_type and "TRUST" not in doc_type:
                    if not last_deed_date:
                        last_deed_date = doc.get("record_date")
            
            results.append(LeadRecorderResult(
                address=address,
                owner_name=owner_name,
                documents=doc_results,
                doc_count=len(doc_results),
                has_deed_of_trust=has_deed_of_trust,
                has_lis_pendens=has_lis_pendens,
                has_notice_sale=has_notice_sale,
                has_lien=has_lien,
                has_judgment=has_judgment,
                has_reconveyance=has_reconveyance,
                last_deed_date=last_deed_date
            ))
            total_success += 1
            
            # Rate limit between searches (2 seconds)
            if i < len(request.leads) - 1:
                await asyncio.sleep(2)
                
        except Exception as e:
            results.append(LeadRecorderResult(
                address=address,
                owner_name=owner_name,
                documents=[],
                doc_count=0,
                error=str(e)
            ))
            total_errors += 1
    
    return BulkLookupResponse(
        results=results,
        total_processed=len(request.leads),
        total_success=total_success,
        total_errors=total_errors
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
