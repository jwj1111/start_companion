# 架构设计文档

## 1. 系统总览

START Companion 是一个基于 LangGraph 的多 Agent START 情感陪伴系统，专为腾讯 START 云游戏场景设计。

### 核心设计原则

| 原则 | 说明 |
|------|------|
| **模块可插拔** | 背景上下文通过 Context Provider 机制提供，新增/删除模块不改核心流程 |
| **预设与用户分离** | 开发者预设 (presets/) 和用户自定义 (custom/) 物理隔离 |
| **模型可配置** | 所有模型调用通过统一 Provider 层，按角色配置 |
| **工具可扩展** | 实时交互通过 Tool 或 Sub-Agent 接入 |
| **两条通道分离** | 背景上下文（SP注入）和实时交互（Tool/ToolMessage）走不同路径 |
| **前后端分离** | WebSocket + REST API 通信 |

---

## 2. LangGraph 架构

### 2.1 主图 (Main Graph)

```
                    ┌────────────────┐
                    │   Entry Point  │
                    │  (route_input) │
                    │                │
                    │  遍历 Context  │
                    │  Providers     │
                    │  → 填充        │
                    │  context_parts │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
             ┌─────│   Main Agent   │─────┐
             │     │    (ReAct)     │     │
             │     │                │     │
             │     │  SP 由         │     │
             │     │  context_parts │     │
             │     │  动态组装      │     │
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

### 2.2 两条通道

系统中有两种信息通道，职责明确分离：

| 通道 | 载体 | 特点 | 例子 |
|------|------|------|------|
| **背景上下文** | Context Provider → `context_parts` → SP | 模型从头就能看到，确定性触发 | 人设、档案、长期记忆 |
| **实时交互** | Tool → ToolMessage → messages | 模型主动调用，结果在对话流中 | 截图、知识库、搜索、SubAgent |

**为什么这样分？**
- 档案、记忆等信息模型"不知道自己不知道"，必须主动给它看 → 背景上下文
- 截图、知识库等信息模型会主动请求 → 实时交互

### 2.3 Context Providers（背景上下文提供者）

```
context_providers/
├── base.py                  # 抽象基类 + ProviderGroup 枚举
├── persona_provider.py      # 人设（STATIC 组，可缓存）
├── profile_provider.py      # 用户档案（DYNAMIC 组，每轮全量读）
├── memory_provider.py       # 长期记忆（DYNAMIC 组，Gate→改写→检索）
└── ... 未来可扩展
```

每个 Provider 是独立沙箱：
- `should_run(state)` → 自己决定本轮要不要执行
- `run(state)` → 执行逻辑，返回一段文本
- 分组为 STATIC（固定不变）或 DYNAMIC（每轮可能变化）

**新增模块**：写一个 Provider 文件 + 注册，不碰 state / nodes / prompts。
**删除模块**：在 `config.yaml` 的 `context_providers.disabled` 里加上名字。

### 2.4 System Prompt 组装

SP 由 `context_parts` 动态拼接，支持两种模式（配置切换）：

| 模式 | 配置值 | SP 结构 | 适用场景 |
|------|--------|---------|---------|
| 统一 | `sp_mode: unified` | 所有内容拼成一个 SystemMessage | 兼容性最好，小模型推荐 |
| 分离 | `sp_mode: split` | STATIC 一个 SP + DYNAMIC 一个 SP | 可利用 prompt caching |

两种都保留，测试后选定。

### 2.5 Tools（实时交互）

| Tool | 功能 | 何时触发 |
|------|------|----------|
| `screenshot_tool` | 截图 + 视觉模型分析 | 需要理解游戏画面时 |
| `game_info_tool` | 游戏信息查询（知识库优先，没有就联网搜索，auxiliary 总结） | 用户问游戏问题时 |

注意：
- 记忆读写都不走 Tool。读取由 `MemoryProvider` 在入口阶段注入 SP；写入在 session_end 时 LLM 自动提取。
- `game_info_tool` 合并了原来分散的知识库搜索和联网搜索，内部自动选择来源并用 auxiliary 模型压缩总结。
- 主 Agent 可以先调 `screenshot_tool` 获取画面描述，再通过 `game_info_tool` 的 `screen_context` 参数传入，也可以不传。

### 2.6 Sub-Agents（由 Main Agent 作为 Tool 调用）

| Sub-Agent | 功能 | 场景 |
|-----------|------|------|
| `emotion_analyzer` | 分析用户情绪，建议回复语气，驱动 Live2D 表情 | 输出后处理 |

注意：游戏策略查询已合并为 `game_info_tool`（单 tool 内搜索+总结），不再需要独立子 Agent。
未来如果查询逻辑变复杂（如需要多轮检索+推理），可将 tool 内部升级为子图，对外接口不变。

---

## 3. 模块详解

### 3.1 Model Provider (`models/`)

**设计**：统一抽象层，所有模型调用通过 `get_model(role)` 获取。

**模型角色**：
- `main`: 主对话模型（最强，用于核心回复）
- `vision`: 视觉模型（支持图片输入）
- `auxiliary`: 辅助模型（轻量快速，用于情感分析/记忆提取/query 改写等）
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

采用**"用户档案 + 短期滚动 + 长期可编辑卡片"**三层架构。

```
┌──────────────────────────────────────────────────────────┐
│ 用户档案 (Profile)                                       │
│   存储: 关系型 DB（EAV 模式）                            │
│   读取: ProfileProvider → 每轮全量注入 SP                │
│   写入: session_end 时 LLM 提取更新                      │
│   参考: EVE 128 记忆槽 + KokoroMemo 状态板              │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│ 短期记忆 (Short-term)                                    │
│   存储: LangGraph State.messages（内存）                  │
│   结构: [可选的 HISTORY_SUMMARY 块] + [最近 N 条原始消息] │
│   策略: 对话轮次超过 turns_threshold 时触发摘要压缩       │
│   参考: SillyTavern Summary 扩展                         │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│ 长期记忆 (Long-term) —— 可编辑记忆卡片                   │
│   存储: 向量数据库 (Qdrant) + 关系数据库 (SQLite)        │
│   读取: MemoryProvider（Gate → 改写 query → 检索）            │
│   写入: session_end 提取 + 去重合并 / tool 主动写入      │
│   审核: 新卡片 PENDING → 用户审核 → ACTIVE               │
│   参考: KokoroMemo 卡片图谱 + 收件箱审核                │
└──────────────────────────────────────────────────────────┘
```

#### 读取路径

```
[route_input 节点]
    │
    ├─ ProfileProvider
    │   └─ get_profile_text() → 全量 EAV 读取 → 注入 SP
    │
    ├─ MemoryProvider
    │   ├─ RuleBasedGate: 含引用词才触发，其余不搜
    │   ├─ Gate 通过 → auxiliary 模型改写 query（结合上下文优化检索质量）
    │   └─ 向量检索 top-K（只搜 status=ACTIVE）→ 注入 SP
    │
    └─ 短期压缩检查: 超阈值则 LLM 摘要旧消息
