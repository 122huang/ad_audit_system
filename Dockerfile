# 多阶段构建，减小镜像体积
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# 复制后端代码
COPY backend/ /app/backend/

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist/

# 创建数据目录
RUN mkdir -p /app/backend/data

# 暴露端口
EXPOSE 8000

# 启动命令（自动初始化数据库）
CMD ["sh", "-c", "cd /app/backend && python init_data.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
