import hashlib
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from sqlalchemy.orm import Session
import logging

from app.core.config import settings
from app.models.models import ComplianceRule, RuleReview, RuleVersion, Region
from app.schemas.schemas import ValidationIssue, RuleValidationResult

logger = logging.getLogger(__name__)


class Issue:
    def __init__(self, level: str, issue_type: str, message: str):
        self.level = level
        self.type = issue_type
        self.message = message

    def to_dict(self):
        return {"level": self.level, "type": self.type, "message": self.message}


class SourceValidator:
    """校验1: 来源真实性校验"""

    def __init__(self, db: Session):
        self.db = db
        self.whitelist = settings.OFFICIAL_WHITELIST

    def extract_domain(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ""

    def is_in_whitelist(self, domain: str, region_code: str) -> bool:
        allowed_domains = self.whitelist.get(region_code, [])
        for allowed in allowed_domains:
            allowed_domain = self.extract_domain(allowed)
            if domain == allowed_domain or domain.endswith("." + allowed_domain):
                return True
        return False

    def validate(self, url: str, raw_content: str, region_code: str) -> Tuple[bool, List[Issue], str]:
        issues = []

        if not url:
            issues.append(Issue("critical", "no_source_url", "规则必须提供来源URL"))
            return False, issues, ""

        domain = self.extract_domain(url)
        if not domain:
            issues.append(Issue("critical", "invalid_url", "URL格式无效"))
            return False, issues, ""

        if not self.is_in_whitelist(domain, region_code):
            issues.append(Issue("critical", "unofficial_source",
                              f"来源 {domain} 不在{region_code}法域官方白名单中，禁止入库"))
            return False, issues, ""

        content_hash = hashlib.sha256(raw_content.encode('utf-8')).hexdigest()[:16]
        snapshot_id = f"snap_{region_code}_{content_hash}"

        return True, issues, snapshot_id


class ContentValidator:
    """校验2: 提取内容校验 - 防幻觉、防断章取义"""

    def __init__(self, db: Session):
        self.db = db

    def validate(self, rule: ComplianceRule, source_full_text: str,
                 existing_rules: List[ComplianceRule] = None) -> List[Issue]:
        issues = []

        for keyword in (rule.keywords or []):
            if keyword and keyword not in source_full_text:
                issues.append(Issue(
                    "critical",
                    "hallucination_keyword",
                    f"关键词 '{keyword}' 在原文中未找到，疑似AI幻觉生成"
                ))

        desc = rule.description or ""
        if len(desc) > 10:
            if not self._find_quote_in_source(desc, source_full_text):
                issues.append(Issue(
                    "warning",
                    "quote_not_found",
                    "规则描述未能在原文中找到对应片段，请人工核实上下文是否完整"
                ))

        if existing_rules:
            conflicts = self._check_rule_conflicts(rule, existing_rules)
            issues.extend(conflicts)

        if self._has_contradictory_keywords(rule.keywords or []):
            issues.append(Issue(
                "warning",
                "contradictory_keywords",
                "关键词中存在矛盾组合（如同时包含'禁止'和'允许'相关词），请检查"
            ))

        if rule.patterns:
            for pattern in rule.patterns:
                try:
                    re.compile(pattern)
                except re.error as e:
                    issues.append(Issue("critical", "invalid_regex",
                                       f"正则表达式无效: {pattern}, 错误: {str(e)}"))

        return issues

    def _find_quote_in_source(self, description: str, source_text: str) -> bool:
        desc_words = [w for w in description if len(w) >= 4]
        if not desc_words:
            return True
        match_count = 0
        for word in desc_words[:20]:
            if word in source_text:
                match_count += 1
        return match_count >= min(3, len(desc_words[:20]))

    def _check_rule_conflicts(self, new_rule: ComplianceRule,
                               existing_rules: List[ComplianceRule]) -> List[Issue]:
        issues = []
        new_keywords = set(new_rule.keywords or [])

        for existing in existing_rules:
            existing_keywords = set(existing.keywords or [])
            overlap = new_keywords & existing_keywords

            if overlap and new_rule.rule_type != existing.rule_type:
                type_conflict = (
                    (new_rule.rule_type.value == "prohibited" and existing.rule_type.value == "required") or
                    (new_rule.rule_type.value == "required" and existing.rule_type.value == "prohibited")
                )
                if type_conflict:
                    issues.append(Issue(
                        "critical",
                        "rule_conflict",
                        f"与已有规则[{existing.rule_code} {existing.rule_name}]存在冲突："
                        f"关键词{overlap}在两条规则中要求相反"
                    ))

        return issues

    def _has_contradictory_keywords(self, keywords: List[str]) -> bool:
        positive = {"允许", "可以", "应当", "必须", "得"}
        negative = {"禁止", "不得", "不能", "不可", "严禁"}

        has_positive = any(any(p in k for p in positive) for k in keywords)
        has_negative = any(any(n in k for n in negative) for k in keywords)

        return has_positive and has_negative


class LogicValidator:
    """校验3: 逻辑一致性校验"""

    def __init__(self, db: Session):
        self.db = db

    def validate(self, rule: ComplianceRule, region_code: str) -> List[Issue]:
        issues = []

        now = datetime.utcnow()
        if rule.effective_date:
            if rule.effective_date > now + timedelta(days=365 * 2):
                issues.append(Issue("warning", "date_too_future",
                    "生效日期设置为2年以后，请确认是否正确"))
            if rule.effective_date < now - timedelta(days=365 * 10):
                issues.append(Issue("warning", "date_too_past",
                    "生效日期为10年前，请确认是否为最新版本法规"))

        if rule.expire_date and rule.effective_date:
            if rule.expire_date < rule.effective_date:
                issues.append(Issue("critical", "date_logic_error",
                    "失效日期早于生效日期，日期逻辑错误"))

        severity = rule.severity.value if hasattr(rule.severity, 'value') else str(rule.severity)
        penalty = rule.penalty or ""
        if severity in ["high", "critical"]:
            if penalty and "警告" in penalty and "罚款" not in penalty:
                issues.append(Issue("warning", "severity_penalty_mismatch",
                    f"严重等级为{severity}但处罚仅为警告，等级与处罚可能不匹配"))

        return issues


class RuleValidationService:
    """规则校验服务 - 三重校验入口"""

    def __init__(self, db: Session):
        self.db = db
        self.source_validator = SourceValidator(db)
        self.content_validator = ContentValidator(db)
        self.logic_validator = LogicValidator(db)

    def validate_new_rule(self, rule_data: Dict[str, Any], source_url: str,
                          source_content: str, region_code: str) -> RuleValidationResult:
        all_issues = []

        source_passed, source_issues, snapshot_id = self.source_validator.validate(
            source_url, source_content, region_code
        )
        all_issues.extend(source_issues)

        content_passed = True
        if source_passed:
            existing = self.db.query(ComplianceRule).filter(
                ComplianceRule.is_active == True
            ).all()
            content_issues = self.content_validator.validate(
                self._dict_to_rule(rule_data), source_content, existing
            )
            all_issues.extend(content_issues)
            content_passed = not any(i.level == "critical" for i in content_issues)

        logic_passed = True
        if source_passed:
            logic_issues = self.logic_validator.validate(
                self._dict_to_rule(rule_data), region_code
            )
            all_issues.extend(logic_issues)
            logic_passed = not any(i.level == "critical" for i in logic_issues)

        overall_passed = source_passed and content_passed and logic_passed

        self._save_review_record(rule_data, source_url, source_content,
                                  all_issues, snapshot_id)

        return RuleValidationResult(
            passed=overall_passed,
            issues=[ValidationIssue(level=i.level, type=i.type, message=i.message)
                    for i in all_issues],
            source_valid=source_passed,
            content_valid=content_passed,
            logic_valid=logic_passed,
            snapshot_id=snapshot_id if source_passed else None
        )

    def _dict_to_rule(self, data: Dict[str, Any]) -> ComplianceRule:
        rule = ComplianceRule()
        for key, value in data.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        return rule

    def _save_review_record(self, rule_data: Dict, source_url: str,
                            source_content: str, issues: List[Issue],
                            snapshot_id: str):
        try:
            review = RuleReview(
                rule_id=rule_data.get("id"),
                rule_type="compliance",
                source_validation={"source_url": source_url, "snapshot_id": snapshot_id},
                content_validation={"issues_count": len(issues)},
                logic_validation={},
                source_snapshot=snapshot_id,
                source_context=source_content[:5000],
                review_status="pending"
            )
            self.db.add(review)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to save review record: {e}")
            self.db.rollback()

    def approve_rule(self, review_id: str, reviewer: str, notes: str = "") -> bool:
        review = self.db.query(RuleReview).filter(RuleReview.id == review_id).first()
        if not review:
            return False

        review.review_status = "approved"
        review.reviewed_by = reviewer
        review.reviewed_at = datetime.utcnow()
        review.review_notes = notes
        self.db.commit()
        return True

    def reject_rule(self, review_id: str, reviewer: str, reason: str) -> bool:
        review = self.db.query(RuleReview).filter(RuleReview.id == review_id).first()
        if not review:
            return False

        review.review_status = "rejected"
        review.reviewed_by = reviewer
        review.reviewed_at = datetime.utcnow()
        review.review_notes = reason
        self.db.commit()
        return True

    def create_version(self, rule: ComplianceRule, created_by: str, change_note: str = ""):
        version = RuleVersion(
            rule_id=rule.id,
            rule_type="compliance",
            version=rule.version or "1.0",
            rule_data={
                "rule_code": rule.rule_code,
                "rule_name": rule.rule_name,
                "keywords": rule.keywords,
                "patterns": rule.patterns,
                "description": rule.description,
                "suggestion": rule.suggestion,
            },
            change_note=change_note,
            created_by=created_by
        )
        self.db.add(version)
        self.db.commit()
        return version
