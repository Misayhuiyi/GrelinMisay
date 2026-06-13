# ============================================================
# GrelinMisay 健身目标管理助手 - Dockerfile
# 多阶段构建，减小最终镜像体积
# ============================================================

# ==================== 阶段1: 构建阶段 ====================
FROM python:3.11-slim AS builder

# 安装 Python 依赖到独立前缀目录
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ==================== 阶段2: 运行阶段 ====================
FROM python:3.11-slim

WORKDIR /app

# 从构建阶段复制依赖到系统目录
COPY --from=builder /install /usr/local

# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && mkdir -p /app/data /app/logs \
    && chown -R appuser:appuser /app

# 复制应用代码
COPY --chown=appuser:appuser . .

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# 启动服务
CMD ["python", "run.py"]
