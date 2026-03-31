# Claude Code Agentic Harness 分析报告

> 版本：0.117.0 | 分析日期：2026-04-01
> 数据来源：`~/.codex/` 配置、SQLite 状态库、会话 JSONL

---

## 一、什么是 Agentic Harness？

Claude Code 的核心并非大模型本身，而是一个用 **Rust 编写的本地二进制**（`codex`，142MB Mach-O ARM64），业界称之为 **Agentic Harness（代理线束系统）**。

```
用户输入 → Harness 编排层 → Model API（GPT-5.4 等）
                         ↕
              Harness 执行层（Tools / Shell / 文件系统）
                         ↕
              状态持久化层（SQLite + JSONL）
```

Harness 是一个**pure 编排层**：它不做推理，但控制推理的一切前提条件——上下文怎么注入、工具怎么路由、权限怎么检查、任务怎么恢复。它的存在把"一个能思考的模型"变成了"一个能干活的 Agent"。

---

## 二、Model 与 Tools 的连接机制

### 2.1 Model 连接

Claude Code 通过 OpenAI 兼容的 Chat Completions API 调用远程模型，配置在 `~/.codex/config.toml`：

```toml
model = "gpt-5.4"
model_reasoning_effort = "medium"
```

模型元数据（能力描述、context window、工具支持情况）从远程服务器动态获取，缓存在 `~/.codex/models_cache.json`。当前使用的模型 `gpt-5.4`：

- **Context Window**: 258,400 tokens（有效利用率 95%）
- **支持 reasoning summaries**（思维摘要）
- **支持 parallel tool calls**（并行工具调用）
- **Truncation Policy**: `tokens` 模式，阈值 10,000 tokens

### 2.2 Tools 连接

Tools 不在 Model 侧定义——它们由 **Harness 侧通过 JSON Schema 动态注册**，并通过 `turn_context` 注入给 Model。

**动态工具注册**（`thread_dynamic_tools` 表）：

| 字段 | 说明 |
|------|------|
| `thread_id` | 绑定到特定 Thread |
| `position` | 工具优先级顺序 |
| `name` | 工具名称（Model 调用时使用） |
| `description` | 描述（Model 决定是否调用） |
| `input_schema` | JSON Schema（参数校验） |
| `defer_loading` | 延迟加载标志 |

当前唯一的动态工具是 `read_thread_terminal`（读取桌面终端输出），由 VSCode 插件注册。

**核心内置工具**由 Harness 内置实现，Model 通过 `multi_tool_use.parallel` 语义调用：
- 文件读写 / 搜索（`rg`、`cat`、`nl`）
- Shell 命令执行（通过 sandbox 沙箱）
- 代码编辑（`apply_patch`）
- 网络请求（在 `network_access: true` 时）

### 2.3 Model-Tool 循环

```
Turn 开始
  ↓
Harness 注入：base_instructions + AGENTS.md + Skills + Permissions + Environment
  ↓
Model 生成 Tool Calls（或文本响应）
  ↓
Harness 拦截 Tool Calls：
  - 权限检查（sandbox_policy / prefix_rule）
  - 路由到对应工具处理器
  - 执行文件系统 / Shell 操作
  ↓
Tool 结果注入回 Model 上下文
  ↓
下一个 Turn
```

---

## 三、上下文注入机制

Claude Code 的上下文不是简单拼凑 prompt，而是一套**分层注入协议**。每次 Turn 开始，Harness 向 Model 注入以下信息块：

### 3.1 System Prompt（来自 `models_cache.json`）

Model 的 `base_instructions` 字段定义了 Codex 的核心人格和交互规范：

- **人格定位**：务实的资深软件工程师（pragmatic）
- **核心价值观**：Clarity、Pragmatism、Rigor
- **交互规范**：简洁、不废话、以终为向
- **工具规范**：优先用 `rg` 而非 `grep`，并行工具调用用 `multi_tool_use.parallel`

### 3.2 Turn Context（来自 `turn_context` 事件）

```json
{
  "turn_id": "019d4609-a6d5-74c1-a315-2e388d2c0f61",
  "cwd": "/Users/a1/.openclaw/workspace/agents/developer",
  "current_date": "2026-04-01",
  "timezone": "Asia/Shanghai",
  "approval_policy": "on-request",
  "sandbox_policy": {
    "type": "workspace-write",
    "writable_roots": ["/Users/a1/.codex/memories", ...],
    "network_access": false
  },
  "model": "gpt-5.4",
  "personality": "pragmatic",
  "collaboration_mode": { "mode": "default", "settings": {...} },
  "effort": "medium",
  "summary": "none"
}
```

