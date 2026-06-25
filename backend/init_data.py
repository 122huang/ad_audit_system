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


def make_rule(region_id, category_id, code, name, keywords, description, suggestion, penalty, source_url, severity="high", rule_type="prohibited"):
    return ComplianceRule(
        id=new_id(), region_id=region_id, category_id=category_id,
        rule_code=code, rule_name=name, rule_type=rule_type,
        severity=severity, keywords=keywords, patterns=[],
        description=description, suggestion=suggestion,
        penalty=penalty, source_url=source_url,
        version="1.0", review_status="approved",
        effective_date=datetime(2023, 1, 1)
    )


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        existing = db.query(Region).count()
        if existing > 0:
            print("数据库已初始化，跳过...")
            db.close()
            return

        # 法域
        region_data = [
            ("SG", "新加坡", "Singapore", "zh"),
            ("MY", "马来西亚", "Malaysia", "zh"),
            ("TH", "泰国", "Thailand", "th"),
            ("AU", "澳洲", "Australia", "en"),
            ("JP", "日本", "Japan", "ja"),
            ("KR", "韩国", "Korea", "ko"),
            ("IN", "印度", "India", "en"),
        ]
        regions = []
        for code, cn, en, lang in region_data:
            r = Region(id=new_id(), code=code, name_cn=cn, name_en=en, language=lang)
            db.add(r)
            regions.append(r)
        db.flush()

        region_map = {r.code: r for r in regions}

        cat = Category(id=new_id(), name="小家电",
                       keywords=["空气净化器", "电饭煲", "吸尘器", "吹风机", "电水壶", "加湿器", "电磁炉", "榨汁机", "烤箱", "微波炉"])
        db.add(cat)
        db.flush()

        all_rules = []

        # ====== 新加坡 SG ======
        sg = region_map["SG"].id
        all_rules.extend([
            make_rule(sg, cat.id, "SG_001", "禁止绝对化用语",
                      ["最", "第一", "顶级", "独家", "极致", "最佳", "最好", "最高级", "唯一", "首选", "领先", "冠军", "之王", "万能"],
                      "新加坡广告标准管理局(CSA)禁止使用无法证实的绝对化用语",
                      "用具体数据替代，如'能效等级3级，能耗降低30%'", "警告/罚款/S$10,000",
                      "https://www.csa.org.sg/advertising-code"),
            make_rule(sg, cat.id, "SG_002", "禁止虚假功效声明",
                      ["100%杀菌", "彻底清除", "永久", "一劳永逸", "包治百病", "根治", "完全无毒", "零辐射", "绝对安全", "永不损坏"],
                      "不得作出无法证实的功效承诺，尤其涉及健康、医疗效果",
                      "提供检测报告和数据支持，避免绝对化词汇", "产品下架/罚款",
                      "https://www.csa.org.sg/advertising-code"),
            make_rule(sg, cat.id, "SG_003", "禁止贬低竞品",
                      ["比XX好", "秒杀", "完胜", "碾压", "吊打", "甩几条街", "遥遥领先"],
                      "不得通过贬低竞争对手来宣传自家产品",
                      "客观描述产品优势，避免与竞品直接对比", "警告/罚款",
                      "https://www.csa.org.sg/advertising-code"),
            make_rule(sg, cat.id, "SG_004", "能效标识必须标注",
                      ["能效", "节能", "省电", "低功耗", "环保"],
                      "涉及能效声明的小家电广告必须标注能效等级和检测依据",
                      "展示官方能效标识，注明检测机构名称和报告编号", "限期整改",
                      "https://www.nea.gov.sg", severity="medium", rule_type="required"),
            make_rule(sg, cat.id, "SG_005", "禁止未经证实的认证宣称",
                      ["通过认证", "国际认证", "权威认证", "官方认证", "ISO认证", "CE认证"],
                      "声称产品通过某认证时必须提供真实证书编号和发证机构",
                      "在广告中展示认证证书编号和发证机构名称", "罚款/产品下架",
                      "https://www.csa.org.sg/advertising-code"),
            make_rule(sg, cat.id, "SG_006", "价格声明需真实",
                      ["原价", "市场价", "建议零售价", "折扣", "特价", "促销", "限时优惠"],
                      "价格对比广告必须基于真实的历史售价，不得虚构原价",
                      "保留历史售价记录，促销广告注明促销期限", "罚款",
                      "https://www.csa.org.sg/advertising-code", severity="medium", rule_type="restricted"),
        ])

        # ====== 马来西亚 MY ======
        my = region_map["MY"].id
        all_rules.extend([
            make_rule(my, cat.id, "MY_001", "禁止使用皇室相关词汇",
                      ["皇家", "Royal", "皇室", "苏丹", "陛下", "王宫", "御用"],
                      "马来西亚广告不得使用与皇室、苏丹相关的词汇进行商业宣传",
                      "移除所有涉及皇室、皇家、苏丹相关的词汇", "严厉罚款/法律追责",
                      "https://www.kpdnhep.gov.my", severity="critical"),
            make_rule(my, cat.id, "MY_002", "禁止猪肉/不洁物相关表述",
                      ["猪肉", "猪油", "酒精", "酒", "啤酒", "白酒", "不洁"],
                      "马来西亚为穆斯林国家，不得暗示与猪肉、酒精等伊斯兰禁忌相关",
                      "避免提及敏感宗教词汇，如有Halal认证需展示真实认证标识", "产品下架/罚款",
                      "https://www.kpdnhep.gov.my"),
            make_rule(my, cat.id, "MY_003", "Halal认证需真实",
                      ["清真", "Halal", "halal", "伊斯兰"],
                      "声称Halal认证的产品必须持有JAKIM颁发的有效证书",
                      "展示JAKIM Halal证书编号和有效期", "产品下架/罚款",
                      "https://www.halal.gov.my", severity="critical"),
            make_rule(my, cat.id, "MY_004", "禁止虚假促销",
                      ["免费", "赠送", "买一送一", "大减价", "清仓", "跳楼价"],
                      "促销广告必须真实，不得以虚假促销诱导消费者",
                      "促销活动需注明活动期限和具体条件", "罚款",
                      "https://www.kpdnhep.gov.my", severity="medium", rule_type="restricted"),
            make_rule(my, cat.id, "MY_005", "禁止绝对化用语",
                      ["最", "第一", "顶级", "独家", "最好", "唯一", "冠军", "领先"],
                      "马来西亚广告法禁止使用无法证实的绝对化用语",
                      "使用具体数据替代绝对化表述", "警告/罚款",
                      "https://www.kpdnhep.gov.my", severity="high"),
        ])

        # ====== 泰国 TH ======
        th = region_map["TH"].id
        all_rules.extend([
            make_rule(th, cat.id, "TH_001", "禁止贬低王室",
                      ["王室", "国王", "皇室", "陛下", "公主", "王子"],
                      "泰国严禁任何涉及王室的商业广告，违反者将面临严厉处罚",
                      "彻底移除所有涉及泰国王室的词汇和暗示", "严厉法律处罚",
                      "https://www.cpall.co.th", severity="critical"),
            make_rule(th, cat.id, "TH_002", "禁止虚假广告",
                      ["100%", "绝对", "永久", "终身", "永不", "万能"],
                      "泰国消费者保护法禁止虚假或夸大广告",
                      "提供真实数据和检测报告", "罚款/监禁",
                      "https://www.ocpb.go.th"),
            make_rule(th, cat.id, "TH_003", "需标注泰语说明",
                      [],
                      "在泰国销售的电器产品广告必须包含泰语使用说明和安全警告",
                      "添加泰语版产品说明和安全警告", "限期整改",
                      "https://www.ocpb.go.th", severity="medium", rule_type="required"),
        ])

        # ====== 澳洲 AU ======
        au = region_map["AU"].id
        all_rules.extend([
            make_rule(au, cat.id, "AU_001", "禁止误导性声明",
                      ["best", "guaranteed", "100%", "miracle", "cure", "instant", "free"],
                      "澳大利亚消费者法(ACL)禁止误导或欺骗性广告声明",
                      "使用客观数据和事实描述产品", "罚款/AU$10M+",
                      "https://www.accc.gov.au"),
            make_rule(au, cat.id, "AU_002", "能效标识强制要求",
                      ["energy", "efficient", "power", "saving", "eco", "green"],
                      "澳洲小家电必须标注能效星级评级(Energy Rating Label)",
                      "在广告中展示Energy Rating标签", "罚款/产品下架",
                      "https://www.energyrating.gov.au", severity="medium", rule_type="required"),
            make_rule(au, cat.id, "AU_003", "安全标准必须符合",
                      ["safe", "safety", "child", "protected"],
                      "电器产品必须符合AS/NZS安全标准，广告中安全声明需有认证支持",
                      "展示安全认证标志和标准编号", "产品召回/罚款",
                      "https://www.productsafety.gov.au"),
        ])

        # ====== 日本 JP ======
        jp = region_map["JP"].id
        all_rules.extend([
            make_rule(jp, cat.id, "JP_001", "禁止景品表示法违规",
                      ["最高", "日本一", "No.1", "完全", "绝对", "永久", "無料", "只今"],
                      "日本景品表示法禁止不当表示(优良误认/有利误认)",
                      "提供客观数据支持，避免主观夸大", "罚款/业务改善命令",
                      "https://www.caa.go.jp"),
            make_rule(jp, cat.id, "JP_002", "JIS/PSE认证需标注",
                      ["安全", "安心", "認証", "検査", "基準"],
                      "电器产品需符合PSE认证要求，安全声明需有认证支持",
                      "展示PSE认证标志和安全标准符合声明", "产品下架/罚款",
                      "https://www.meti.go.jp", severity="medium", rule_type="required"),
            make_rule(jp, cat.id, "JP_003", "药机法禁止医疗效果宣称",
                      ["治療", "治癒", "予防", "改善", "効果", "健康"],
                      "电器产品不得宣称具有医疗或治疗效果",
                      "避免使用医疗相关词汇，改为功能描述", "罚款/产品下架",
                      "https://www.mhlw.go.jp"),
        ])

        # ====== 韩国 KR ======
        kr = region_map["KR"].id
        all_rules.extend([
            make_rule(kr, cat.id, "KR_001", "禁止夸大广告",
                      ["최고", "1위", "완벽", "100%", "절대", "영구", "완전"],
                      "韩国标示广告法禁止夸大或虚假广告",
                      "使用客观数据，标注测试条件和机构", "罚款/产品下架",
                      "https://www.kca.go.kr"),
            make_rule(kr, cat.id, "KR_002", "KC认证需标注",
                      ["안전", "인증", "검증", "테스트", "품질"],
                      "电器产品需取得KC认证，安全/质量声明需有认证支持",
                      "展示KC认证标志和证书编号", "产品下架/罚款",
                      "https://www.kats.go.kr", severity="medium", rule_type="required"),
            make_rule(kr, cat.id, "KR_003", "禁止不当比较广告",
                      ["보다", "더", "비교", "차별", "우월"],
                      "比较广告需基于客观事实，不得贬低竞品",
                      "使用具体数据比较，注明数据来源和测试条件", "警告/罚款",
                      "https://www.kca.go.kr", severity="medium", rule_type="restricted"),
        ])

        # ====== 印度 IN ======
        ind = region_map["IN"].id
        all_rules.extend([
            make_rule(ind, cat.id, "IN_001", "禁止误导性广告",
                      ["best", "guaranteed", "100%", "miracle", "magic", "instant", "free"],
                      "印度消费者保护法禁止误导性广告声明",
                      "使用客观数据，避免夸大宣传", "罚款/监禁",
                      "https://consumeraffairs.nic.in"),
            make_rule(ind, cat.id, "IN_002", "BIS认证需标注",
                      ["certified", "approved", "tested", "quality", "standard"],
                      "电器产品需符合BIS认证标准，质量声明需有认证支持",
                      "展示BIS认证标志和ISI编号", "产品下架/罚款",
                      "https://www.bis.gov.in", severity="medium", rule_type="required"),
            make_rule(ind, cat.id, "IN_003", "禁止宗教敏感内容",
                      ["god", "hindu", "muslim", "temple", "prayer", "holy"],
                      "广告不得涉及宗教敏感内容或利用宗教信仰进行促销",
                      "移除所有宗教相关内容，保持广告中立", "罚款/产品抵制",
                      "https://consumeraffairs.nic.in", severity="critical"),
        ])

        for rule in all_rules:
            db.add(rule)

        # 示例案例
        sample_cases = [
            AuditCase(
                id=new_id(), title="空气净化器'最净化'被罚案例(新加坡)",
                material_type="text",
                content_text="本品牌空气净化器最净化，最强效，99.99%除菌率",
                violation_type="绝对化用语", region_code="SG",
                description="某品牌空气净化器广告使用'最净化'、'最强效'等绝对化用语，被新加坡广告标准局警告并责令整改。",
                decision="整改后通过",
                before_edit=["最净化", "最强效", "99.99%除菌率"],
                after_edit=["CADR值450m³/h", "经检测CADR值450m³/h，适用面积30㎡", "除菌率99.99%（检测报告编号XXX）"],
                reviewer_notes="注意：数据必须有检测报告支持",
                tags=["绝对化用语", "新加坡", "空气净化器"]
            ),
            AuditCase(
                id=new_id(), title="电饭煲'皇家品质'被罚案例(马来西亚)",
                material_type="text",
                content_text="皇家品质电饭煲，为皇室打造的烹饪体验",
                violation_type="皇室敏感词", region_code="MY",
                description="某品牌电饭煲广告使用'皇家'、'皇室'等词汇，违反马来西亚广告法，被严厉处罚。",
                decision="罚款+整改",
                before_edit=["皇家品质", "为皇室打造"],
                after_edit=["高品质", "精湛工艺打造"],
                reviewer_notes="马来西亚对皇室相关词汇零容忍",
                tags=["皇室", "马来西亚", "电饭煲"]
            ),
            AuditCase(
                id=new_id(), title="吹风机'日本一'被罚案例(日本)",
                material_type="text",
                content_text="日本一の品質、最高級ドライヤー",
                violation_type="景品表示法违规", region_code="JP",
                description="某吹风机广告使用'日本一'（日本第一）表述，违反景品表示法，被消费者厅发出业务改善命令。",
                decision="业务改善命令",
                before_edit=["日本一の品質", "最高級"],
                after_edit=["厳選された品質", "プレミアムグレード"],
                reviewer_notes="日本对'No.1'类表述审查非常严格",
                tags=["日本一", "日本", "吹风机", "景品表示法"]
            ),
        ]
        for case in sample_cases:
            db.add(case)

        db.commit()
        print("✅ 种子数据初始化完成:")
        print(f"   - 法域: {len(regions)} 个")
        print(f"   - 行业类目: {cat.name}")
        print(f"   - 合规规则: {len(all_rules)} 条")
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