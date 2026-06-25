import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, ForeignKey, Enum, Float, JSON
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base

UUIDType = String(36)
VectorType = Text


class MaterialType(str, enum.Enum):
    text = "text"
    image = "image"
    video = "video"


class AuditStatus(str, enum.Enum):
    pending = "pending"
    checking = "checking"
    passed = "passed"
    warning = "warning"
    rejected = "rejected"


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RuleType(str, enum.Enum):
    prohibited = "prohibited"
    restricted = "restricted"
    required = "required"
    warn = "warn"
    suggest = "suggest"


class DocType(str, enum.Enum):
    regulation = "regulation"
    internal = "internal"
    case = "case"
    guide = "guide"


def gen_uuid():
    return str(uuid.uuid4())


def parse_uuid(value):
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


class Region(Base):
    __tablename__ = "regions"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name_cn = Column(String(50), nullable=False)
    name_en = Column(String(100), nullable=False)
    flag_icon = Column(String(255))
    language = Column(String(20), default="zh")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    name = Column(String(100), nullable=False)
    parent_id = Column(UUIDType, ForeignKey("categories.id"), nullable=True)
    keywords = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    children = relationship("Category", backref="parent", remote_side="Category.id")


class Advert(Base):
    __tablename__ = "adverts"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    name = Column(String(200), nullable=False)
    brand = Column(String(100))
    category_id = Column(UUIDType, ForeignKey("categories.id"))
    description = Column(Text)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdMaterial(Base):
    __tablename__ = "ad_materials"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    advert_id = Column(UUIDType, ForeignKey("adverts.id"), nullable=False)
    material_type = Column(Enum(MaterialType), nullable=False)
    title = Column(String(200))
    content_text = Column(Text)
    content_url = Column(String(500))
    thumbnail_url = Column(String(500))
    ocr_text = Column(Text)
    video_duration = Column(Float)
    status = Column(Enum(AuditStatus), default=AuditStatus.pending)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.low)
    target_regions = Column(JSON, default=list)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    results = relationship("AuditResult", back_populates="material", cascade="all, delete-orphan")


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    region_id = Column(UUIDType, ForeignKey("regions.id"))
    category_id = Column(UUIDType, ForeignKey("categories.id"))
    rule_code = Column(String(50), unique=True, nullable=False, index=True)
    rule_name = Column(String(200), nullable=False)
    rule_type = Column(Enum(RuleType), nullable=False)
    severity = Column(Enum(RiskLevel), default=RiskLevel.medium)
    keywords = Column(JSON, default=list)
    patterns = Column(JSON, default=list)
    description = Column(Text, nullable=False)
    suggestion = Column(Text)
    penalty = Column(String(500))
    source_url = Column(String(500))
    source_snapshot_id = Column(String(100))
    effective_date = Column(DateTime)
    expire_date = Column(DateTime)
    version = Column(String(20), default="1.0")
    review_status = Column(String(20), default="pending")
    reviewed_by = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CustomRule(Base):
    __tablename__ = "custom_rules"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    user_id = Column(String(100), nullable=False)
    region_id = Column(UUIDType, ForeignKey("regions.id"))
    category_id = Column(UUIDType, ForeignKey("categories.id"))
    rule_code = Column(String(50), unique=True, nullable=False, index=True)
    rule_name = Column(String(200), nullable=False)
    rule_type = Column(Enum(RuleType), nullable=False)
    severity = Column(Enum(RiskLevel), default=RiskLevel.medium)
    keywords = Column(JSON, default=list)
    patterns = Column(JSON, default=list)
    description = Column(Text, nullable=False)
    suggestion = Column(Text)
    case_ref = Column(UUIDType, ForeignKey("audit_cases.id"))
    hit_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditResult(Base):
    __tablename__ = "audit_results"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    material_id = Column(UUIDType, ForeignKey("ad_materials.id"), nullable=False)
    region_code = Column(String(10), nullable=False)
    source = Column(String(50), nullable=False)
    rule_id = Column(UUIDType)
    rule_code = Column(String(50))
    rule_name = Column(String(200))
    violation_type = Column(String(50))
    matched_text = Column(Text)
    violation_desc = Column(Text)
    suggestion = Column(Text)
    severity = Column(String(20))
    confidence = Column(Float, default=1.0)
    is_blocked = Column(Boolean, default=False)
    reference_doc = Column(String(200))
    reference_content = Column(Text)
    similarity = Column(Float)
    checked_by = Column(String(100))
    checked_at = Column(DateTime, default=datetime.utcnow)

    material = relationship("AdMaterial", back_populates="results")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    title = Column(String(300), nullable=False)
    doc_type = Column(Enum(DocType), nullable=False)
    file_url = Column(String(500))
    file_name = Column(String(255))
    content_text = Column(Text)
    region_id = Column(UUIDType, ForeignKey("regions.id"))
    category_id = Column(UUIDType, ForeignKey("categories.id"))
    source = Column(String(200))
    tags = Column(JSON, default=list)
    version = Column(String(20), default="1.0")
    chunk_count = Column(Integer, default=0)
    is_indexed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    document_id = Column(UUIDType, ForeignKey("knowledge_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    chunk_metadata = Column("metadata", JSON, default=dict)
    embedding = Column(VectorType)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("KnowledgeDocument", back_populates="chunks")


class AuditCase(Base):
    __tablename__ = "audit_cases"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    title = Column(String(300), nullable=False)
    material_type = Column(Enum(MaterialType))
    content_text = Column(Text)
    violation_type = Column(String(100))
    region_code = Column(String(10))
    description = Column(Text)
    decision = Column(String(50))
    before_edit = Column(JSON, default=list)
    after_edit = Column(JSON, default=list)
    reviewer_notes = Column(Text)
    tags = Column(JSON, default=list)
    hit_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class RuleReview(Base):
    __tablename__ = "rule_reviews"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    rule_id = Column(UUIDType, nullable=False)
    rule_type = Column(String(20), nullable=False)
    source_validation = Column(JSON)
    content_validation = Column(JSON)
    logic_validation = Column(JSON)
    source_snapshot = Column(Text)
    source_context = Column(Text)
    review_status = Column(String(20), default="pending")
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class RuleVersion(Base):
    __tablename__ = "rule_versions"

    id = Column(UUIDType, primary_key=True, default=gen_uuid)
    rule_id = Column(UUIDType, nullable=False)
    rule_type = Column(String(20), nullable=False)
    version = Column(String(20), nullable=False)
    rule_data = Column(JSON, nullable=False)
    change_note = Column(Text)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