### 3.3 User Instructions（来自 AGENTS.md）

`AGENTS.md` 的内容通过 `<user_instructions>` 块注入。这是**用户自定义行为规范**，由 Harness 从工作区根目录自动读取并注入 Model 上下文。

当前注入的 AGENTS.md 内容包含：
- 木白AI团队协作规范（三省六部架构）
- 工作流程（旨意 → 方案 → 审核 → 执行 → 交付）
- 文件规范、权限矩阵、核心原则
- OpenClaw workspace 标准规范（Memory、Tools、Heartbeat）

### 3.4 Permissions Instructions（沙箱策略）

通过 `<permissions instructions>` 块注入，包含：
- **Sandbox Type**：`workspace-write`（只允许在 cwd 和 writable_roots 写文件）
- **Escalation 机制**：`require_escalated` + `justification` 参数
- **Prefix Rule**：已批准的命令前缀白名单（如 `["npm", "run", "dev"]`）
- **Network Access**：当前为 `false`
- **Writable Roots**：`/Users/a1/.codex/memories` 等目录

### 3.5 Skills Instructions

通过 `<skills_instructions>` 块注入，当前会话可用的 Skills：
- `imagegen`：AI 图片生成
- `openai-docs`：OpenAI 官方文档查询
- `plugin-creator`：插件创建脚手架
- `skill-creator`：创建新 Skill
- `skill-installer`：安装 Skill

每个 Skill 有触发规则（名称匹配 / 描述匹配），Model 在 Turn 中可主动调用对应 SKILL.md。

### 3.6 Collaboration Mode

通过 `<collaboration_mode>` 块注入。当前为 `default` 模式：
- `request_user_input` 工具不可用
- Model 应自主决策，不频繁提问
- 有 `plan` / `default` 两种模式

---

## 四、权限与审批模型

### 4.1 审批模式（`approval_policy`）

存储在 `threads` 表的 `approval_mode` 字段：

| 模式 | 说明 |
|------|------|
| `on-request` | 默认；高权限操作需用户审批 |
| `bypass-all` | 跳过所有审批（仅供受信任环境） |
| `bypass-powerful` | 跳过"强大"操作的审批 |

### 4.2 沙箱策略（`sandbox_policy`）

```json
{
  "type": "workspace-write",
  "writable_roots": ["/Users/a1/.codex/memories", ...],
  "network_access": false
}
```

- **workspace-write**：只允许在 cwd 和 writable_roots 目录写文件
- **network_access**：当前为 `false`，禁止网络请求
- **Tmpdir 排除**：`exclude_tmpdir_env_var: false`（允许 tmp 访问）

### 4.3 Prefix Rule 系统

`~/.codex/rules/default.rules` 中存储了命令前缀白名单规则：

```python
prefix_rule(pattern=["npm", "run", "dev"], decision="allow")
prefix_rule(pattern=["cargo", "test"], decision="allow")
```

每条规则由 Harness 在命令执行前匹配，**匹配则直接放行**，不匹配则触发审批流程。规则是**持久化**的（存储在 `default.rules`），一次批准后效。

### 4.4 Escalation 机制

当命令超出沙箱范围时，Model 通过工具参数请求 escalation：

```json
{
  "sandbox_permissions": "require_escalated",
  "justification": "Do you want to download and install dependencies for this project?"
}
```

用户批准后，命令在沙箱外执行，并可选择"记住此规则"（生成新的 prefix_rule）。

---

## 五、任务持久化与恢复机制

### 5.1 Thread（会话）持久化

每次会话创建时，Harness 在 `threads` 表中写入记录：

```sql
CREATE TABLE threads (
    id TEXT PRIMARY KEY,              -- UUID
    rollout_path TEXT NOT NULL,        -- JSONL 文件路径
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    model_provider TEXT NOT NULL,     -- "openai"
    cwd TEXT NOT NULL,                -- 工作目录
    title TEXT NOT NULL,              -- 会话标题
    sandbox_policy TEXT NOT NULL,     -- JSON 序列化沙箱策略
    approval_mode TEXT NOT NULL,      -- 审批模式
    tokens_used INTEGER NOT NULL,     -- 累计 token 消耗
    git_sha TEXT,                     -- Git commit hash
    git_branch TEXT,                   -- 当前分支
    model TEXT,                        -- 具体模型
    reasoning_effort TEXT,             -- 推理强度
    ...
);
```

### 5.2 Rollout JSONL（完整消息历史）

