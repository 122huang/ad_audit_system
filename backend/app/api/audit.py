from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.core.database import get_db
from app.models.models import AdMaterial, Advert, MaterialType, AuditStatus, RiskLevel
from app.schemas.schemas import (
    MaterialCreate, MaterialResponse, TextAuditRequest,
    AuditResponse, ViolationItem, KnowledgeReference, SimilarCase
)
from app.services.audit_engine import AuditEngine

router = APIRouter(prefix="/api/audit", tags=["广告审核"])


def _id():
    return str(uuid.uuid4())


@router.post("/text", response_model=AuditResponse)
def audit_text(request: TextAuditRequest, db: Session = Depends(get_db)):
    if not request.regions:
        raise HTTPException(status_code=400, detail="请至少选择一个目标法域")

    engine = AuditEngine(db)
    audit_result = engine.audit_text(request.text, request.regions)

    advert = Advert(
        id=_id(),
        name=request.advert_name or "文本审核",
        created_by="user"
    )
    db.add(advert)
    db.flush()

    max_risk = RiskLevel.low
    has_blocking = audit_result.get("has_blocking_violations", False)

    for region_code, result in audit_result["regions"].items():
        material = AdMaterial(
            id=_id(),
            advert_id=advert.id,
            material_type=MaterialType.text,
            title=request.title or "文本广告",
            content_text=request.text,
            target_regions=request.regions,
            status=AuditStatus.rejected if result["risk_level"] in [RiskLevel.high, RiskLevel.critical]
                   else AuditStatus.warning if result["hard_violations"]
                   else AuditStatus.passed,
            risk_level=result["risk_level"],
            created_by="user"
        )
        db.add(material)
        db.flush()

        for v in result["hard_violations"]:
            from app.models.models import AuditResult as AuditResultModel
            ar = AuditResultModel(
                id=_id(),
                material_id=material.id,
                region_code=region_code,
                source=v.source,
                rule_code=v.rule_code,
                rule_name=v.rule_name,
                matched_text=v.matched_text,
                violation_desc=v.violation_desc,
                suggestion=v.suggestion,
                severity=v.severity.value if hasattr(v.severity, 'value') else str(v.severity),
                confidence=v.confidence,
                is_blocked=v.is_blocked
            )
            db.add(ar)

        for ref in result["knowledge_references"]:
            from app.models.models import AuditResult as AuditResultModel
            ar = AuditResultModel(
                id=_id(),
                material_id=material.id,
                region_code=region_code,
                source="knowledge",
                reference_doc=ref.doc_title,
                reference_content=ref.relevant_content,
                similarity=ref.similarity,
                is_blocked=False
            )
            db.add(ar)

        risk_val = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        current_risk_val = risk_val.get(result["risk_level"].value if hasattr(result["risk_level"], 'value') else str(result["risk_level"]), 0)
        max_risk_val = risk_val.get(max_risk.value, 0)
        if current_risk_val > max_risk_val:
            max_risk = result["risk_level"]

    db.commit()

    hard_violations_flat = []
    soft_references_flat = []
    knowledge_refs_flat = []
    cases_flat = []
    for region_code, result in audit_result["regions"].items():
        hard_violations_flat.extend(result["hard_violations"])
        soft_references_flat.extend(result["soft_references"])
        knowledge_refs_flat.extend(result["knowledge_references"])
        cases_flat.extend(result["similar_cases"])

    overall_status = AuditStatus.rejected if max_risk in [RiskLevel.high, RiskLevel.critical] \
        else AuditStatus.warning if hard_violations_flat else AuditStatus.passed

    from datetime import datetime, timezone
    return AuditResponse(
        material_id=advert.id,
        overall_risk=max_risk,
        overall_status=overall_status,
        hard_violations=hard_violations_flat,
        soft_references=soft_references_flat,
        knowledge_references=knowledge_refs_flat,
        similar_cases=cases_flat,
        checked_at=datetime.now(timezone.utc)
    )


@router.get("/materials", response_model=List[MaterialResponse])
def list_materials(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    materials = db.query(AdMaterial).order_by(AdMaterial.created_at.desc())\
        .offset(skip).limit(limit).all()
    return materials


@router.get("/materials/{material_id}", response_model=MaterialResponse)
def get_material(material_id: str, db: Session = Depends(get_db)):
    material = db.query(AdMaterial).filter(AdMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material
