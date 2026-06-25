from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.models import Region
from app.schemas.schemas import RegionResponse

router = APIRouter(prefix="/api/regions", tags=["法域管理"])


@router.get("", response_model=List[RegionResponse])
def list_regions(db: Session = Depends(get_db)):
    regions = db.query(Region).filter(Region.is_active == True).all()
    return regions


@router.get("/{code}", response_model=RegionResponse)
def get_region(code: str, db: Session = Depends(get_db)):
    region = db.query(Region).filter(Region.code == code, Region.is_active == True).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region