每个 Thread 对应一个 JSONL 文件（如 `rollout-2026-04-01T06-35-30-019d4609....jsonl`），记录了完整的多轮交互：

```jsonl
{"timestamp":"...","type":"session_meta",   "payload":{...}}  ← 元信息（base_instructions, git）
{"timestamp":"...","type":"event_msg",      "payload":{"type":"task_started",...}}
{"timestamp":"...","type":"response_item",  "payload":{"type":"message","role":"developer",...}}
{"timestamp":"...","type":"response_item",  "payload":{"type":"message","role":"user",...}}
{"timestamp":"...","type":"turn_context",    "payload":{...}}  ← 每轮上下文
```

**事件类型**：
- `session_meta`：会话初始化（包含完整的 base_instructions 和 git 信息）
- `event_msg`：会话事件（task_started, task_done 等）
- `response_item`：Model 或 User 的消息
- `turn_context`：每轮 Turn 的上下文快照（AGENTS.md、sandbox_policy 等）

### 5.3 任务恢复流程

```
用户启动 codex --resume <thread_id>
  ↓
Harness 从 state_5.sqlite 读取 Thread 元信息
  ↓
加载对应 JSONL 文件，重建完整的消息历史
  ↓
从 stage1_outputs 恢复 Memory（如果启用）
  ↓
重新建立 Model 上下文（注入 base_instructions + 历史消息）
  ↓
继续执行
```

### 5.4 Stage1 Memory（跨会话记忆）

`stage1_outputs` 表存储了 Agent 的记忆摘要：

```sql
raw_memory TEXT,        -- 原始记忆内容
rollout_summary TEXT,   -- 摘要
rollout_slug TEXT,      -- 记忆标识
usage_count INTEGER,     -- 使用次数
selected_for_phase2 INTEGER  -- 是否被 phase2 选中
```

这是一个**两阶段记忆系统**：
1. **Phase 1**：将历史上下文压缩为 rollout_summary
2. **Phase 2**：选择性加载相关记忆到当前会话

### 5.5 后台任务队列（Jobs / Agent Jobs）

```sql
-- Jobs：分布式任务队列
CREATE TABLE jobs (
    kind TEXT NOT NULL,        -- 任务类型
    job_key TEXT NOT NULL,     -- 唯一键
    status TEXT NOT NULL,      -- pending / running / completed / failed
    worker_id TEXT,            -- 执行者 ID
    retry_remaining INTEGER,   -- 重试剩余次数
    lease_until INTEGER,       -- 租约过期时间
    last_error TEXT
);

-- Agent Jobs：长时任务
CREATE TABLE agent_jobs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,       -- pending / running / completed / failed
    instruction TEXT NOT NULL,  -- 任务指令
    output_schema_json TEXT,    -- 输出格式
    created_at INTEGER,
    started_at INTEGER,
    completed_at INTEGER,
    max_runtime_seconds INTEGER,
    last_error TEXT
);
```

---

## 六、Agent Orchestration（多 Agent 编排）

### 6.1 Thread Spawn Edges

`thread_spawn_edges` 表支持子 Agent 派生：

```sql
-- 表结构（推测）
parent_thread_id TEXT,
child_thread_id TEXT,
spawn_reason TEXT,
created_at INTEGER
```

一个 Thread 可以派生多个子 Thread，子 Thread 可独立运行后合并结果。

### 6.2 Collaboration Modes

| 模式 | 说明 |
|------|------|
| `default` | 完全自主执行，不调用 `request_user_input` |
| `plan` | 计划模式，先输出计划再执行 |

### 6.3 Effort Levels

`model_reasoning_effort` 参数控制推理深度：

| 级别 | 适用场景 |
|------|----------|
| `low` | 简单查询、快速响应 |
| `medium` | 日常编码任务（默认） |
| `high` | 复杂问题 |
| `xhigh` | 超复杂问题 |

---

## 七、为什么说 Harness 才是 Claude Code 的核心？

### 7.1 Model 是通用推理引擎，Harness 赋予它"职业身份"

GPT-5.4 是一个通用大模型，什么都能推理，但没有身份。Harness 通过**分层上下文注入**让同一个模型在不同工作区表现出不同人格——在 OpenClaw workspace 里它是"开发工程师"，在另一个工作区可能是"产品经理"。

**没有 Harness，Model 只是一个 chat 机器人。**

### 7.2 Model 不知道自己能做到什么，Harness 知道

Model 的工具调用能力来自 Harness 提供的 JSON Schema 和描述信息。Model 并不知道系统里有哪些工具可用、每个工具的参数是什么——这些全部由 Harness 注入。