```

#### 写入路径（与读取完全隔离）

```
[session_end / process_output]
    │
    ├─ MemoryExtractor: LLM 从对话中提取候选记忆
    │   └─ 去重合并写入（PENDING），不影响读取侧
    │
    ├─ ProfileUpdater: LLM 从对话中提取档案字段更新
    │
    └─ memory_write_tool: 对话中主动写入（PENDING）
```

#### 模块划分

```
memory/
├── schema.py                  # MemoryCard / 枚举类型
├── manager.py                 # 对外统一入口（绑定 user × agent）
├── extractor.py               # 从对话提取候选记忆
├── retrieval_gate.py          # 检索门控（RuleBasedGate）
├── profile/                   # 用户档案
│   ├── base.py                # EAV 抽象基类
│   ├── store.py               # SQLite 实现
│   └── updater.py             # session_end 提取更新
├── short_term/
│   ├── window.py              # ConversationWindow 数据结构
│   └── summarizer.py          # 按轮次触发的滚动摘要
├── long_term/
│   └── store.py               # 协调向量库 + 关系库的读写 + 去重合并
├── vector_stores/             # 向量库抽象 + 实现
│   ├── base.py / factory.py
│   ├── qdrant_store.py        # 推荐
│   ├── chroma_store.py        # 占位
│   └── milvus_store.py        # 占位
└── relational/                # 关系型存储抽象 + 实现
    ├── base.py / factory.py
    ├── sqlite_store.py
    └── mysql_store.py
