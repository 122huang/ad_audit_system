"""
高级审核引擎 - 实现 ad-claim-review skill 的 R01/R02 双轮审核框架
R01: A-K 十一类风险扫描 + 文字质检 + 执法案例
R02: 证据充分性审查
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models.models import Region

logger = logging.getLogger(__name__)

# ── R01 风险分类定义 ──────────────────────────────────────────

RISK_CATEGORIES = {
    "A": {
        "name": "本地化残留、内部批注与视觉展示合规",
        "keywords": ["Change to", "待补充", "待确认", "TBD", "INSERT", "placeholder",
                      "接洽当地", "此处替换", "English version", "中文面板", "五常米", "东北大米",
                      "10A 评级", "5A 品质", "水印"],
        "type": "🔴 强制修改",
        "description": "物料中出现内部批注、占位符、中文面板、中国特有地理标志等未完成内容"
    },
    "B": {
        "name": "健康功能宣示（医疗器械级监管风险）",
        "keywords": ["Healthier", "Healthy", "Nourishing", "Sterilize", "Sterilization",
                      "Anti-bacterial", "Detox", "Cleanse", "Boost immunity",
                      "Doctor-recommended", "Clinically proven", "Medical-grade",
                      "Pharmaceutical-grade", "Easy to digest", "Gentle on the stomach",
                      "滋补", "养胃", "排毒", "增强免疫力", "医生推荐"],
        "type": "🔴 强制修改",
        "description": "非医疗/保健食品类产品做健康功效暗示，触发医疗器械级监管"
    },
    "C": {
        "name": "食品安全与产品责任风险",
        "keywords": ["24-hour timer", "overnight", "Load before bed", "Prep tonight",
                      "12-hour preset", "fresh in the morning", "Come home to",
                      "隔夜", "定时烹饪", "晚上放食材", "第二天自动"],
        "type": "🔴 强制修改",
        "description": "宣传长时间室温存放食材的场景，可能导致食物中毒 PL 索赔"
    },
    "D": {
        "name": "绝对化用词与无支撑数据宣示",
        "keywords": ["Best", "#1", "No.1", "Perfect", "Perfectly", "Flawless",
                      "100%", "Zero", "Complete", "Absolute", "Ultimate",
                      "Revolutionizes", "Game-changing", "Endless", "Infinite",
                      "Lasts forever", "Never fails", "Every time", "万能", "极致"],
        "type": "🔴 强制修改",
        "description": "使用无法证实的绝对化用词和最高级表述"
    },
    "E": {
        "name": "同级产品对比贬损与同业贬损",
        "keywords": ["Lower-grade", "inferior quality", "cheap alternatives",
                      "Traditional motors", "conventional", "ordinary products",
                      "普通", "传统", "低档", "劣质"],
        "type": "🔴 强制修改",
        "description": "使用模糊基准贬损竞品，比较广告须可识别可验证"
    },
    "F": {
        "name": "专利与商标地域错配",
        "keywords": ["Patented", "Patent Pending", "专利", "实用新型专利",
                      "外观设计专利", "发明专利"],
        "type": "🔴 强制修改",
        "description": "在海外宣传未经目的国授权的专利，构成误导"
    },
    "G": {
        "name": "中国机构/标准/认证用于海外宣传",
        "keywords": ["GB/T", "GB ", "CHCT", "CQC", "CVC", "威凯",
                      "鲁班奖", "国家科技进步奖", "national standard", "市监局",
                      "3C认证", "中国质量认证", "SGS-CSTC"],
        "type": "🔴 强制修改",
        "description": "将中国国内标准/认证/机构用于海外市场宣传，构成误导"
    },
    "H": {
        "name": "产品描述前后不一致",
        "keywords": [],  # 需要跨页对照，关键词无法覆盖
        "type": "🟡 业务确认",
        "description": "需跨页交叉对照：材质、容量、型号、品牌名是否一致"
    },
    "I": {
        "name": "涂层与材料声明",
        "keywords": ["never peel", "零脱落", "永不粘锅", "永不脱落",
                      "non-stick forever", "永久不粘", "everlasting coating",
                      "0 coating", "零涂层", "无涂层"],
        "type": "🟡 业务确认",
        "description": "涂层耐久性声明需有测试报告支撑；零涂层声明需确认实际材质"
    },
    "J": {
        "name": "绿色/可持续声明",
        "keywords": ["Eco-friendly", "Sustainable", "Carbon neutral",
                      "Zero carbon", "BPA-free", "Food-grade", "Non-toxic",
                      "Natural material", "Good for the planet", "Green",
                      "环保", "可降解", "碳中和"],
        "type": "🟡 业务确认",
        "description": "环保/绿色声明须有认证机构背书和检测报告"
    },
    "K": {
        "name": "促销定价话术",
        "keywords": ["Was $", "Sale ends today", "Last 24 hours",
                      "Only X left", "Limited stock", "Closing down sale",
                      "Moving sale", "限时抢购", "最后一天", "清仓"],
        "type": "🟡 业务确认",
        "description": "促销/限时/稀缺话术须真实有效，时间准确"
    },
}

# 文字质检
TEXT_QUALITY_RULES = {
    "Q1": {
        "name": "内部笔记与草稿残留",
        "keywords": ["[INSERT]", "[TBD]", "[待补充]", "Draft", "草稿", "审阅批注"],
        "type": "🔴 强制修改",
    },
    "Q2": {
        "name": "错别字与语法错误",
        "keywords": ["22:00PM", "presets", "more enjoying", "Extra more",
                      "when you back home", "presents"],
        "type": "🔴 强制修改",
    },
    "Q3": {
        "name": "前后矛盾",
        "keywords": [],  # 需要上下文分析
        "type": "🔴 强制修改",
    },
}

# 🟡 业务确认需要补充的证明材料模板
EVIDENCE_REQUIREMENTS = {
    "B": "第三方实验室测试报告（如 SGS/Intertek/TÜV），或加 disclaimer",
    "C": "食品安全场景说明，改为非生鲜食材场景，或加 disclaimer",
    "D": "具体数据来源及测试条件说明",
    "I": "涂层耐磨测试报告（如 EN 12983 标准），或材质证明",
    "J": "第三方检测报告（BPA迁移测试、食品级材料证明等），或认证证书",
    "K": "历史价格记录截图，促销活动时间范围说明",
    "F": "目的国专利号或同族专利信息",
    "G": "目的国对应认证（如 CPSO/SIRIM/TISI mark）",
}


class AdvancedAuditEngine:
    """R01/R02 高级审核引擎"""

    def __init__(self, db: Session):
        self.db = db

    def audit_r01(self, text: str, regions: List[str], category: str = "") -> Dict[str, Any]:
        """
        R01: 文案扫描 → 输出风险清单 + 需要举证材料的宣称清单
        按 A-K 十一节系统扫描 + 文字质检
        """
        forced_changes = []    # 🔴 强制修改
        biz_confirm = []       # 🟡 业务确认
        reminders = []         # 🟢 仅提醒
        text_quality = []      # ✏️ 文字质检
        evidence_required = [] # 需要举证的宣称

        # 扫描 A-K 风险类别
        for cat_code, cat_info in RISK_CATEGORIES.items():
            for keyword in cat_info["keywords"]:
                if keyword and keyword.lower() in text.lower():
                    item = {
                        "category": cat_code,
                        "category_name": cat_info["name"],
                        "matched_keyword": keyword,
                        "description": cat_info["description"],
                        "risk_type": cat_info["type"],
                        "suggestion": self._get_suggestion(cat_code, keyword),
                    }
                    if cat_info["type"] == "🔴 强制修改":
                        forced_changes.append(item)
                    elif cat_info["type"] == "🟡 业务确认":
                        biz_confirm.append(item)
                        if cat_code in EVIDENCE_REQUIREMENTS:
                            item["evidence_required"] = EVIDENCE_REQUIREMENTS[cat_code]
                    else:
                        reminders.append(item)

        # 扫描文字质检
        for q_code, q_info in TEXT_QUALITY_RULES.items():
            for keyword in q_info["keywords"]:
                if keyword and keyword.lower() in text.lower():
                    text_quality.append({
                        "category": q_code,
                        "category_name": q_info["name"],
                        "matched_keyword": keyword,
                        "risk_type": q_info["type"],
                        "suggestion": f"修正或删除: {keyword}",
                    })

        # 计算风险等级
        overall_risk = self._compute_r01_risk(forced_changes, biz_confirm, reminders)

        return {
            "review_type": "R01",
            "overall_risk": overall_risk,
            "reviewed_at": datetime.utcnow().isoformat() + "Z",
            "regions": regions,
            "category": category,
            "forced_changes": forced_changes,
            "biz_confirm": biz_confirm,
            "reminders": reminders,
            "text_quality": text_quality,
            "summary": {
                "forced_count": len(forced_changes),
                "biz_confirm_count": len(biz_confirm),
                "reminder_count": len(reminders),
                "text_quality_count": len(text_quality),
                "total_issues": len(forced_changes) + len(biz_confirm) + len(reminders) + len(text_quality),
            },
            "next_step": f"请上传相关测试报告/认证文件，进入 R02 证据充分性审查。" if biz_confirm else "审查完成，无需额外证据。"
        }

    def audit_r02(self, r01_result: Dict[str, Any], evidence_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        R02: 证据充分性审查
        evidence_files: [{"name": "文件名", "type": "机构/类型", "date": "日期", "covers": "覆盖宣称"}]
        """
        results = []
        sufficient = 0
        partial = 0
        insufficient = 0

        for item in r01_result.get("biz_confirm", []):
            # 检查是否有对应证据
            matched_evidence = []
            for ev in evidence_files:
                covers = ev.get("covers", "")
                if isinstance(covers, list):
                    if item["category"] in covers:
                        matched_evidence.append(ev)
                elif item["category"] in str(covers):
                    matched_evidence.append(ev)

            # 五维度评估
            if not matched_evidence:
                rating = "❌ 不充分"
                insufficient += 1
                reason = "未提供对应证明文件"
            else:
                # 简化评估：有文件即部分充分，有国际机构文件即充分
                ev = matched_evidence[0]
                ev_type = ev.get("type", "").lower()
                international = any(w in ev_type for w in ["sgs", "intertek", "tüv", "tuv", "bureau veritas", "bsi"])
                if international:
                    rating = "✅ 充分"
                    sufficient += 1
                    reason = f"有国际认可机构({ev.get('type', '')})出具的报告"
                else:
                    rating = "⚠️ 部分充分"
                    partial += 1
                    reason = f"有证据文件({ev.get('name', '')})，建议补充国际机构报告"

            results.append({
                "category": item["category"],
                "category_name": item["category_name"],
                "original_claim": item["matched_keyword"],
                "evidence_files": [e["name"] for e in matched_evidence],
                "rating": rating,
                "reason": reason,
                "action": self._get_r02_action(rating, item["category"]),
            })

        # 整体合规结论
        if insufficient > 0:
            conclusion = "修改后可上线"
            conclusion_detail = f"有 {insufficient} 项宣称证据不充分，须修改或补充材料"
        elif partial > 0:
            conclusion = "可上线（需加限定条件）"
            conclusion_detail = f"有 {partial} 项宣称需加注限定条件"
        else:
            conclusion = "可上线"
            conclusion_detail = "所有宣称均有充分证据支撑"

        return {
            "review_type": "R02",
            "reviewed_at": datetime.utcnow().isoformat() + "Z",
            "evidence_review": results,
            "conclusion": conclusion,
            "conclusion_detail": conclusion_detail,
            "summary": {
                "sufficient": sufficient,
                "partial": partial,
                "insufficient": insufficient,
                "total": len(results),
            }
        }

    def _get_suggestion(self, cat_code: str, keyword: str) -> str:
        """获取修改建议"""
        suggestions = {
            "A": "删除所有内部批注和占位符，做一次全量盲审",
            "B": "软化为事实性描述，或加 disclaimer 并附第三方检测报告",
            "C": "改为非生鲜食材场景，并加 disclaimer: 'for non-perishable ingredients only'",
            "D": f"将 '{keyword}' 替换为事实性表述，如 'engineered for'、'designed to'",
            "E": "删除贬损式对比，或改为明确对照物 + 测试条件 + 报告编号",
            "F": "删除 'Patented' 用词，或改为 'patented in China'，核查目的国同族专利",
            "G": "替换为国际通行机构（SGS、TÜV、Intertek）或目的国对应认证",
            "I": "改为限定条件表述，如 '经 XX 次耐磨测试验证'，或提供检测报告",
            "J": "加具体说明或附第三方检测报告（SGS/Intertek 等）",
            "K": "确认促销真实性，标明准确截止时间，使用真实库存",
        }
        return suggestions.get(cat_code, "请参照 skill 中对应章节的建议处理")

    def _get_r02_action(self, rating: str, cat_code: str) -> str:
        if "✅" in rating:
            return "该宣称可保留"
        if "⚠️" in rating:
            return f"可保留，但须标注: {EVIDENCE_REQUIREMENTS.get(cat_code, '加注限定条件')}"
        return "须修改或删除该宣称，或重新提供充分证据"

    def _compute_r01_risk(self, forced: List, biz: List, reminders: List) -> str:
        """计算 R01 综合风险等级"""
        critical_keywords = ["Sterilize", "Medical-grade", "Doctor-recommended", "Anti-bacterial",
                             "排毒", "增强免疫力", "overnight", "隔夜"]
        has_critical = any(
            item["matched_keyword"] in critical_keywords
            for item in forced
        )
        if has_critical or len(forced) >= 5:
            return "critical"
        if len(forced) >= 3:
            return "high"
        if len(forced) >= 1 or len(biz) >= 2:
            return "medium"
        if biz or reminders:
            return "low"
        return "low"