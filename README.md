# START Companion

基于 LangGraph 的多 Agent 情感陪伴系统，专为腾讯 START 云游戏设计。

## 核心设计原则

1. **两条通道分离** — 背景上下文（Context Provider → System Prompt）与实时交互（Tool → Messages）职责正交，互不侵入
2. **可插拔扩展** — Context Provider、Tool、SubAgent 均为注册制，新增模块不改框架代码
3. **预设与用户分离** — 开发者维护 `presets/`，用户微调 `custom/`，运行时 deep merge 覆盖
4. **模型无关** — 统一 `get_model(role)` 抽象，声明式 YAML 配置即可切换模型，业务代码零感知
5. **三层记忆** — 用户档案（全量注入）+ 短期记忆（对话窗口）+ 长期记忆（向量检索）

## 架构概览

```
Frontend (桌面应用，可嵌入宿主程序)
  │  虚拟形象 / 语音交互 / 对话界面 / 设置面板
  │
  │ WebSocket + REST API
  ▼
Backend (Python)
  │
  ├── LangGraph Orchestrator
  │     │
  │     ├── route_input
  │     │     └── Context Providers (可插拔)
  │     │           注入人设、档案、记忆等背景上下文至 System Prompt
  │     │
  │     ├── Main Agent (ReAct Loop)
  │     │     ├── Tools — 实时交互能力（按需调用，可扩展）
  │     │     └── SubAgents — 专项子任务（可扩展）
  │     │
  │     └── process_output → 响应文本 + 情感标签
  │
  ├── Memory Layer — 三层记忆架构
  ├── Model Provider — 模型抽象与路由
  ├── Preset Manager — 角色预设管理
  └── Agent Registry — Agent 注册与生命周期
```

## 技术栈

### 架构选型（稳定）

| 层 | 选型 | 说明 |
|---|------|------|
| 多 Agent 编排 | LangGraph | 状态图驱动，支持 ReAct + 条件路由 |
| Web 框架 | FastAPI | 异步优先，原生 WebSocket 支持 |
| 数据建模 | Pydantic 2.x | 配置、状态、API 统一校验 |
| 记忆存储 | 关系型 DB + 向量 DB | 双写，结构化查询 + 语义检索并行 |
| 前后端通信 | WebSocket + REST | 实时流（语音/事件）+ 管理接口 |

### 当前实现（可替换）

- **向量 DB**: Qdrant（可换 Milvus / ChromaDB）
- **关系 DB**: SQLite（开发）/ MySQL（生产）
- **模型**: OpenAI / Anthropic / Ollama / 混元 等 OpenAI 协议兼容模型
- **前端**: 桌面应用形态，最终嵌入宿主程序（技术选型待定）

## 目录结构

```
start_companion/
├── backend/                # Python 后端
│   ├── app/                # FastAPI 应用入口、路由、配置
│   ├── agents/             # LangGraph 编排图定义
│   ├── context_providers/  # 背景上下文提供者（可插拔）
│   ├── tools/              # LangGraph Tools（实时交互能力）
│   ├── models/             # Model Provider 抽象层
│   ├── memory/             # 记忆层（档案 / 短期 / 长期）
│   ├── presets/            # 开发者预设（角色人设 / 行为策略）
│   ├── custom/             # 用户微调空间（运行时覆盖）
│   ├── knowledge/          # 知识库 & RAG
│   └── services/           # 外部服务集成（ASR / TTS / Vision）
├── frontend/               # 前端（桌面应用，技术选型待定）
├── docs/                   # 文档（架构细节、模块说明）
└── docker/                 # 容器化部署
```

## 配置体系

| 文件 | 职责 | Git 管理 |
|------|------|----------|
| `config.yaml` | 结构化配置（模型池、记忆策略、服务端点） | ✅ 提交模板 |
| `.env` | 敏感凭据（API Key、数据库密码） | ❌ 不提交 |
| `presets/` | 角色人设 & 行为配置 | ✅ |
| `custom/` | 用户运行时微调 | ❌ 按用户隔离 |

**加载优先级**: 环境变量 > `.env` > `config.yaml` > 代码默认值

## 快速开始

```bash
# 后端
cd backend
pip install -e ".[dev]"
cp app/config/config.example.yaml app/config/config.yaml
# 编辑 config.yaml 填入模型 API Key，或通过 .env 配置
python -m app.main

# 前端（待定）
# 前端为桌面应用形态，开发启动方式待技术选型确定后补充
```

## 文档

详细的模块说明、Tool/SubAgent 清单、API 参考等内容请查阅 [`docs/`](./docs/) 目录。
