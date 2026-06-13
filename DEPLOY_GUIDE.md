# GrelinMisay 部署指南

**适用版本**: MVP v1.1.0 (含 ReAct Agent + 验证码登录 + AI 个性化 + Token 鉴权)

## 一、项目结构

```
GrelinMisay/
├── app/                    # FastAPI 后端
│   ├── api/                # API 路由
│   │   ├── g_auth.py       # 认证（密码登录+验证码登录+注册）
│   │   ├── g_users.py      # 用户资料
│   │   ├── g_goals.py      # 目标管理
│   │   ├── g_training.py   # 训练记录
│   │   ├── g_calendar.py   # 日历事件
│   │   ├── g_ai.py         # AI 对话（含用户个性化称呼）
│   │   ├── g_schemas.py    # GrelinMisay 业务请求/响应模型
│   │   ├── chat.py         # ReAct Agent 对话（需 Token 鉴权）
│   │   ├── session.py      # Agent 会话管理
│   │   ├── tool.py         # 工具列表
│   │   ├── dependencies.py # 依赖注入
│   │   └── router.py       # 路由注册
│   ├── agent/              # ReAct 推理引擎 (Thought-Action-Observation)
│   ├── tools/              # 8 个内置工具 (math/document/sql)
│   ├── memory/             # 记忆管理 (滑动窗口 + 历史压缩)
│   ├── models/             # LLM 包装器 + 通用 Pydantic Schema
│   ├── core/               # 核心配置 (pydantic-settings)
│   ├── db/                 # 数据库模型 (SQLAlchemy async)
│   └── main.py             # FastAPI 入口 (lifespan, CORS, 全局异常)
├── grelinmisay-app/        # 前端 (Taro + React + Vite)
│   ├── src/
│   │   ├── pages/          # 页面组件（登录/注册/首页/目标/训练/个人/AI）
│   │   ├── services/       # API 服务层
│   │   └── taro-adapter/   # Taro 适配层
│   └── dist/               # 构建输出目录
├── data/                   # 数据目录 (SQLite)
├── logs/                   # 日志目录
├── Dockerfile              # Docker 镜像构建文件
├── docker-compose.yml      # Docker 编排文件
├── run.py                  # 开发启动入口
├── requirements.txt        # Python 依赖
├── .env.template           # 环境变量模板
├── GrelinMisay_PRD_v1.1.0.md   # 产品需求文档
├── GrelinMisay_迭代复盘_v1.0.md # 迭代复盘文档
└── DEPLOY_GUIDE.md         # 本文档
```

## 二、API 接口

### GrelinMisay 业务 API

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | `/api/auth/send_code` | 发送验证码 | 否 |
| POST | `/api/auth/register` | 注册账号 | 否 |
| POST | `/api/auth/login` | 密码登录 | 否 |
| POST | `/api/auth/login_by_code` | 验证码登录 | 否 |
| GET | `/api/users/me` | 获取个人信息 | 是 |
| PUT | `/api/users/me` | 更新个人信息 | 是 |
| GET | `/api/goals` | 目标列表 | 是 |
| POST | `/api/goals` | 创建目标 | 是 |
| PUT | `/api/goals/{id}` | 更新目标 | 是 |
| DELETE | `/api/goals/{id}` | 删除目标 | 是 |
| POST | `/api/goals/{id}/checkin` | 打卡 | 是 |
| GET | `/api/training/actions` | 动作库 | 否 |
| GET | `/api/training/records` | 训练记录 | 是 |
| POST | `/api/training/records` | 创建训练记录 | 是 |
| GET | `/api/calendar/events` | 日历事件 | 是 |
| POST | `/api/ai/chat` | AI 对话 | 是 |

### ReAct Agent API

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | `/api/chat/send` | 发送消息给 Agent | **是** |
| POST | `/api/sessions/create` | 创建会话 | 否 |
| GET | `/api/sessions/list` | 会话列表 | 否 |
| GET | `/api/sessions/{id}` | 会话详情 | 否 |
| DELETE | `/api/sessions/{id}` | 删除会话 | 否 |
| GET | `/api/tools` | 已注册工具列表 | 否 |

> `POST /api/chat/send` 需要 `Authorization: Bearer <token>` 请求头。Agent 会将用户身份（user_id、nickname、phone）注入 System Prompt，从而在调用工具时针对性查询当前用户的数据。

## 三、云服务器部署 (Ubuntu 20.04+)

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

# 创建数据和日志目录
mkdir -p data logs
```

### 4. 配置环境变量

从模板复制并编辑：

```bash
cp .env.template .env
nano .env
```

关键配置项：

```ini
# LLM 配置（必须修改）
LLM_API_KEY=your-deepseek-api-key
LLM_API_BASE=https://api.deepseek.com/v1
LLM_MODEL_NAME=deepseek-chat

