"""
导入 ad-claim-review skill 到知识库
1. 将完整 skill 文档作为知识库文档导入
2. 从 skill 中提取 A-K 十一类关键规则词，创建自定义规则
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.services.knowledge_service import KnowledgeService
import uuid


def new_id():
    return str(uuid.uuid4())


def import_skill():
    db = SessionLocal()
    service = KnowledgeService(db)

    # 读取 skill 文档
    skill_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "ad-claim-review.md")
    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 导入完整 skill 文档到知识库
    print("📄 导入 skill 文档到知识库...")
    try:
        doc = service.create_document_from_text(
            title="广告宣传词合规审核 Skill v4（A-K 十一类风险 + SG/MY/TH 国别附录）",
            doc_type="internal",
            content=content,
            region_code=None,
            tags=["skill", "审核标准", "合规审核", "出海广告", "东南亚"],
            source="用户上传的审核 skill"
        )
        print(f"   ✅ 文档已导入: {doc.title}")
    except Exception as e:
        print(f"   ⚠️ 文档导入异常: {e}")

    # 2. 从 skill 提取 A-K 规则并创建自定义规则
    print("\n📋 提取 A-K 关键规则词...")

    rules = [
        # A. 本地化残留
        {
            "rule_name": "A-本地化残留与内部批注",
            "rule_type": "prohibited",
            "keywords": ["Change to", "待补充", "待确认", "TBD", "INSERT", "placeholder", "接洽当地", "此处替换"],
            "description": "禁止出现内部批注、占位符、草稿标记等未完成内容",
            "severity": "high",
            "suggestion": "删除所有内部批注和占位符，做一次全量盲审"
        },
        # B. 健康功能宣示
        {
            "rule_name": "B-健康功能宣示（医疗器械级监管风险）",
            "rule_type": "prohibited",
            "keywords": ["Healthier", "Healthy", "Nourishing", "Sterilize", "Sterilization",
                         "Anti-bacterial", "Detox", "Cleanse", "Boost immunity",
                         "Doctor-recommended", "Clinically proven", "Medical-grade",
                         "Pharmaceutical-grade", "Easy to digest", "Gentle on the stomach"],
            "description": "禁止非医疗/保健食品类产品做健康功效暗示，触发医疗器械级监管",
            "severity": "critical",
            "suggestion": "软化为事实性描述，或加 disclaimer 并附第三方检测报告"
        },
        # C. 食品安全
        {
            "rule_name": "C-食品安全与产品责任风险",
            "rule_type": "prohibited",
            "keywords": ["24-hour timer", "overnight", "Load before bed", "Prep tonight",
                         "12-hour preset", "fresh in the morning", "Come home to"],
            "description": "禁止宣传长时间室温存放食材的场景，可能导致食物中毒 PL 索赔",
            "severity": "high",
            "suggestion": "改为非生鲜食材场景，并加 disclaimer"
        },
        # D. 绝对化用词
        {
            "rule_name": "D-绝对化用词与无支撑数据宣示",
            "rule_type": "prohibited",
            "keywords": ["Best", "#1", "No.1", "Perfect", "Perfectly", "Flawless",
                         "100%", "Zero", "Complete", "Absolute", "Ultimate",
                         "Revolutionizes", "Game-changing", "Endless", "Infinite",
                         "Lasts forever", "Never fails", "Every time"],
            "description": "禁止使用无法证实的绝对化用词和最高级表述",
            "severity": "high",
            "suggestion": "替换为事实性表述，如 'engineered for'、'designed to'"
        },
        # E. 同业贬损
        {
            "rule_name": "E-同业贬损式对比",
            "rule_type": "prohibited",
            "keywords": ["Lower-grade", "inferior quality", "cheap alternatives",
                         "Traditional motors", "conventional", "ordinary products"],
            "description": "禁止使用模糊基准贬损竞品，比较广告须可识别可验证",
            "severity": "high",
            "suggestion": "删除贬损式对比，或改为明确对照物 + 测试条件 + 报告编号"
        },
        # F. 专利商标地域错配
        {
            "rule_name": "F-专利与商标地域错配",
            "rule_type": "prohibited",
            "keywords": ["Patented", "Patent Pending", "专利", "实用新型专利"],
            "description": "禁止在海外宣传未经目的国授权的专利",
            "severity": "high",
            "suggestion": "删除或改为 'patented in China'，核查目的国同族专利"
        },
        # G. 中国机构认证
        {
            "rule_name": "G-中国机构/标准/认证用于海外宣传",
            "rule_type": "prohibited",
            "keywords": ["GB/T", "GB ", "CHCT", "CQC", "CVC", "威凯",
                         "鲁班奖", "国家科技进步奖", "national standard", "市监局"],
            "description": "禁止将中国国内标准/认证/机构用于海外市场宣传，构成误导",
            "severity": "high",
            "suggestion": "替换为国际通行机构（SGS、TÜV、Intertek）或目的国认证"
        },
        # I. 涂层与材料
        {
            "rule_name": "I-涂层与材料声明",
            "rule_type": "prohibited",
            "keywords": ["never peel", "零脱落", "永不粘锅", "永不脱落",
                         "non-stick forever", "永久不粘", "everlasting coating"],
            "description": "禁止使用绝对化涂层耐久性声明，需有测试报告支撑",
            "severity": "high",
            "suggestion": "改为限定条件表述，如 '经 XX 次耐磨测试验证'"
        },
        # J. 绿色声明
        {
            "rule_name": "J-绿色/可持续声明",
            "rule_type": "prohibited",
            "keywords": ["Eco-friendly", "Sustainable", "Carbon neutral",
                         "Zero carbon", "BPA-free", "Food-grade", "Non-toxic",
                         "Natural material", "Good for the planet", "Green"],
            "description": "禁止无支撑的环保/绿色声明，须有认证机构背书",
            "severity": "medium",
            "suggestion": "加具体说明（如 'made with 30% recycled plastic'），附检测报告"
        },
        # K. 促销定价
        {
            "rule_name": "K-促销定价话术",
            "rule_type": "prohibited",
            "keywords": ["Was $", "Sale ends today", "Last 24 hours",
                         "Only X left", "Limited stock", "Closing down sale",
                         "Moving sale", "限时抢购", "最后一天"],
            "description": "禁止虚假促销/限时/稀缺话术，须真实有效",
            "severity": "medium",
            "suggestion": "确认促销真实性，标明准确截止时间，使用真实库存"
        },
        # Q. 文字质检
        {
            "rule_name": "Q-文字质检（错别字与语法）",
            "rule_type": "prohibited",
            "keywords": ["22:00PM", "presets", "more enjoying", "Extra more",
                         "when you back home", "Draft", "草稿"],
            "description": "禁止出现错别字、语法错误、草稿标记",
            "severity": "medium",
            "suggestion": "修正拼写/语法错误，删除草稿标记"
        },
    ]

    for rule_data in rules:
        try:
            cr = service.create_custom_rule(
                user_id="system",
                rule_name=rule_data["rule_name"],
                rule_type=rule_data["rule_type"],
                keywords=rule_data["keywords"],
                patterns=[],
                description=rule_data["description"],
                suggestion=rule_data["suggestion"],
                region_code=None,
                severity=rule_data["severity"]
            )
            print(f"   ✅ 规则已创建: {rule_data['rule_name']} ({len(rule_data['keywords'])} 关键词)")
        except Exception as e:
            print(f"   ⚠️ 规则创建失败: {rule_data['rule_name']} - {e}")

    db.close()
    print("\n🎉 Skill 导入完成！")


if __name__ == "__main__":
    import_skill()