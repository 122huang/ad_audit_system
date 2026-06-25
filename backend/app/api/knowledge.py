from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas.schemas import (
    KnowledgeDocCreate, KnowledgeDocResponse,
    CustomRuleCreate, CustomRuleResponse,
    CaseCreate, CaseResponse
)
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/api/knowledge", tags=["知识库管理"])


@router.post("/documents/text", response_model=KnowledgeDocResponse)
def create_document_text(doc: KnowledgeDocCreate, db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    try:
        document = service.create_document_from_text(
            title=doc.title,
            doc_type=doc.doc_type,
            content=doc.content_text or "",
            region_code=doc.region_code,
            tags=doc.tags,
            source=doc.source
        )
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档创建失败: {str(e)}")


@router.post("/documents/upload", response_model=KnowledgeDocResponse)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form("internal"),
    title: Optional[str] = Form(None),
    region_code: Optional[str] = Form(None),
    tags: str = Form(""),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    content = await file.read()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    try:
        document = service.upload_document(
            file_content=content,
            filename=file.filename or "document.txt",
            doc_type=doc_type,
            title=title,
            region_code=region_code,
            tags=tag_list
        )
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.get("/documents", response_model=List[KnowledgeDocResponse])
def list_documents(
    q: Optional[str] = Query(None),
    region_code: Optional[str] = Query(None),
    doc_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    docs, total = service.search_documents(q, region_code, doc_type, page, page_size)
    return docs


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    if service.delete_document(doc_id):
        return {"message": "文档已删除"}
    raise HTTPException(status_code=404, detail="文档不存在")


@router.post("/rules", response_model=CustomRuleResponse)
def create_custom_rule(rule: CustomRuleCreate, db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    try:
        custom_rule = service.create_custom_rule(
            user_id="user",
            rule_name=rule.rule_name,
            rule_type=rule.rule_type,
            keywords=rule.keywords,
            patterns=rule.patterns,
            description=rule.description,
            suggestion=rule.suggestion,
            region_code=rule.region_code,
            severity=rule.severity.value if hasattr(rule.severity, 'value') else rule.severity
        )
        return custom_rule
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"规则创建失败: {str(e)}")


@router.get("/rules", response_model=List[CustomRuleResponse])
def list_custom_rules(
    region_code: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    rules, total = service.list_custom_rules(None, region_code, page, page_size)
    return rules


@router.delete("/rules/{rule_id}")
def delete_custom_rule(rule_id: str, db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    if service.delete_custom_rule(rule_id):
        return {"message": "规则已删除"}
    raise HTTPException(status_code=404, detail="规则不存在")


@router.post("/cases", response_model=CaseResponse)
def create_case(case: CaseCreate, db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    try:
        new_case = service.create_case(
            title=case.title,
            material_type=case.material_type.value if hasattr(case.material_type, 'value') else case.material_type,
            violation_type=case.violation_type,
            description=case.description,
            decision=case.decision,
            content_text=case.content_text,
            region_code=case.region_code,
            before_edit=case.before_edit,
            after_edit=case.after_edit,
            reviewer_notes=case.reviewer_notes,
            tags=case.tags
        )
        return new_case
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"案例创建失败: {str(e)}")


@router.get("/cases", response_model=List[CaseResponse])
def list_cases(
    region_code: Optional[str] = Query(None),
    violation_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    service = KnowledgeService(db)
    cases, total = service.list_cases(region_code, violation_type, page, page_size)
    return cases
