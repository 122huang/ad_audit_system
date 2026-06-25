from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os
import shutil

from app.core.database import get_db
from app.models.models import AdMaterial, Advert, MaterialType, AuditStatus, RiskLevel
from app.schemas.schemas import (
    MaterialCreate, MaterialResponse, TextAuditRequest,
    AuditResponse, ViolationItem, KnowledgeReference, SimilarCase,
    ImageAuditRequest, VideoAuditRequest
)
from app.services.audit_engine import AuditEngine

router = APIRouter(prefix="/api/audit", tags=["广告审核"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _id():
    return str(uuid.uuid4())


def _get(v, key, default=None):
    """安全获取属性或字典值，兼容ViolationItem和dict"""
    if isinstance(v, dict):
        return v.get(key, default)
    return getattr(v, key, default)


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
            sev = _get(v, "severity", "medium")
            sev_val = sev.value if hasattr(sev, 'value') else str(sev)
            ar = AuditResultModel(
                id=_id(),
                material_id=material.id,
                region_code=region_code,
                source=_get(v, "source", "unknown"),
                rule_code=_get(v, "rule_code"),
                rule_name=_get(v, "rule_name"),
                matched_text=_get(v, "matched_text"),
                violation_desc=_get(v, "violation_desc"),
                suggestion=_get(v, "suggestion"),
                severity=sev_val,
                confidence=_get(v, "confidence", 0.9),
                is_blocked=_get(v, "is_blocked", False)
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


@router.post("/image", response_model=AuditResponse)
async def audit_image(
    image: Optional[UploadFile] = File(None),
    image_description: str = Form(""),
    ocr_text: str = Form(""),
    regions: str = Form("SG,MY"),
    category: str = Form("小家电"),
    advert_name: str = Form(""),
    title: str = Form(""),
    db: Session = Depends(get_db)
):
    """图片审核：上传图片 + 图片描述 + 图上文字"""
    region_list = [r.strip() for r in regions.split(",") if r.strip()]

    # 保存图片
    image_url = None
    if image and image.filename:
        file_ext = os.path.splitext(image.filename)[1] or ".png"
        save_name = f"{_id()}{file_ext}"
        save_path = os.path.join(UPLOAD_DIR, save_name)
        with open(save_path, "wb") as f:
            shutil.copyfileobj(image.file, f)
        image_url = f"/uploads/{save_name}"

    # 合并审核文本：图上文字 + 图片描述
    audit_text = f"{ocr_text}\n{image_description}".strip()

    return _do_audit(
        db=db,
        audit_text=audit_text,
        regions=region_list,
        category=category,
        advert_name=advert_name or "图片审核",
        title=title or "图片广告",
        material_type=MaterialType.image,
        content_url=image_url,
        ocr_text=ocr_text
    )


@router.post("/video", response_model=AuditResponse)
def audit_video(
    request: VideoAuditRequest,
    db: Session = Depends(get_db)
):
    """视频审核：脚本/旁白/字幕文案"""
    audit_text = f"{request.video_script}\n{request.video_description}".strip()

    return _do_audit(
        db=db,
        audit_text=audit_text,
        regions=request.regions,
        category=request.category,
        advert_name=request.advert_name or "视频审核",
        title=request.title or "视频广告",
        material_type=MaterialType.video,
        content_url=None,
        ocr_text=None
    )


def _do_audit(
    db: Session,
    audit_text: str,
    regions: List[str],
    category: str,
    advert_name: str,
    title: str,
    material_type: MaterialType,
    content_url: Optional[str] = None,
    ocr_text: Optional[str] = None
) -> AuditResponse:
    """通用审核执行函数"""
    if not audit_text:
        return AuditResponse(
            material_id="",
            overall_risk=RiskLevel.low,
            overall_status=AuditStatus.passed,
            hard_violations=[],
            soft_references=[],
            knowledge_references=[],
            similar_cases=[],
            checked_at=datetime.now(timezone.utc)
        )

    engine = AuditEngine(db)
    audit_result = engine.audit_text(audit_text, regions)

    advert = Advert(
        id=_id(),
        name=advert_name,
        created_by="user"
    )
    db.add(advert)
    db.flush()

    max_risk = RiskLevel.low

    for region_code, result in audit_result["regions"].items():
        material = AdMaterial(
            id=_id(),
            advert_id=advert.id,
            material_type=material_type,
            title=title,
            content_text=audit_text,
            ocr_text=ocr_text,
            content_url=content_url,
            target_regions=regions,
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
            sev = _get(v, "severity", "medium")
            sev_val = sev.value if hasattr(sev, 'value') else str(sev)
            ar = AuditResultModel(
                id=_id(),
                material_id=material.id,
                region_code=region_code,
                source=_get(v, "source", "unknown"),
                rule_code=_get(v, "rule_code"),
                rule_name=_get(v, "rule_name"),
                matched_text=_get(v, "matched_text"),
                violation_desc=_get(v, "violation_desc"),
                suggestion=_get(v, "suggestion"),
                severity=sev_val,
                confidence=_get(v, "confidence", 0.9),
                is_blocked=_get(v, "is_blocked", False)
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


@router.get("/materials/{material_id}", response_model=MaterialResponse)
def get_material(material_id: str, db: Session = Depends(get_db)):
    material = db.query(AdMaterial).filter(AdMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material
