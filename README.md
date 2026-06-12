# ReAct+CoT AI Agent 智能助手

基于 **ReAct 推理框架** + **CoT 思维链** 的轻量化 AI Agent 智能助手后端工程。

## 项目特性

| 特性 | 说明 |
|------|------|
| **手写 ReAct 引擎** | 从零实现 Thought-Action-Observation 循环，不依赖 LangChain Agent 封装 |
| **CoT 思维链** | 结构化 Prompt 模板，引导模型分步推理 |
| **自动校验重试** | LLM 输出格式校验 + 参数 Schema 验证 + 最多3次重试 |
| **8个内置工具** | 文档检索(3) + SQL查询(3) + 数学计算(2) |
| **记忆压缩** | 滑动窗口 + 关键信息提取压缩，稳定支持8轮以上对话 |
| **SQL持久化** | 会话/消息/工具调用/执行日志全量落库 |
| **全局异常处理** | 统一异常体系 + 超时控制 + LLM重试 |
| **Swagger文档** | 自动生成接口文档，可在线调试 |

## 目录结构

```
agent2/
├── app/
│   ├── main.py                 # FastAPI 入口 + 生命周期
│   ├── core/                   # 配置层：config / logger / exceptions
│   ├── db/                     # 数据库层：ORM模型 / Repository
│   ├── models/                 # 模型层：LLM封装 / Pydantic Schema
│   ├── tools/                  # 工具管理层：8个内置工具
│   │   ├── document/           #   文档检索工具(3)
│   │   ├── sql/                #   SQL查询工具(3)
│   │   └── math/               #   数学计算工具(2)
│   ├── memory/                 # 记忆管理层：滑动窗口 + 压缩
│   ├── agent/                  # ReAct推理层：引擎/CoT/校验器
│   └── api/                    # API接口层：路由/依赖
├── run.py                      # 一键启动
├── requirements.txt            # 依赖锁定
├── .env.template               # 环境配置模板
└── README.md
```

## 快速开始

### 1. 环境要求

- Python >= 3.10
- pip

### 2. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置 API Key

```bash
# 复制配置模板
copy .env.template .env    # Windows
cp .env.template .env      # Linux/Mac

# 编辑 .env，填入你的 API Key
# LLM_API_KEY=sk-your-api-key-here
```

### 4. 启动服务

```bash
python run.py

# 或指定端口
python run.py --port=9000

# 开发模式（热重载）
python run.py --reload
```

### 5. 访问接口文档

| 地址 | 说明 |
|------|------|
| http://localhost:8000/docs | Swagger UI 接口文档 |
| http://localhost:8000/redoc | ReDoc 接口文档 |
| http://localhost:8000/api/health | 健康检查 |

## API 接口

### 对话接口

```bash
# 发起对话
POST /api/chat/send
{
  "session_id": null,        # 可选，为空则创建新会话
  "message": "帮我计算 156 * 23 + 89 除以 7 的结果"
}
```

响应示例：
```json
{
  "session_id": "a1b2c3d4e5f6",
  "message": "计算结果为 525.2857...",
  "reaction_steps": [
    {
      "iteration": 1,
      "thought": "需要先用计算器计算乘法...",
      "action": "calculator",
      "action_input": {"expression": "156 * 23"},
      "observation": "成功: 计算结果: 3588",
      "duration_ms": 1200
    }
  ],
  "tool_calls_count": 2,
  "total_duration_ms": 3500
}
```

### 会话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/sessions/create` | 创建会话 |
| GET | `/api/sessions/list` | 会话列表 |
| GET | `/api/sessions/{id}` | 会话详情 |
| DELETE | `/api/sessions/{id}` | 删除会话 |

### 工具管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tools/list` | 工具列表 |
| GET | `/api/tools/{name}` | 工具详情 |
| GET | `/api/tools/{name}/schema` | OpenAI Schema |

## 工具列表

| 分类 | 工具名 | 功能 |
|------|--------|------|
| 文档检索 | `document_search` | 关键词搜索文档 |
| 文档检索 | `file_reader` | 读取本地文件 |
| 文档检索 | `web_fetch` | 抓取网页内容 |
| SQL查询 | `sql_query` | 执行SELECT查询 |
| SQL查询 | `schema_explorer` | 探查表结构 |
| SQL查询 | `data_analyzer` | 数据统计分析 |
| 数学计算 | `calculator` | 表达式计算 |
| 数学计算 | `statistics` | 描述性统计 |

## 技术架构

```
用户请求 → API接口层(api/)
              ↓
        ReAct推理引擎(agent/)
         ↙        ↓         ↘
   记忆层(memory/)  工具层(tools/)  CoT Prompt(agent/cot_prompt.py)
              ↓
        模型层(models/llm.py) ←→ 数据库层(db/)
              ↑
        配置层(core/)  ← 全局异常/日志/配置
```

## 配置说明

所有配置通过 `.env` 文件管理：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `LLM_API_KEY` | API密钥 | - |
| `LLM_API_BASE` | API地址 | `https://api.openai.com/v1` |
| `LLM_MODEL_NAME` | 模型名称 | `gpt-4o` |
| `REACT_MAX_ITERATIONS` | 最大推理轮数 | 10 |
| `MEMORY_WINDOW_SIZE` | 滑动窗口大小 | 12 |
| `DB_TYPE` | 数据库类型 | sqlite |

## 许可证

MIT
