# 广告审核宝 - 多法域广告合规审核系统

面向小家电行业的多法域广告合规智能审核工具，支持文字、图片、视频广告审核。

## 功能特性

- **文字广告审核** - 关键词+正则匹配，融合官方法规、自定义经验规则
- **个人知识库** - 上传审核经验文档、自定义规则、历史案例
- **三重法规校验** - 防AI幻觉机制：来源校验+内容校验+逻辑校验
- **7个法域覆盖** - 新加坡、马来西亚、泰国、澳洲、日本、韩国、印度
- **相似案例匹配** - 自动检索历史违规案例提供参考
- **PWA 支持** - 可安装到桌面/手机，像原生 App 一样使用
- 图片审核（OCR）- 开发中
- 视频审核 - 开发中

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + Ant Design 5 + Vite + PWA |
| 后端 | Python FastAPI + SQLAlchemy + SQLite |
| NLP | jieba 分词 |
| 文档解析 | PyPDF2 / python-docx / openpyxl |
| 部署 | Docker / Render.com |

## 快速开始

### 方式一：一键启动（推荐）

```bash
cd ad_audit_system
bash start.sh
```

打开浏览器访问 **http://localhost:8000**，前后端合一，一个端口即可使用。

### 方式二：Docker 部署

```bash
docker build -t ad-audit .
docker run -p 8000:8000 ad-audit
```

### 方式三：开发模式

```bash
# 后端
cd backend
pip install -r requirements.txt
python init_data.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端（另一个终端）
cd frontend
npm install
npm run dev    # 访问 http://localhost:3000
```

## 线上部署

### GitHub + Render.com（免费）

1. 将代码推送到 GitHub 仓库
2. 在 [render.com](https://render.com) 注册并连接 GitHub
3. 项目根目录已有 [render.yaml](render.yaml)，自动识别配置
4. 点击部署，几分钟后即可获得公网访问地址

### Docker 部署到任意服务器

```bash
docker build -t ad-audit .
docker run -d -p 8000:8000 --restart always ad-audit
```

## PWA 安装

在浏览器中打开后，地址栏会出现「安装」图标，点击即可安装到桌面/手机：

| 浏览器 | 安装方式 |
|--------|----------|
| Chrome / Edge | 地址栏右侧「安装」按钮 |
| Safari (iOS) | 分享 → 添加到主屏幕 |
| Chrome (Android) | 自动弹出安装提示 |

## 项目结构

```
ad_audit_system/
├── backend/
│   ├── app/
│   │   ├── api/           # API路由
│   │   │   ├── audit.py   # 审核接口
│   │   │   ├── knowledge.py # 知识库接口
│   │   │   ├── rules.py   # 法规规则接口
│   │   │   └── regions.py # 法域接口
│   │   ├── core/          # 核心配置
│   │   │   ├── config.py  # 配置项
│   │   │   └── database.py # 数据库连接
│   │   ├── models/        # 数据模型
│   │   │   └── models.py  # SQLAlchemy模型
│   │   ├── schemas/       # Pydantic模式
│   │   │   └── schemas.py
│   │   ├── services/      # 业务逻辑
│   │   │   ├── audit_engine.py    # 审核引擎核心
│   │   │   ├── knowledge_service.py # 知识库服务
│   │   │   └── validator.py       # 三重校验（防幻觉）
│   │   └── main.py        # FastAPI入口（含前端托管）
│   ├── init_data.py       # 种子数据初始化
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   ├── manifest.webmanifest  # PWA 配置
│   │   └── pwa-*.png            # PWA 图标
│   ├── src/
│   │   ├── pages/         # 页面组件
│   │   │   ├── Dashboard.jsx  # 首页
│   │   │   ├── TextAudit.jsx  # 文字审核
│   │   │   ├── Knowledge.jsx  # 知识库管理
│   │   │   ├── Rules.jsx      # 法规规则
│   │   │   └── Cases.jsx      # 案例库
│   │   ├── services/
│   │   │   └── api.js     # API请求封装
│   │   └── App.jsx        # 主应用
│   └── vite.config.js     # Vite + PWA 配置
├── Dockerfile             # Docker 构建
├── render.yaml            # Render.com 部署配置
├── start.sh               # 启动脚本
└── .gitignore
```

## 使用指南

### 文字广告审核

1. 选择「广告审核」菜单
2. 输入广告文案
3. 选择目标法域（可多选）
4. 点击「开始审核」
5. 查看结果：强制违规项、经验提示、知识库参考、相似案例

### 添加审核经验

1. 进入「知识库管理」
2. **添加文档**：上传 PDF/Word/TXT 审核笔记，或直接粘贴文本
3. **添加规则**：创建自定义关键词规则（可设为阻断或警告）
4. **录入案例**：添加历史违规案例，系统审核时自动匹配

### 新法规入库校验

1. 进入「法规规则」→「新规则校验」
2. 填写规则信息、关键词、来源URL、原文片段
3. 运行三重校验：
   - 来源校验：URL 是否在官方白名单
   - 内容校验：关键词是否能在原文中找到（防幻觉）
   - 逻辑校验：日期合理性、规则冲突检查

## 已内置示例数据

- **法域**：SG / MY / TH / AU / JP / KR / IN（7个）
- **新加坡规则**：禁止绝对化用语、禁止虚假功效声明、能效标识需标注
- **马来西亚规则**：禁止"皇家"等敏感词汇、禁止猪肉/不洁物相关表述
- **示例案例**：空气净化器"最净化"被罚案例

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/audit/text | 文字广告审核 |
| GET | /api/audit/materials | 审核历史列表 |
| POST | /api/knowledge/documents/text | 创建文本文档 |
| POST | /api/knowledge/documents/upload | 上传文档 |
| GET | /api/knowledge/documents | 文档列表 |
| POST | /api/knowledge/rules | 创建自定义规则 |
| GET | /api/knowledge/rules | 规则列表 |
| POST | /api/knowledge/cases | 创建案例 |
| GET | /api/knowledge/cases | 案例列表 |
| GET | /api/rules | 官方法规列表 |
| POST | /api/rules/validate | 新规则校验 |
| GET | /api/health | 健康检查 |