# GrelinMisay 部署指南

**适用版本**: MVP v1.1 (含验证码登录 + AI 个性化)

## 一、项目结构

```
GrelinMisay/
├── app/                    # FastAPI 后端
│   ├── api/                # API 路由（认证/用户/目标/训练/日历/AI）
│   │   ├── g_auth.py       # 认证（密码登录+验证码登录+注册）
│   │   ├── g_users.py      # 用户资料
│   │   ├── g_goals.py      # 目标管理
│   │   ├── g_training.py   # 训练记录
│   │   ├── g_calendar.py   # 日历事件
│   │   ├── g_ai.py         # AI 对话（含用户个性化称呼）
│   │   ├── g_schemas.py    # 请求/响应模型
│   │   └── router.py       # 路由注册
│   ├── agent/              # ReAct 推理引擎
│   ├── tools/              # 内置工具
│   ├── memory/             # 记忆管理
│   ├── core/               # 核心配置
│   ├── db/                 # 数据库模型
│   └── main.py             # 入口文件
├── grelinmisay-app/        # 前端 (Vite + React)
│   ├── src/
│   │   ├── pages/          # 页面组件（登录/注册/首页/目标/训练/个人/AI）
│   │   ├── services/       # API 服务层
│   │   └── taro-adapter/   # Taro 适配层
│   └── dist/               # 构建输出目录
├── data/                   # 数据目录 (SQLite)
├── run.py                  # 开发启动入口
├── requirements.txt        # Python 依赖
├── GrelinMisay_PRD_v1.1.0.md   # 产品需求文档
├── GrelinMisay_迭代复盘_v1.0.md # 迭代复盘文档
└── DEPLOY_GUIDE.md         # 本文档
```

## 二、云服务器部署 (Ubuntu 20.04+)

### 1. 环境准备

```bash
# 安装 Python 3.10+
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip

# 安装 Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 安装 Nginx
sudo apt install -y nginx

# 安装 Git
sudo apt install -y git
```

### 2. 上传代码

```bash
# 方式一：从 GitHub 拉取
git clone https://github.com/Misayhuiyi/GrelinMisay.git
cd GrelinMisay

# 方式二：手动上传后解压
# scp -r ./GrelinMisay root@your-server-ip:/root/
# cd /root/GrelinMisay
```

### 3. 配置后端

```bash
# 创建虚拟环境
python3.10 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建数据目录
mkdir -p data
```

### 4. 配置环境变量

```bash
# 创建 .env 文件
cat > .env << 'EOF'
LLM_API_KEY=your-deepseek-api-key
LLM_API_BASE=https://api.deepseek.com/v1
LLM_MODEL_NAME=deepseek-chat
HOST=0.0.0.0
PORT=8000
DB_TYPE=sqlite
DB_PATH=./data/agent.db
EOF
```

### 5. 启动后端服务

```bash
# 开发模式（推荐初次部署测试）
source venv/bin/activate
nohup python run.py > logs/app.log 2>&1 &

# 生产模式 (Gunicorn)
pip install gunicorn

# 后台启动 (绑定 127.0.0.1:8000，仅后端自身)
nohup gunicorn app.main:app \
  -w 4 \
  -b 127.0.0.1:8000 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  > logs/gunicorn.log 2>&1 &

# 创建日志目录
mkdir -p logs
```

### 6. 构建前端

```bash
cd grelinmisay-app

# 安装依赖
npm install

# 构建 H5
npm run build:h5

# 构建产物在 dist/ 目录
cd ..
```

### 7. 配置 Nginx

```bash
sudo nano /etc/nginx/sites-available/grelinmisay
```

写入以下配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或IP

    # 前端静态文件
    location / {
        root /root/GrelinMisay/grelinmisay-app/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    # 后端 API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # WebSocket 支持 (如有需要)
    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/grelinmisay /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx

# 开放防火墙端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp  # 如需 HTTPS
```

### 8. 配置 HTTPS (可选，但推荐)

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取 SSL 证书 (自动配置 Nginx)
sudo certbot --nginx -d your-domain.com
```

### 9. 使用 systemd 管理服务 (可选)

```bash
# 创建后端服务
sudo nano /etc/systemd/system/grelinmisay-backend.service
```

```
[Unit]
Description=GrelinMisay Backend
After=network.target

[Service]
User=root
WorkingDirectory=/root/GrelinMisay
EnvironmentFile=/root/GrelinMisay/.env
ExecStart=/root/GrelinMisay/venv/bin/gunicorn app.main:app -w 4 -b 127.0.0.1:8000 --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable grelinmisay-backend
sudo systemctl start grelinmisay-backend
sudo systemctl status grelinmisay-backend
```

## 三、Docker 部署 (推荐)

### 1. 在服务器根目录创建 Dockerfile

```bash
cd /root/GrelinMisay
nano Dockerfile
```

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/
COPY data/ ./data/
COPY .env.example .env

# 创建非 root 用户
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 创建 docker-compose.yml

```bash
nano docker-compose.yml
```

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./grelinmisay-app/dist:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - backend
    restart: unless-stopped
```

### 3. 创建 nginx.conf

```bash
nano nginx.conf
```

```nginx
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 4. 一键启动

```bash
# 构建并启动所有服务
docker compose up -d --build

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f
```

## 四、验证部署

```bash
# 健康检查
curl http://localhost:8000/api/health

# 前端访问
curl http://localhost/

# 查看后端日志
tail -f logs/access.log
```

预期输出：
```json
{"status":"ok","model":"deepseek-chat","tools_count":8,"db_type":"sqlite"}
```

## 五、更新部署

```bash
# 拉取最新代码
git pull origin main

# 重新构建 (Docker 方式)
docker compose down
docker compose up -d --build

# 非 Docker 方式
source venv/bin/activate
pip install -r requirements.txt
pkill -f gunicorn
nohup gunicorn app.main:app -w 4 -b 127.0.0.1:8000 > logs/gunicorn.log 2>&1 &
```

## 六、常见问题

### 1. 后端启动失败
```bash
# 检查端口占用
netstat -tlnp | grep 8000

# 检查日志
cat logs/error.log
```

### 2. LLM 调用失败
- 确认 `.env` 中 `LLM_API_KEY` 填写正确
- 确认服务器网络可访问 `api.deepseek.com`

### 3. 前端 404
- 检查 Nginx 配置中 `root` 路径是否正确指向 `dist/` 目录
- `npm run build:h5` 是否成功执行

### 4. 数据库路径问题
- 确保 `data/` 目录存在且有写入权限
- SQLite 不需要额外数据库服务

---

**最后更新日期：** 2026-06-13
**适用版本：** MVP v1.0.0
