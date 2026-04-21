from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_optional_user
from app.db.session import get_db
from app.models import User
from app.schemas.analysis import AnalysisRead, UploadRead
from app.services.analysis import analysis_to_dict, create_upload_record, run_analysis_for_upload
from app.services.facilities import get_facility_or_none
from app.services.storage import public_url_for_path, save_upload_file

router = APIRouter(tags=["uploads"])


@router.post("/uploads", response_model=UploadRead)
def upload_image(
    facility_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> UploadRead:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    try:
        path = save_upload_file(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    upload = create_upload_record(db, facility, path, file.filename or "upload", user)
    return UploadRead.model_validate(upload).model_copy(update={"url": public_url_for_path(upload.file_path)})


@router.post("/analyze", response_model=AnalysisRead)
def analyze_existing_upload(upload_id: int = Form(...), db: Session = Depends(get_db)) -> AnalysisRead:
    from app.models import Upload

    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    analysis = run_analysis_for_upload(db, upload)
    return AnalysisRead(**analysis_to_dict(analysis))


@router.post("/uploads/analyze", response_model=AnalysisRead)
def upload_and_analyze(
    facility_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> AnalysisRead:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    try:
        path = save_upload_file(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    upload = create_upload_record(db, facility, path, file.filename or "upload", user)
    analysis = run_analysis_for_upload(db, upload)
    return AnalysisRead(**analysis_to_dict(analysis))