```

#### 检索门控

只保留 `RuleBasedGate`（生产用）和 `AlwaysRetrieveGate`（测试用）。

| 条件 | 操作 |
|------|------|
| 含引用词（"上次""记得""之前""又""你忘了"等） | 召回 |
| 其余 | 不召回 |

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

记忆和知识库**使用同一个向量库实例**，通过不同 collection 隔离：
- `user_memories`：用户记忆卡片
- `game_knowledge`：游戏知识库

推荐 **Qdrant**（过滤能力强、部署简单），百万级向量性能足够。

---

### 3.3 Preset & Custom System (`presets/` + `custom/`)

**分离机制**：

```
presets/agents/default/          # 开发者定义，Git 管理
    ├── persona.yaml            # 完整人设
    ├── prompts.yaml            # 辅助任务提示词（记忆提取/情感分析等）
    └── config.yaml             # 行为配置（SP模式/记忆参数/Tool配置等）

custom/{user_id}/agents/default/ # 用户数据目录，运行时生成
    ├── persona_overrides.yaml  # 仅包含用户修改的字段
    └── config_overrides.yaml   # 仅包含用户修改的字段
```

注意：主 System Prompt 不再由 `prompts.yaml` 模板拼接。
它由 Context Providers 各自产出文本，在 `call_main_agent` 中动态组装。
`prompts.yaml` 只保留辅助任务的提示词模板。

---

### 3.4 Knowledge Base / RAG (`knowledge/`)

**流程**：
1. **Ingest**: 游戏知识文档 → 分块 → Embedding → 存入向量数据库
2. **Retrieve**: 用户通过 `knowledge_search_tool` 触发检索

**与长期记忆的区别**：
- 知识库 = 客观游戏知识（开发者维护），通过 Tool 访问
- 长期记忆 = 用户个人信息（运行时生成），通过 MemoryProvider 注入 SP

---

### 3.5 Voice Services (`services/voice/`)

ASR/TTS pipeline，支持流式处理，实现低延迟语音对话。

---

### 3.6 Vision / Screenshot (`services/vision/`)

前端截图 → WebSocket 传输 → Vision 模型分析 → 结果作为 ToolMessage 回到对话流。

---

## 4. 前端架构 (frontend/)

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
| `/api/memory/cards` | GET | 列出记忆卡片（审核/管理） |
| `/api/memory/cards/{id}/status` | PUT | 审核卡片（通过/拒绝） |
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

## 7. 迭代路线

| Phase | 目标 | 核心任务 | 验收标准 |
|-------|------|----------|----------|
| **1. 能说话** (1w) | 文本对话跑通 | 人设加载 → LangGraph ReAct → 用户微调 | 有人设地聊天，用户能改性格 |
| **2. 能听能看** (2w) | 多模态核心体验 | ASR/TTS + 截图分析 + 情感/Live2D | 语音聊天 + 看游戏画面 + 表情 |
| **3. 能记住 + 懂游戏** (1.5w) | 短期记忆 + 联网 | 摘要压缩 + Profile 档案 + 联网搜索 | 30轮不丢；跨session记称呼；答游戏问题 |
| **4. 深度记忆** (2w) | 长期记忆 RAG | 向量库 + 提取去重 + MemoryProvider + 审核API | 跨session记住偏好/事件 |
| **5. 深度游戏理解** (1.5w) | 游戏知识库 | 知识摄入 + game_info_tool 知识库路径 | 攻略准确度提升 |
| **6. 生产化** (2w) | 上线准备 | MySQL + 记忆管理UI + 监控 + 压测 | 多用户并发 |
