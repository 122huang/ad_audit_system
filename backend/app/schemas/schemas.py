from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MaterialType(str, Enum):
    text = "text"
    image = "image"
    video = "video"


class AuditStatus(str, Enum):
    pending = "pending"
    checking = "checking"
    passed = "passed"
    warning = "warning"
    rejected = "rejected"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RegionBase(BaseModel):
    code: str
    name_cn: str
    name_en: str
    language: str = "zh"
    is_active: bool = True


class RegionCreate(RegionBase):
    pass


class RegionResponse(RegionBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class MaterialBase(BaseModel):
    material_type: MaterialType
    title: Optional[str] = None
    content_text: Optional[str] = None
    target_regions: List[str] = Field(default_factory=list)


class MaterialCreate(MaterialBase):
    advert_id: Optional[str] = None
    advert_name: Optional[str] = None


class MaterialResponse(MaterialBase):
    id: str
    advert_id: Optional[str] = None
    status: AuditStatus
    risk_level: RiskLevel
    ocr_text: Optional[str] = None
    content_url: Optional[str] = None
    created_at: datetime
    results: List["AuditResultResponse"] = []

    class Config:
        from_attributes = True


class ViolationItem(BaseModel):
    source: str
    rule_code: Optional[str] = None
    rule_name: Optional[str] = None
    matched_text: Optional[str] = None
    violation_desc: str
    suggestion: Optional[str] = None
    severity: RiskLevel
    confidence: float = 1.0
    is_blocked: bool = False


class KnowledgeReference(BaseModel):
    doc_title: str
    relevant_content: str
    similarity: float
    page: Optional[int] = None


class SimilarCase(BaseModel):
    case_id: str
    title: str
    decision: str
    before: Optional[str] = None
    after: Optional[str] = None


class AuditResultResponse(BaseModel):
    id: str
    material_id: str
    region_code: str
    source: str
    rule_id: Optional[str] = None
    rule_code: Optional[str] = None
    rule_name: Optional[str] = None
    violation_type: Optional[str] = None
    matched_text: Optional[str] = None
    violation_desc: Optional[str] = None
    suggestion: Optional[str] = None
    severity: Optional[str] = None
    confidence: float = 1.0
    is_blocked: bool = False
    reference_doc: Optional[str] = None
    reference_content: Optional[str] = None
    similarity: Optional[float] = None
    checked_at: datetime

    class Config:
        from_attributes = True


class AuditResponse(BaseModel):
    material_id: str
    overall_risk: RiskLevel
    overall_status: AuditStatus
    hard_violations: List[ViolationItem] = []
    soft_references: List[ViolationItem] = []
    knowledge_references: List[KnowledgeReference] = []
    similar_cases: List[SimilarCase] = []
    checked_at: datetime


class RuleBase(BaseModel):
    rule_code: str
    rule_name: str
    rule_type: str
    severity: RiskLevel = RiskLevel.medium
    keywords: List[str] = Field(default_factory=list)
    patterns: List[str] = Field(default_factory=list)
    description: str
    suggestion: Optional[str] = None
    penalty: Optional[str] = None
    source_url: Optional[str] = None
    region_code: Optional[str] = None
    is_active: bool = True


class RuleCreate(RuleBase):
    pass


class RuleResponse(RuleBase):
    id: str
    review_status: str = "approved"
    version: str = "1.0"
    created_at: datetime

    class Config:
        from_attributes = True


class CustomRuleCreate(BaseModel):
    rule_name: str
    rule_type: str
    severity: RiskLevel = RiskLevel.medium
    keywords: List[str] = Field(default_factory=list)
    patterns: List[str] = Field(default_factory=list)
    description: str
    suggestion: Optional[str] = None
    region_code: Optional[str] = None
    case_ref: Optional[str] = None


class CustomRuleResponse(CustomRuleCreate):
    id: str
    rule_code: str
    hit_count: int = 0
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeDocCreate(BaseModel):
    title: str
    doc_type: str
    content_text: Optional[str] = None
    source: Optional[str] = None
    region_code: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class KnowledgeDocResponse(KnowledgeDocCreate):
    id: str
    file_name: Optional[str] = None
    chunk_count: int = 0
    is_indexed: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class CaseCreate(BaseModel):
    title: str
    material_type: MaterialType = MaterialType.text
    content_text: Optional[str] = None
    violation_type: str
    region_code: Optional[str] = None
    description: str
    decision: str
    before_edit: List[str] = Field(default_factory=list)
    after_edit: List[str] = Field(default_factory=list)
    reviewer_notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class CaseResponse(CaseCreate):
    id: str
    hit_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class TextAuditRequest(BaseModel):
    text: str = Field(..., min_length=1, description="待审核文本")
    regions: List[str] = Field(default_factory=lambda: ["SG", "MY"], description="目标法域列表")
    advert_name: Optional[str] = None
    title: Optional[str] = None


class ValidationIssue(BaseModel):
    level: str
    type: str
    message: str


class RuleValidationResult(BaseModel):
    passed: bool
    issues: List[ValidationIssue] = []
    source_valid: bool = False
    content_valid: bool = False
    logic_valid: bool = False
    snapshot_id: Optional[str] = None