# 服务配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# 数据库
DB_TYPE=sqlite
DB_PATH=./data/agent.db
```

### 5. 启动后端服务

```bash
source venv/bin/activate

# 方式一：开发模式（推荐初次部署测试）
nohup python run.py > logs/app.log 2>&1 &

# 方式二：生产模式 (Gunicorn + UvicornWorker)
pip install gunicorn uvicorn[standard]

# 后台启动（绑定 127.0.0.1:8000，仅后端自身）
nohup gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 127.0.0.1:8000 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  > logs/gunicorn.log 2>&1 &
```

> `-k uvicorn.workers.UvicornWorker` 是异步 FastAPI 的关键，直接使用 Gunicorn 默认 worker 将导致异步代码无法执行。

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

## 四、配置开机自启（重要）

服务器重启后需要项目自动恢复运行，以下为完整的自启配置。

### 4.1 后端自启（systemd）

创建 systemd 服务文件：

```bash
sudo nano /etc/systemd/system/grelinmisay-backend.service
```

写入以下内容：

```ini
[Unit]
Description=GrelinMisay Backend
After=network.target

[Service]
User=root
WorkingDirectory=/root/GrelinMisay
EnvironmentFile=/root/GrelinMisay/.env
ExecStart=/root/GrelinMisay/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable grelinmisay-backend

# 立即启动服务
sudo systemctl start grelinmisay-backend

# 检查运行状态
sudo systemctl status grelinmisay-backend
```

常用管理命令：

```bash
sudo systemctl start grelinmisay-backend     # 启动
sudo systemctl stop grelinmisay-backend      # 停止
sudo systemctl restart grelinmisay-backend   # 重启
sudo systemctl status grelinmisay-backend    # 查看状态
sudo journalctl -u grelinmisay-backend -f    # 实时日志
```

### 4.2 Nginx 自启

```bash
# Nginx 通过 apt 安装后通常已自动启用自启，手动确认：
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl status nginx
```

### 4.3 验证开机自启

```bash
# 重启服务器
sudo reboot

# 重新登录后验证后端
sudo systemctl status grelinmisay-backend

# 验证 Nginx
sudo systemctl status nginx

# 验证服务可访问
curl http://localhost:8000/api/health
curl http://localhost/
```

## 五、Docker 部署 (推荐)

项目已包含 `Dockerfile`、`docker-compose.yml`、`nginx.conf` 和 `.dockerignore`，无需额外编写。

### 5.1 架构说明

```
浏览器 :80 → nginx (前端静态文件 + /api/ 反向代理)
                │
                └→ backend:8000 (FastAPI + ReAct Agent)
```

| 组件 | 镜像 | 端口 | 作用 |
|------|------|------|------|
| backend | 本地构建 (python:3.11-slim) | 8000 | FastAPI 后端 + ReAct 引擎 |
| nginx | nginx:alpine | 80 | 前端托管 + API 反向代理 |

### 5.2 启动步骤

```bash
# 1. 创建 .env 文件
cp .env.template .env
# 编辑 .env 填入 LLM_API_KEY

# 2. 构建前端
cd grelinmisay-app
npm install
npm run build:h5
cd ..

# 3. 启动全部服务（后端 + Nginx）
docker compose up -d --build

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f
```

> `docker-compose.yml` 包含两个服务：
> - **backend**：FastAPI 后端，端口 `8000`，健康检查已内置
> - **nginx**：前端静态文件 + API 反向代理，端口 `80`
>
> 访问 `http://localhost` 即可使用完整应用。

## 五、验证部署

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

完整功能验证：

```bash
# 1. 注册用户
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800138000","password":"123456","nickname":"测试用户"}'

# 2. 登录获取 Token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800138000","password":"123456"}'

# 3. 带 Token 调用 Agent (使用上一步返回的 token)
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"message":"你好，帮我算一下 123 * 456"}'
```

## 六、更新部署

```bash
# 拉取最新代码
git pull origin main

# Docker 方式
docker compose down
docker compose up -d --build

# 非 Docker 方式
source venv/bin/activate
pip install -r requirements.txt
pkill -f gunicorn
nohup gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 --timeout 120 > logs/gunicorn.log 2>&1 &
```

## 七、常见问题

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

### 5. chat/send 返回 401

- 确认请求带 `Authorization: Bearer <token>` 请求头
- Token 来自 `/api/auth/login` 或 `/api/auth/register` 返回的 `token` 字段

---

**最后更新日期:** 2026-06-13
**适用版本:** MVP v1.1.0
