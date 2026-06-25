"""
初始化种子数据 - 法域、行业类目、示例规则
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.models.models import Region, Category, ComplianceRule, AuditCase
import uuid
from datetime import datetime


def new_id():
    return str(uuid.uuid4())


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        existing = db.query(Region).count()
        if existing > 0:
            print("数据库已初始化，跳过...")
            db.close()
            return

        regions = [
            Region(id=new_id(), code="SG", name_cn="新加坡", name_en="Singapore", language="zh"),
            Region(id=new_id(), code="MY", name_cn="马来西亚", name_en="Malaysia", language="zh"),
            Region(id=new_id(), code="TH", name_cn="泰国", name_en="Thailand", language="th"),
            Region(id=new_id(), code="AU", name_cn="澳洲", name_en="Australia", language="en"),
            Region(id=new_id(), code="JP", name_cn="日本", name_en="Japan", language="ja"),
            Region(id=new_id(), code="KR", name_cn="韩国", name_en="Korea", language="ko"),
            Region(id=new_id(), code="IN", name_cn="印度", name_en="India", language="en"),
        ]
        for r in regions:
            db.add(r)
        db.flush()

        sg_region = next(r for r in regions if r.code == "SG")
        my_region = next(r for r in regions if r.code == "MY")

        category = Category(
            id=new_id(),
            name="小家电",
            keywords=["空气净化器", "电饭煲", "吸尘器", "吹风机", "电水壶", "加湿器", "电磁炉"]
        )
        db.add(category)
        db.flush()

        sg_rules = [
            ComplianceRule(
                id=new_id(),
                region_id=sg_region.id,
                category_id=category.id,
                rule_code="SG_PROHIBITED_001",
                rule_name="禁止绝对化用语",
                rule_type="prohibited",
                severity="high",
                keywords=["最", "第一", "顶级", "独家", "极致", "最佳", "最好", "最高级"],
                patterns=[r"最[\u4e00-\u9fa5]{1,8}", r"(第一|顶级|独家|极致|最佳|最好)[\u4e00-\u9fa5]+"],
                description="新加坡广告标准管理局(CSA)规定：广告中不得使用无法证实的绝对化用语，如最、第一、顶级等。",
                suggestion="使用具体数据替代绝对化表述，例如：将最节能改为能效等级3级，经检测能耗降低30%",
                penalty="警告/罚款/最高S$10,000",
                source_url="https://www.csa.org.sg/advertising-code",
                version="1.0",
                review_status="approved",
                effective_date=datetime(2023, 1, 1)
            ),
            ComplianceRule(
                id=new_id(),
                region_id=sg_region.id,
                category_id=category.id,
                rule_code="SG_PROHIBITED_002",
                rule_name="禁止虚假功效声明",
                rule_type="prohibited",
                severity="high",
                keywords=["100%杀菌", "彻底清除", "永久", "一劳永逸", "包治百病"],
                patterns=[],
                description="不得作出无法证实的功效承诺，特别是涉及健康、医疗效果的声明。小家电产品不得宣称具有医疗效果。",
                suggestion="提供具体检测报告和数据支持，避免使用100%、彻底、永久等绝对化词汇",
                penalty="产品下架/罚款/民事赔偿",
                source_url="https://www.csa.org.sg/advertising-code",
                version="1.0",
                review_status="approved",
                effective_date=datetime(2023, 1, 1)
            ),
            ComplianceRule(
                id=new_id(),
                region_id=sg_region.id,
                category_id=category.id,
                rule_code="SG_REQUIRED_001",
                rule_name="能效标识需标注",
                rule_type="required",
                severity="medium",
                keywords=["能效", "节能", "能耗"],
                patterns=[],
                description="涉及能效声明的小家电广告，必须标注能效等级标签来源和检测依据。",
                suggestion="在广告中展示官方能效标识，并注明检测机构名称和报告编号",
                penalty="限期整改",
                source_url="https://www.nea.gov.sg",
                version="1.0",
                review_status="approved",
                effective_date=datetime(2023, 1, 1)
            ),
        ]

        my_rules = [
            ComplianceRule(
                id=new_id(),
                region_id=my_region.id,
                category_id=category.id,
                rule_code="MY_PROHIBITED_001",
                rule_name='禁止使用"皇家"等敏感词汇',
                rule_type="prohibited",
                severity="critical",
                keywords=["皇家", "Royal", "皇室", "苏丹"],
                patterns=[],
                description="马来西亚广告不得使用与皇室、苏丹相关的词汇进行商业宣传，这在马来西亚属于严重违法行为。",
                suggestion="移除所有涉及皇室、皇家、苏丹相关的词汇，使用中性描述替代",
                penalty="严厉罚款/产品下架/法律追责",
                source_url="https://www.kpdnhep.gov.my",
                version="1.0",
                review_status="approved",
                effective_date=datetime(2023, 1, 1)
            ),
            ComplianceRule(
                id=new_id(),
                region_id=my_region.id,
                category_id=category.id,
                rule_code="MY_PROHIBITED_002",
                rule_name="禁止猪肉/不洁物相关表述",
                rule_type="prohibited",
                severity="high",
                keywords=["猪肉", "猪油", "酒精"],
                patterns=[],
                description="马来西亚为穆斯林国家，小家电产品不得暗示与猪肉、酒精等伊斯兰教禁忌物品相关。",
                suggestion="避免提及敏感宗教相关词汇，如有halal认证需在广告中展示真实认证标识",
                penalty="产品下架/罚款/宗教局介入",
                source_url="https://www.kpdnhep.gov.my",
                version="1.0",
                review_status="approved",
                effective_date=datetime(2023, 1, 1)
            ),
        ]

        for rules_list in [sg_rules, my_rules]:
            for rule in rules_list:
                db.add(rule)

        sample_cases = [
            AuditCase(
                id=new_id(),
                title="空气净化器'最净化'绝对化用语被罚案例(新加坡)",
                material_type="text",
                content_text="本品牌空气净化器最净化，最强效，99.99%除菌率",
                violation_type="绝对化用语",
                region_code="SG",
                description="某品牌空气净化器广告使用'最净化'、'最强效'等绝对化用语，被新加坡广告标准局警告并责令整改。",
                decision="整改后通过",
                before_edit=["最净化", "最强效", "99.99%除菌率"],
                after_edit=["CADR值450m³/h", "经检测CADR值450m³/h，适用面积30㎡", "除菌率99.99%（检测报告编号XXX）"],
                reviewer_notes="注意：数据必须有检测报告支持",
                tags=["绝对化用语", "新加坡", "空气净化器"]
            ),
        ]

        for case in sample_cases:
            db.add(case)

        db.commit()
        print("✅ 种子数据初始化完成:")
        print(f"   - 法域: {len(regions)} 个")
        print(f"   - 行业类目: {category.name}")
        print(f"   - 新加坡规则: {len(sg_rules)} 条")
        print(f"   - 马来西亚规则: {len(my_rules)} 条")
        print(f"   - 示例案例: {len(sample_cases)} 个")

    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"❌ 初始化失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
