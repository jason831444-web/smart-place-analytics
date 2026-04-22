from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.cv.base import DetectorConfigurationError
from app.db.session import get_db
from app.schemas.analysis import LiveAnalysisRead
from app.services.facilities import get_facility_or_none
from app.services.live import analyze_live_frame

router = APIRouter(prefix="/live", tags=["live"])


@router.post("/analyze", response_model=LiveAnalysisRead)
async def analyze_live(
    facility_id: int = Form(...),
    file: UploadFile = File(...),
    persist: bool = Form(True),
    db: Session = Depends(get_db),
) -> LiveAnalysisRead:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    content_type = file.content_type or "application/octet-stream"
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Frame is empty")
        return analyze_live_frame(
            db=db,
            facility=facility,
            frame_content=content,
            content_type=content_type,
            original_filename=file.filename or "live-frame.jpg",
            persist_requested=persist,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DetectorConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
