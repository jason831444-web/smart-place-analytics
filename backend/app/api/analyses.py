from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import AnalysisRead
from app.services.analysis import analysis_to_dict, get_analysis

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.get("/{analysis_id}", response_model=AnalysisRead)
def read_analysis(analysis_id: int, db: Session = Depends(get_db)) -> AnalysisRead:
    analysis = get_analysis(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return AnalysisRead(**analysis_to_dict(analysis))

