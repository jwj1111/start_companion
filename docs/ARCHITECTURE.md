# 架构设计文档

## 1. 系统总览

START Companion 是一个基于 LangGraph 的多 Agent START 情感陪伴系统，专为腾讯 START 云游戏场景设计。

### 核心设计原则

| 原则 | 说明 |
|------|------|
| **模块可分离** | 每个功能模块独立开发、测试、部署 |
| **预设与用户分离** | 开发者预设 (presets/) 和用户自定义 (custom/) 物理隔离 |
| **模型可配置** | 所有模型调用通过统一 Provider 层，按角色配置 |
| **工具可扩展** | 新功能通过 Tool 或 Sub-Agent 接入，无需修改核心流程 |
| **前后端分离** | WebSocket + REST API 通信 |

---

## 2. LangGraph 架构

### 2.1 主图 (Main Graph)

```
                    ┌────────────────┐
                    │   Entry Point  │
                    │  (route_input) │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
             ┌─────│   Main Agent   │─────┐
             │     │    (ReAct)     │     │
             │     └───────┬────────┘     │
             │             │              │
        has_tool_call   no_tool_call      │
             │             │              │
    ┌────────▼───┐   ┌────▼──────┐       │
    │  Tool Node │   │  Output   │       │
    │            │   │ Processor │       │
    └────────┬───┘   └───────────┘       │
             │                            │
             └────────────────────────────┘
                    (loop back)
```

### 2.2 Tools (由 Main Agent 自主调用)

| Tool | 功能 | 何时触发 |
|------|------|----------|
| `screenshot_tool` | 截图 + 视觉模型分析 | 需要理解游戏画面时 |
| `memory_read_tool` | 检索长期记忆 | 需要回忆过去对话/用户偏好时 |
| `memory_write_tool` | 写入长期记忆 | 对话中出现重要信息时 |
| `knowledge_search_tool` | 搜索游戏知识库 | 用户询问游戏相关问题时 |
| `web_search_tool` | 联网搜索 | 知识库无答案/需要实时信息时 |

### 2.3 Sub-Agents (由 Main Agent 作为 Tool 调用)

| Sub-Agent | 功能 | 场景 |
|-----------|------|------|
| `emotion_analyzer` | 分析用户情绪，建议回复语气 | 复杂情感交互场景 |
| `game_strategist` | 游戏策略分析（RAG + Search） | 深度游戏问题 |

---

## 3. 模块详解

### 3.1 Model Provider (`models/`)

**设计**：统一抽象层，所有模型调用通过 `get_model(role)` 获取。

**模型角色**：
- `main`: 主对话模型（最强，用于核心回复）
- `vision`: 视觉模型（支持图片输入）
- `auxiliary`: 辅助模型（轻量快速，用于情感分析/记忆提取等）
- `embedding`: 向量嵌入模型

**支持的 Provider**：
- OpenAI / Azure OpenAI
- Anthropic (Claude)
- 腾讯混元 (Hunyuan)
- DeepSeek
- 智谱 (ZhiPu)
- Ollama (本地模型)
- 任意 OpenAI-compatible API

**扩展新 Provider**：在 `models/provider.py` 的 `_create_chat_model` 中添加新分支即可。

---

### 3.2 Memory Layer (`memory/`)

采用**"短期滚动 + 长期可编辑卡片"**的双层架构（参考 SillyTavern Summary + KokoroMemo 卡片）。

```
┌──────────────────────────────────────────────────────────┐
│  短期记忆 (Short-term)                                   │
│  位置: LangGraph State.messages                          │
│  结构: [可选的摘要块] + [最近 N 条原始消息]              │
│  策略: 对话轮次超过 turns_threshold 时触发摘要压缩        │
│  实现: memory/short_term/summarizer.py                   │
└──────────────────────────────────────────────────────────┘
              │ 压缩时提取重要信息
              ▼
┌──────────────────────────────────────────────────────────┐
│  长期记忆 (Long-term) —— KokoroMemo 风格记忆卡片          │
│  存储:                                                   │
│    - 向量数据库 (Qdrant): 向量 + 过滤字段                │
│    - 关系数据库 (SQLite): 完整卡片元数据                 │
│  结构: MemoryCard                                        │
│    - content / category / tags / importance              │
│    - status: pending → active → archived / rejected      │
│    - source: llm_extracted / user_manual / system        │
│    - user_edited / editable                              │
│    - recall_count / last_recalled_at                     │
│  隔离: user_id × agent_id 强制过滤                       │
│  可编辑: 提供 CRUD API，用户可审核/编辑/删除卡片         │
│  实现: memory/long_term/store.py                         │
└──────────────────────────────────────────────────────────┘
```

#### 模块划分

```
memory/
├── schema.py                  # MemoryCard / 枚举类型
├── manager.py                 # 对外统一入口（绑定 user × agent）
├── extractor.py               # 从对话提取候选记忆
├── retrieval_gate.py          # 检索门控：是否触发召回
├── short_term/
│   ├── window.py              # ConversationWindow 数据结构
│   └── summarizer.py          # 按轮次触发的滚动摘要
├── long_term/
│   └── store.py               # 协调向量库 + 关系库的读写
├── vector_stores/             # 向量库抽象 + 实现
│   ├── base.py
│   ├── factory.py
│   ├── qdrant_store.py        # 推荐
│   ├── chroma_store.py        # 占位
│   └── milvus_store.py        # 占位
└── relational/                # 关系型存储抽象 + 实现
    ├── base.py
    ├── factory.py
    └── sqlite_store.py
```

#### 检索门控策略（`retrieval_gate.py`）

