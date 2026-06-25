import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
import jieba
import logging

from app.models.models import (
    ComplianceRule, CustomRule, AuditCase,
    KnowledgeDocument, DocumentChunk, Region
)
from app.schemas.schemas import (
    ViolationItem, KnowledgeReference, SimilarCase,
    RiskLevel
)

logger = logging.getLogger(__name__)


class AuditEngine:
    """广告审核引擎 - 融合官方法规、自定义规则、知识库、案例库"""

    def __init__(self, db: Session):
        self.db = db
        self._load_jieba()

    def _load_jieba(self):
        """初始化jieba分词"""
        for word in ["最节能", "最安全", "顶级", "第一品牌", "销量冠军"]:
            jieba.add_word(word)

    def audit_text(self, text: str, regions: List[str]) -> Dict[str, Any]:
        """
        审核文本内容
        返回: {region: {hard_violations, soft_references, knowledge_refs, cases}}
        """
        results = {}
        overall_risk = RiskLevel.low
        all_hard = []

        for region_code in regions:
            hard_violations = []
            soft_references = []
            knowledge_refs = []
            cases = []

            official_hits = self._match_official_rules(text, region_code)
            hard_violations.extend(official_hits)

            custom_hits = self._match_custom_rules(text, region_code)
            for hit in custom_hits:
                if hit.get("is_blocked", False):
                    hard_violations.append(hit)
                else:
                    soft_references.append(hit)

            knowledge_hits = self._retrieve_knowledge(text, region_code)
            knowledge_refs.extend(knowledge_hits)

            similar_cases = self._find_similar_cases(text, region_code)
            cases.extend(similar_cases)

            region_risk = self._calculate_risk(hard_violations, soft_references)
            if self._risk_level_value(region_risk) > self._risk_level_value(overall_risk):
                overall_risk = region_risk

            results[region_code] = {
                "hard_violations": hard_violations,
                "soft_references": soft_references,
                "knowledge_references": knowledge_refs,
                "similar_cases": cases,
                "risk_level": region_risk
            }

            all_hard.extend(hard_violations)

        return {
            "regions": results,
            "overall_risk": overall_risk,
            "has_blocking_violations": len(all_hard) > 0
        }

    def _match_official_rules(self, text: str, region_code: str) -> List[ViolationItem]:
        """匹配官方法规规则"""
        violations = []

        region = self.db.query(Region).filter(Region.code == region_code).first()
        if not region:
            return violations

        rules = self.db.query(ComplianceRule).filter(
            ComplianceRule.region_id == region.id,
            ComplianceRule.is_active == True,
            ComplianceRule.review_status == "approved"
        ).all()

        for rule in rules:
            match_result = self._match_rule(text, rule.keywords, rule.patterns)
            if match_result["matched"]:
                is_blocked = rule.rule_type.value in ["prohibited", "restricted"]
                violations.append(ViolationItem(
                    source="official",
                    rule_code=rule.rule_code,
                    rule_name=rule.rule_name,
                    matched_text=match_result.get("value"),
                    violation_desc=rule.description,
                    suggestion=rule.suggestion,
                    severity=RiskLevel(rule.severity.value) if hasattr(rule.severity, 'value') else RiskLevel.medium,
                    confidence=match_result.get("confidence", 0.9),
                    is_blocked=is_blocked
                ))

        return violations

    def _match_custom_rules(self, text: str, region_code: str) -> List[Dict]:
        """匹配用户自定义规则"""
        violations = []

        rules = self.db.query(CustomRule).filter(
            CustomRule.is_active == True
        ).all()

        for rule in rules:
            if rule.region_id:
                region = self.db.query(Region).filter(Region.id == rule.region_id).first()
                if region and region.code != region_code:
                    continue

            match_result = self._match_rule(text, rule.keywords, rule.patterns)
            if match_result["matched"]:
                rule.hit_count = (rule.hit_count or 0) + 1
                is_blocked = rule.rule_type.value == "prohibited"
                violations.append({
                    "source": "custom",
                    "rule_code": rule.rule_code,
                    "rule_name": rule.rule_name,
                    "matched_text": match_result.get("value"),
                    "violation_desc": rule.description,
                    "suggestion": rule.suggestion,
                    "severity": RiskLevel(rule.severity.value) if hasattr(rule.severity, 'value') else RiskLevel.medium,
                    "confidence": match_result.get("confidence", 0.85),
                    "is_blocked": is_blocked
                })

        self.db.commit()
        return violations

    def _match_rule(self, text: str, keywords: List[str], patterns: List[str]) -> Dict[str, Any]:
        """规则匹配核心逻辑 - 关键词+正则"""
        if not keywords and not patterns:
            return {"matched": False}

        text_lower = text.lower()

        for keyword in (keywords or []):
            if keyword and keyword.lower() in text_lower:
                return {"matched": True, "type": "keyword", "value": keyword, "confidence": 0.95}

        for pattern in (patterns or []):
            try:
                match = re.search(pattern, text)
                if match:
                    return {"matched": True, "type": "pattern", "value": match.group(), "confidence": 0.85}
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern}")
                continue

        return {"matched": False}

    def _retrieve_knowledge(self, text: str, region_code: str, top_k: int = 3) -> List[KnowledgeReference]:
        """从知识库检索相关内容（简化版向量检索）"""
        references = []

        try:
            region = self.db.query(Region).filter(Region.code == region_code).first()

            query_keywords = self._extract_keywords(text)

            docs = self.db.query(KnowledgeDocument).filter(
                KnowledgeDocument.is_active == True,
                KnowledgeDocument.is_indexed == True
            )
            if region:
                docs = docs.filter(
                    or_(KnowledgeDocument.region_id == region.id,
                        KnowledgeDocument.region_id == None)
                )

            docs = docs.limit(50).all()

            scored_chunks = []
            for doc in docs:
                chunks = self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == doc.id
                ).limit(20).all()

                for chunk in chunks:
                    score = self._keyword_similarity(query_keywords, chunk.content)
                    if score > 0.1:
                        scored_chunks.append((score, doc, chunk))

            scored_chunks.sort(key=lambda x: x[0], reverse=True)

            for score, doc, chunk in scored_chunks[:top_k]:
                ref = KnowledgeReference(
                    doc_title=doc.title,
                    relevant_content=chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    similarity=round(score, 3),
                    page=chunk.chunk_metadata.get("page") if chunk.chunk_metadata else None
                )
                references.append(ref)

        except Exception as e:
            logger.error(f"Knowledge retrieval error: {e}")

        return references

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        words = jieba.cut(text)
        stop_words = {"的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}
        keywords = [w for w in words if len(w) >= 2 and w not in stop_words]
        return keywords[:20]

    def _keyword_similarity(self, query_keywords: List[str], content: str) -> float:
        """基于关键词重叠的简单相似度计算"""
        if not query_keywords:
            return 0.0
        content_lower = content.lower()
        matches = sum(1 for kw in query_keywords if kw.lower() in content_lower)
        return matches / len(query_keywords) if query_keywords else 0.0

    def _find_similar_cases(self, text: str, region_code: str, top_k: int = 3) -> List[SimilarCase]:
        """查找相似历史案例"""
        cases = []

        try:
            query = self.db.query(AuditCase).filter(AuditCase.is_active == True)
            if region_code:
                query = query.filter(
                    or_(AuditCase.region_code == region_code,
                        AuditCase.region_code == None)
                )

            all_cases = query.limit(100).all()

            query_keywords = self._extract_keywords(text)
            scored_cases = []

            for case in all_cases:
                case_text = case.title + " " + (case.content_text or "") + " " + case.description
                score = self._keyword_similarity(query_keywords, case_text)
                if score > 0.15:
                    scored_cases.append((score, case))

            scored_cases.sort(key=lambda x: x[0], reverse=True)

            for score, case in scored_cases[:top_k]:
                case.hit_count = (case.hit_count or 0) + 1
                before = case.before_edit[0] if case.before_edit else None
                after = case.after_edit[0] if case.after_edit else None
                cases.append(SimilarCase(
                    case_id=case.id,
                    title=case.title,
                    decision=case.decision,
                    before=before,
                    after=after
                ))

            self.db.commit()
        except Exception as e:
            logger.error(f"Case matching error: {e}")

        return cases

    def _calculate_risk(self, hard_violations: List, soft_references: List) -> RiskLevel:
        """计算综合风险等级"""
        if not hard_violations and not soft_references:
            return RiskLevel.low

        max_hard_severity = RiskLevel.low
        for v in hard_violations:
            severity = v.severity if hasattr(v.severity, 'value') else RiskLevel(v.get("severity", "medium"))
            if self._risk_level_value(severity) > self._risk_level_value(max_hard_severity):
                max_hard_severity = severity

        if self._risk_level_value(max_hard_severity) >= self._risk_level_value(RiskLevel.high):
            return max_hard_severity

        if hard_violations:
            return RiskLevel.medium if len(hard_violations) <= 2 else RiskLevel.high

        if soft_references:
            return RiskLevel.low

        return RiskLevel.low

    def _risk_level_value(self, level: RiskLevel) -> int:
        """风险等级数值化"""
        values = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        if isinstance(level, str):
            return values.get(level, 0)
        return values.get(level.value if hasattr(level, 'value') else str(level), 0)
