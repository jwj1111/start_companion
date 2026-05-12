# START Companion for START Cloud Gaming

基于 LangGraph 的多 Agent START 情感陪伴系统，专为腾讯 START 云游戏设计。

## 架构概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (Web/Electron)                       │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌───────────────┐   │
│  │ Live2D   │  │ Voice I/O    │  │ Chat UI  │  │ Settings Panel│   │
│  │ Renderer │  │ (ASR + TTS)  │  │          │  │               │   │
│  └──────────┘  └──────────────┘  └──────────┘  └───────────────┘   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ WebSocket / REST API
┌─────────────────────────────▼───────────────────────────────────────┐
│                         Backend (Python)                              │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                   LangGraph Orchestrator                      │    │
│  │  ┌─────────┐                                                 │    │
│  │  │  Main   │── ReAct ──┬── Tool: Screenshot & Vision         │    │
│  │  │  Agent  │           ├── Tool: Voice (ASR/TTS)             │    │
│  │  │         │           ├── Tool: Game Knowledge RAG          │    │
│  │  │         │           ├── Tool: Web Search                  │    │
│  │  │         │           ├── Tool: Memory Read/Write           │    │
│  │  │         │           ├── SubAgent: Emotion Analysis        │    │
│  │  │         │           └── SubAgent: Game Strategy           │    │
│  │  └─────────┘                                                 │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │  Memory  │  │  Model   │  │  Preset  │  │  Agent Registry  │    │
│  │  Layer   │  │  Provider│  │  Manager │  │                  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## 目录结构

```
ai_companion/
├── backend/                    # Python 后端
│   ├── app/                    # 应用主入口
│   ├── agents/                 # LangGraph Agent 定义
│   ├── tools/                  # LangGraph Tools
│   ├── models/                 # Model Provider 抽象层
│   ├── memory/                 # 记忆层（短期/长期/向量）
│   ├── presets/                # 开发者预设（角色/人设/策略）
│   ├── custom/                 # 用户微调空间（运行时加载）
│   ├── knowledge/              # 游戏知识库 & RAG
│   ├── services/               # 外部服务集成（ASR/TTS/Vision）
│   └── config/                 # 配置管理
├── frontend/                   # 前端（Live2D + 语音 + Chat）
├── docs/                       # 文档
├── tests/                      # 测试
└── docker/                     # 部署配置
```

## 技术栈

- **后端**: Python 3.11+, LangGraph, FastAPI, Pydantic
- **记忆层**: 向量数据库 (Qdrant/Milvus/ChromaDB 可配置) + SQLite
- **模型层**: 统一抽象，支持 OpenAI / Claude / 本地模型 / 混元等
- **前端**: Vue 3 + TypeScript + Live2D + Web Audio API
- **通信**: WebSocket (实时语音/状态) + REST API (配置/管理)

## 快速开始

```bash
# 后端
cd backend
pip install -e ".[dev]"
cp config/config.example.yaml config/config.yaml
# 编辑配置文件，填入模型 API Key 等
python -m app.main

# 前端
cd frontend
pnpm install
pnpm dev
```
