# GrelinMisay

**健身目标管理助手** —— 一款帮助用户设定健身目标、记录训练数据、管理日程的跨端应用。

## 项目简介

GrelinMisay 是一个全栈健身管理应用，包含：

- **后端**：FastAPI + SQLAlchemy + SQLite，提供 RESTful API
- **前端**：Taro (React) 跨端框架，支持 H5 / 微信小程序 / APP
- **AI 助手**：基于 ReAct+CoT 框架的智能对话助手

## 功能模块

| 模块 | 功能 |
|------|------|
| **用户系统** | 手机号注册/登录、个人资料管理 |
| **目标管理** | 创建目标、每日打卡、进度追踪、成员协作 |
| **训练记录** | 训练计划、组数记录、休息计时、动作库 |
| **日历日程** | 日历视图、事件管理、提醒通知 |
| **AI 助手** | 智能对话、健身建议、数据分析 |

## 技术栈

### 后端
- **框架**：FastAPI 0.100+
- **ORM**：SQLAlchemy 2.0 (async)
- **数据库**：SQLite (MVP) / PostgreSQL (生产)
- **LLM**：DeepSeek API (兼容 OpenAI)

### 前端
- **框架**：Taro 3.6+ / React 18
- **构建**：Vite 5
- **UI**：自定义组件 + Taro Components

## 目录结构

```
GrelinMisay/
├── app/                        # 后端代码
│   ├── main.py                 # FastAPI 入口
│   ├── core/                   # 配置、日志、异常
│   ├── db/                     # 数据库模型
│   │   ├── database.py         # 数据库连接
│   │   └── models.py           # ORM 模型
│   ├── api/                    # API 路由
│   │   ├── router.py           # 路由注册
│   │   ├── g_auth.py           # 认证 API
│   │   ├── g_users.py          # 用户 API
│   │   ├── g_goals.py          # 目标 API
│   │   ├── g_training.py       # 训练 API
│   │   ├── g_calendar.py       # 日历 API
│   │   ├── g_ai.py             # AI 对话 API
│   │   └── g_schemas.py        # 请求/响应模型
│   ├── agent/                  # ReAct Agent 引擎
│   ├── tools/                  # 内置工具
│   └── memory/                 # 记忆管理
├── grelinmisay-app/            # 前端代码
│   ├── src/
│   │   ├── pages/              # 页面组件
│   │   │   ├── login/          # 登录页
│   │   │   ├── register/       # 注册页
│   │   │   ├── home/           # 首页
│   │   │   ├── goals/          # 目标页
│   │   │   ├── training/       # 训练页
│   │   │   ├── profile/        # 个人中心
│   │   │   └── ai/             # AI 助手
│   │   ├── services/           # API 服务
│   │   └── taro-adapter/       # Taro 适配层
│   ├── package.json
│   └── vite.config.ts
├── data/                       # 数据目录
├── requirements.txt            # Python 依赖
├── DEPLOY_GUIDE.md             # 部署指南
├── GrelinMisay_PRD_v1.1.0.md   # 产品需求文档
└── README.md
```

## 快速开始

### 环境要求

- Python >= 3.10
- Node.js >= 18
- npm / yarn

### 后端启动

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.template .env
# 编辑 .env，填入 LLM_API_KEY

# 启动服务
python -m uvicorn app.main:app --reload --port 8000
```

### 前端启动

```bash
cd grelinmisay-app

# 安装依赖
npm install

# 开发模式 (H5)
npm run dev

# 构建 H5
npm run build:h5

# 构建微信小程序
npm run build:weapp

# 构建 APP
npm run build:app
```

### 访问地址

| 服务 | 地址 |
|------|------|
| 前端 H5 | http://localhost:10086 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/api/health |

## API 接口

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/send_code` | 发送验证码 |
| POST | `/api/auth/register` | 注册账号 |
| POST | `/api/auth/login` | 登录 |

### 用户

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/users/me` | 获取个人信息 |
| PUT | `/api/users/me` | 更新个人信息 |

### 目标

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/goals` | 目标列表 |
| POST | `/api/goals` | 创建目标 |
| PUT | `/api/goals/{id}` | 更新目标 |
| DELETE | `/api/goals/{id}` | 删除目标 |
| POST | `/api/goals/{id}/checkin` | 打卡 |
| GET | `/api/goals/{id}/stats` | 统计数据 |

### 训练

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/training/actions` | 动作库 |
| GET | `/api/training/records` | 训练记录 |
| POST | `/api/training/records` | 创建记录 |

### 日历

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/calendar/events` | 日历事件 |

### AI

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ai/chat` | AI 对话 |

## 数据库模型

| 表名 | 说明 |
|------|------|
| `g_users` | 用户表 |
| `g_goals` | 目标表 |
| `g_goal_members` | 目标成员表 |
| `g_goal_checkins` | 目标打卡表 |
| `g_training_records` | 训练记录表 |
| `g_training_sets` | 训练组表 |
| `g_calendar_events` | 日历事件表 |
| `g_ai_chat_messages` | AI 对话记录表 |

## 部署

详细部署指南请参阅 [DEPLOY_GUIDE.md](./DEPLOY_GUIDE.md)。

### Docker 一键部署

```bash
docker compose up -d --build
```

### 手动部署

1. 后端：Gunicorn + Uvicorn
2. 前端：Nginx 托管静态文件
3. 反向代理：Nginx 代理 API 请求

## 开发计划

- [x] 用户认证系统
- [x] 目标管理 CRUD
- [x] 训练记录功能
- [x] 日历日程管理
- [x] AI 对话助手
- [ ] 微信小程序端
- [ ] APP 打包
- [ ] 数据可视化
- [ ] 社交功能

## 许可证

MIT
