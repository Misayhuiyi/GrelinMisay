# ============================================================
# ReAct+CoT AI Agent 智能助手 - Dockerfile
# 多阶段构建，减小最终镜像体积
# ============================================================

# ==================== 阶段1: 构建阶段 ====================
FROM python:3.11-slim AS builder

# 安装依赖到中性目录（避免绑定到特定用户）
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/install -r requirements.txt

# ==================== 阶段2: 运行阶段 ====================
FROM python:3.11-slim

WORKDIR /app

# 从构建阶段复制已安装的包到系统目录（对所有用户可见）
COPY --from=builder /install /usr/local/lib/python3.11/site-packages/

# 创建非 root 用户运行应用（安全最佳实践）
RUN groupadd -r agent && useradd -r -g agent agent \
    && mkdir -p /app/data /app/logs \
    && chown -R agent:agent /app

# 复制应用代码
COPY --chown=agent:agent . .

# 切换到非 root 用户
USER agent

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# 启动服务
CMD ["python", "run.py"]
