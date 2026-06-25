from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.models import ComplianceRule, Region
from app.schemas.schemas import RuleResponse, RuleValidationResult, ValidationIssue
from app.services.validator import RuleValidationService

router = APIRouter(prefix="/api/rules", tags=["法规规则"])


@router.get("", response_model=List[RuleResponse])
def list_rules(
    region_code: str = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    query = db.query(ComplianceRule)
    if active_only:
        query = query.filter(ComplianceRule.is_active == True)
    if region_code:
        region = db.query(Region).filter(Region.code == region_code).first()
        if region:
            query = query.filter(ComplianceRule.region_id == region.id)
    rules = query.order_by(ComplianceRule.created_at.desc()).all()
    return rules


@router.get("/{rule_id}", response_model=RuleResponse)
def get_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/validate", response_model=RuleValidationResult)
def validate_rule(
    rule_code: str,
    rule_name: str,
    description: str,
    keywords: str,
    source_url: str,
    source_content: str,
    region_code: str,
    db: Session = Depends(get_db)
):
    validator = RuleValidationService(db)
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    rule_data = {
        "rule_code": rule_code,
        "rule_name": rule_name,
        "description": description,
        "keywords": keyword_list,
        "patterns": [],
        "rule_type": "prohibited",
        "severity": "medium"
    }
    result = validator.validate_new_rule(rule_data, source_url, source_content, region_code)
    return result