### 7.3 Model 无法保证安全性，Harness 强制执行

在没有 Harness 的情况下，Agent 可能会执行任意 Shell 命令。Harness 通过：
- **Sandbox Policy**：文件系统边界
- **Prefix Rule**：命令白名单
- **Escalation 机制**：高权限操作需人工审批
- **Approval Mode**：可配置的审批粒度

这四层机制让 Agent 的"自主性"和"安全性"可以精确平衡。

### 7.4 Model 无法跨会话记忆，Harness 构建了完整的持久化层

- **Threads 表**：元信息 + 状态
- **Rollout JSONL**：完整消息历史
- **Stage1 Memory**：压缩记忆摘要
- **Shell Snapshots**：Shell 状态快照

这使得 Claude Code 可以**随时中断、随时恢复**，而不丢失任何上下文。

### 7.5 Model 无法并行协调，Harness 提供了 Agent 编排能力

`thread_spawn_edges` + `Jobs` 队列 + `Agent Jobs` 表，构建了一个**多 Agent 任务协调系统**。一个父 Agent 可以派生子 Agent，分别完成子任务后汇总——这在复杂项目中是必要能力。

### 7.6 Model 的输出是随机的，Harness 把它变成确定的工作流

Harness 的 `base_instructions` 规定了 Model 的**输出格式规范**（`commentary` 通道 + `final` 通道）、**格式化规则**（扁平列表、不超过 70 行）、**行为准则**（不自报进度、不 cheerleading）。这让 Agent 的输出可预期、可解析、可用程序处理。

---

## 八、架构总结图

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code CLI / VSCode               │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              codex (Rust Binary - Harness)                   │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ Context     │  │ Permission   │  │ Tool Router        │  │
│  │ Assembler   │  │ Engine       │  │                    │  │
│  │             │  │              │  │  • file read/write │  │
│  │ • base_     │  │  • sandbox_  │  │  • shell exec      │  │
│  │   instructions  │   policy    │  │  • apply_patch    │  │
│  │ • AGENTS.md │  │  • prefix_   │  │  • network (opt)   │  │
│  │ • turn_ctx  │  │   rules      │  │                    │  │
│  │ • skills    │  │  • approval_ │  │                    │  │
│  │ • perms     │  │   modes      │  │                    │  │
│  └─────────────┘  └──────────────┘  └────────────────────┘  │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ Persistence │  │ Job Queue    │  │ Session Manager    │  │
│  │ Layer       │  │              │  │                    │  │
│  │             │  │  • Jobs      │  │  • Thread metadata  │  │
│  │  • state_   │  │  • Agent_    │  │  • Rollout JSONL   │  │
│  │    5.sqlite │  │    Jobs     │  │  • Shell snapshots  │  │
│  │  • JSONL    │  │  • Workers   │  │  • Stage1 Memory   │  │
│  └─────────────┘  └──────────────┘  └────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
    ┌─────────▼──────────┐   ┌─────────▼──────────┐
    │  Model API          │   │  Local Filesystem   │
    │  (gpt-5.4 via       │   │  Shell / Tools     │
    │   OpenAI compat)     │   │                    │
    └─────────────────────┘   └────────────────────┘
```

---

## 九、关键数据文件清单

| 文件 | 用途 |
|------|------|
| `~/.codex/state_5.sqlite` | Thread 元信息、Jobs、Agent Jobs、Memory 索引 |
| `~/.codex/logs_1.sqlite` | 运行时日志 |
| `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` | 完整消息历史 |
| `~/.codex/shell_snapshots/*.sh` | Shell 状态快照 |
| `~/.codex/models_cache.json` | 模型元数据缓存 |
| `~/.codex/config.toml` | 当前模型和 MCP 服务器配置 |
| `~/.codex/rules/default.rules` | 命令前缀白名单规则 |
| `~/.codex/AGENTS.md` | 用户自定义行为规范 |
| `~/.codex/memories/` | 跨会话记忆文件 |

---

## 十、结论

**Harness 才是 Claude Code 的核心，因为它把一个通用的推理引擎变成了一个可控的、持久的、可信的工作伙伴。**

Model 提供"智力"，Harness 提供：
1. **边界**（Security / Safety）
2. **记忆**（Persistence / Memory）
3. **工具**（Tool Routing / Execution）
4. **规范**（Behavior / Output Format）
5. **编排**（Multi-Agent / Job Queue）

没有 Harness，Model 只是一个 API 调用。**有了 Harness，Model 才成为一个能独自在真实世界里完成复杂任务的 Agent。**