为避免"每轮都召回"的浪费和延迟：

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `always` | 总是召回 | MVP 阶段 |
| `never` | 仅 LLM 主动 tool 调用 | 极致省钱 |
| `rule_based` | 规则过滤（短消息 / 问候 / 引用词） | **推荐默认** |
| `model_based` | 小模型判断 | 精度优先 |
| `composite` | 规则 + 模型组合 | 生产最佳 |

#### 记忆生命周期

```
LLM 自动提取      →  PENDING  →  用户审核
                                    ↓
                              ┌─────┴─────┐
                              ↓           ↓
                           ACTIVE    REJECTED
                              │
                        （定期整合）
                              ↓
                          ARCHIVED

用户手动添加      →  直接 ACTIVE
```

#### 用户隔离

- 所有 `MemoryManager` 实例绑定 `(user_id, agent_id)`
- 向量库检索强制带 `user_id` 过滤
- SQLite 查询强制带 `user_id = ?` 条件
- API 层从鉴权中取 `user_id`，前端无法伪造

#### 向量数据库选型

记忆和知识库**使用同一个向量库实例**，但通过不同 collection 隔离：
- `user_memories`：用户记忆卡片（带 user_id / agent_id / status 过滤）
- `game_knowledge`：游戏知识库（带 game_name 过滤）

推荐 **Qdrant**（过滤能力强、部署简单），百万级向量性能足够。超大规模再切 Milvus。

---

### 3.3 Preset & Custom System (`presets/` + `custom/`)


**分离机制**：

```
presets/agents/default/          # 开发者定义，Git 管理，不可被用户修改
    ├── persona.yaml            # 完整人设
    ├── prompts.yaml            # 提示词模板
    └── config.yaml             # 行为配置

custom/{user_id}/agents/default/ # 用户数据目录，运行时生成
    ├── persona_overrides.yaml  # 仅包含用户修改的字段
    └── config_overrides.yaml   # 仅包含用户修改的字段
```

**加载逻辑**：
```python
final = deep_merge(preset_config, user_overrides)
```

**可微调字段控制**：预设中的 `user_customizable_fields` 列表声明允许用户修改的字段路径。

---

### 3.4 Knowledge Base / RAG (`knowledge/`)

**功能**：游戏攻略、机制说明等结构化知识的检索。

**流程**：
1. **Ingest**: 游戏知识文档 → 分块 → Embedding → 存入向量数据库（独立 Collection）
2. **Retrieve**: 用户问题 → Embedding → 向量搜索 → 可选 Re-rank → 返回相关内容

**与长期记忆的区别**：
- 知识库 = 客观游戏知识（开发者维护）
- 长期记忆 = 用户个人信息和对话记录（运行时生成）
- 两者存在同一个向量数据库的不同 Collection 中

---

### 3.5 Voice Services (`services/voice/`)

**ASR Pipeline**:
```
用户语音 → WebSocket → ASR 服务 → 文本 → LangGraph → 文本回复
```

**TTS Pipeline**:
```
文本回复 → TTS 服务 → 音频流 → WebSocket → 前端播放
```

**支持流式处理**，实现低延迟语音对话。

---

### 3.6 Vision / Screenshot (`services/vision/`)

**流程**：
```
前端截图 → WebSocket 传输 → 后端接收 → 压缩 → Vision 模型分析 → 返回描述
```

**截图来源**：由前端（运行在云游戏环境中）负责截取当前游戏画面并通过 WebSocket 发送。

---

## 4. 前端架构 (frontend/)

前端参考 `start-agent` 项目的设计：

```
frontend/
├── src/
│   ├── components/
│   │   ├── Live2D/          # Live2D 渲染组件
│   │   ├── Chat/            # 聊天面板
│   │   ├── Voice/           # 语音交互控件
│   │   └── Settings/        # 设置面板
│   ├── services/
│   │   ├── websocket.ts     # WebSocket 通信
│   │   ├── screenshot.ts    # 截图捕获
│   │   └── audio.ts         # 音频录制/播放
│   ├── stores/              # 状态管理
│   └── App.vue
├── public/
│   └── live2d-models/       # Live2D 模型资源
└── package.json
```

---

## 5. 通信协议

### REST API

| Endpoint | Method | 功能 |
|----------|--------|------|
| `/api/chat/send` | POST | 发送文本消息 |
| `/api/chat/history/{session_id}` | GET | 获取历史 |
| `/api/agent/list` | GET | 列出所有 Agent |
| `/api/agent/{id}/customize` | POST | 保存用户微调 |
| `/api/config/models` | GET/PUT | 模型配置管理 |

### WebSocket

| Endpoint | 功能 |
|----------|------|
| `/api/ws/voice/{session_id}` | 实时语音流 |
| `/api/ws/events/{session_id}` | 事件推送（截图、状态、Live2D 指令） |

---

## 6. 部署架构

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│  Qdrant DB   │
│  (Nginx/CDN) │     │  (FastAPI)   │     │              │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                    ┌───────▼───────┐
                    │  LLM APIs     │
                    │  (OpenAI/     │
                    │   混元/本地)  │
                    └───────────────┘
```

Docker Compose 一键启动开发环境。

---

## 7. 迭代路线建议

### Phase 1: MVP
- [x] 项目架构搭建
- [ ] LangGraph 主图跑通（纯文本对话）
- [ ] 基础记忆层（短期 + 简单长期）
- [ ] 单 Agent 预设加载

### Phase 2: 多模态
- [ ] 语音对话（ASR + TTS）
- [ ] 截图分析（Vision）
- [ ] Live2D 渲染 + 情感驱动

### Phase 3: 游戏深度
- [ ] 游戏知识库 RAG
- [ ] 联网搜索集成
- [ ] 游戏策略子 Agent

### Phase 4: 完善
- [ ] 用户微调系统
- [ ] 多 Agent 管理
- [ ] 记忆整合与遗忘
- [ ] 性能优化与部署
