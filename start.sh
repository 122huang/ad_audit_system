#!/bin/bash
set -e

echo "🚀 广告审核宝 - 启动中..."

# 进入后端目录
cd "$(dirname "$0")/backend"

# 初始化数据库（如果不存在）
if [ ! -f data/ad_audit.db ]; then
    echo "📦 初始化数据库..."
    python init_data.py
fi

# 启动服务
echo "✅ 服务启动: http://0.0.0.0:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000