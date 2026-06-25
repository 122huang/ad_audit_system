"""高级审核 API - R01/R02 双轮审核"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.advanced_audit import AdvancedAuditEngine

router = APIRouter(prefix="/api/advanced-audit", tags=["高级审核"])


class R01Request(BaseModel):
    text: str
    regions: List[str] = ["SG"]
    category: str = "小家电"


class EvidenceFile(BaseModel):
    name: str
    type: str = ""
    date: str = ""
    covers: List[str] = []


class R02Request(BaseModel):
    r01_result: dict
    evidence_files: List[EvidenceFile] = []


@router.post("/r01")
def audit_r01(req: R01Request, db: Session = Depends(get_db)):
    """R01: 文案扫描 → 风险清单 + 需要举证的宣称清单"""
    engine = AdvancedAuditEngine(db)
    result = engine.audit_r01(req.text, req.regions, req.category)
    return result


@router.post("/r02")
def audit_r02(req: R02Request, db: Session = Depends(get_db)):
    """R02: 证据充分性审查"""
    engine = AdvancedAuditEngine(db)
    evidence_dicts = [e.model_dump() for e in req.evidence_files]
    result = engine.audit_r02(req.r01_result, evidence_dicts)
    return result