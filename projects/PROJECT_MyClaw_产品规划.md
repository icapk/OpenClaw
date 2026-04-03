# MyClaw 产品规划

> 代号：MyClaw
> 定位：OpenClaw × Claude Code 整合的新一代 AI Agent 平台
> 状态：规划中

---

## 产品愿景

做一个比 OpenClaw 和 Claude Code 都更好的产品：
- **OpenClaw 的强项**：多 Agent 协作、框架化管理、多通道接入
- **Claude Code 的强项**：深度编程能力、本体质量高
- **我们的差异化**：更易用、更透明、更强的记忆系统

---

## 核心架构

### Agent 三层架构

```
┌─────────────────────────────────────┐
│          Agent = 大脑 + 工具 + 记忆   │
├─────────────────────────────────────┤
│  大脑（Brain）  │  LLM 模型          │
│  工具（Tools）  │  插件 + MCP        │
│  记忆（Memory） │  人类可读层 + 程序高效层  │
└─────────────────────────────────────┘
```

---

## 记忆系统设计（两层架构）

### 第一层：人类可读层

- **格式**：Markdown（`.md`）
- **用途**：
  - 管理员直接查看、编辑
  - 跨平台可迁移
  - 便于调试和干预
- **代表文件**：
  - `MEMORY.md` — 长期记忆
  - `memory/YYYY-MM-DD.md` — 每日工作记录
  - `SOUL.md` — Agent 身份定义
  - `USER.md` — 用户信息
  - `AGENTS.md` — 工作区规范

### 第二层：程序高效层

- **格式**：JSON（`.jsonl`）或数据库
- **用途**：
  - Agent 运行时快速读写
  - 高频访问的低延迟存储
  - 结构化查询能力
- **特点**：
  - 机器可读，程序直接解析
  - 对用户透明，不可直接编辑

### 两层同步机制

```
┌──────────────────────────┐
│  人类可读层（Markdown）   │  ← 管理员直接操作
└────────────┬─────────────┘
             │ 同步（自动 / 手动）
             ↓
┌──────────────────────────┐
│  程序高效层（JSON/SQLite）│  ← Agent 运行时调用
└──────────────────────────┘
```

**同步原则**：
- 人类可读层为"主"，程序高效层为"从"
- 程序高效层故障时，不影响人类可读层独立运作
- 避免双写冲突，以程序高效层为"真相源"

---

## 工具层设计

### 设计原则

- **插件系统**：完全自定义，扩展性无限
- **MCP 兼容层**：支持接入现有 MCP Server 生态
- 优先使用插件架构，MCP 作为补充

### 架构图

```
Agent 工具层
   │
   ├── 插件系统（自有生态，完全自定义）
   │     └── 可接入任何外部能力
   │
   └── MCP 客户端（标准协议，接入社区生态）
         └── 一个客户端，接所有 MCP Server
```

---

## OpenClaw 架构深度拆解

### 核心架构：Gateway 模式

OpenClaw 的核心是一个 **Gateway 守护进程**，它：

- 拥有所有消息渠道（WhatsApp、Telegram、Discord、Signal 等）
- 客户端通过 **WebSocket** 连接到 `127.0.0.1:18789`
- 节点（macOS/iOS/Android）也通过 WebSocket 连接，声明 `role: node`
- 一个 Gateway 控制一个主机上的所有会话

```
┌─────────────────────────────────────────────────┐
│                   Gateway                        │
│  ┌─────────────────────────────────────────┐    │
│  │  Provider Connections (WhatsApp/Telegram) │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │  WebSocket API (typed, JSON Schema)      │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │  Events: agent, chat, presence, heartbeat│    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
           ↕ WebSocket
┌─────────────────────────────────────────────────┐
│  Clients: macOS app / CLI / web admin / nodes   │
└─────────────────────────────────────────────────┘
```

---

### Agent Loop（Agent 运行循环）

这是 OpenClaw 最核心的部分——一个消息如何变成 Agent 的动作和回复：

```
Entry → Context Assembly → Model Inference → Tool Execution → Streaming Reply → Persistence
```

**关键流程：**

1. **Entry** — `agent` RPC 验证参数，解析 session，返回 `{ runId, acceptedAt }` 立即响应
2. **Queueing** — 运行按 session key 序列化（session lane），防止工具/session 竞争
3. **Session + Workspace 准备** — 解析并创建 workspace，装载 skills
4. **Prompt Assembly** — 从 OpenClaw 基础 prompt + skills + bootstrap context 构建
5. **Hook Points** — 可注入的拦截点：
   - `agent:bootstrap` — 构建 bootstrap 文件时
   - `before_prompt_build` — session 加载后、prompt 提交前
   - `before/after_tool_call` — 工具调用前后
   - `agent_end` — 运行完成后
6. **Streaming** — Assistant delta 从 pi-agent-core 流式输出
7. **Compaction** — 上下文窗口满时自动压缩

---

### Context Engine（上下文引擎）

这是一个**可插拔**的架构：

| 生命周期点 | 功能 |
|---|---|
| **Ingest** | 新消息加入时存储/索引 |
| **Assemble** | 模型运行前返回适合 token 预算的消息集 |
| **Compact** | 上下文满时压缩历史 |
| **After Turn** | 运行完成后持久化状态 |

**内置 Legacy Engine：**
- Ingest: no-op
- Assemble: pass-through
- Compact: 内置 summarization

**Plugin Engine：**
- 可注册自定义 context engine
- 可选择 `ownsCompaction: true`（拥有自己的压缩策略）或 `false`（委托给内置）

---

### 多 Agent 路由

OpenClaw 支持**多个隔离的 Agent**，每个 Agent 有：

- **自己的 Workspace**（文件、AGENTS.md/SOUL.md/USER.md、 persona 规则）
- **自己的 State 目录**（auth profiles、model registry、per-agent 配置）
- **自己的 Session Store**（聊天历史 + 路由状态）

**路由绑定（Bindings）：**
- 按 `(channel, accountId, peer)` 路由到不同 Agent
- **确定性 + 最具体匹配优先**
- 支持 Discord role routing、Telegram per-bot、WhatsApp per-number

---

### 记忆系统

```
┌────────────────────────────────────────────┐
│  Workspace 记忆文件（Markdown）              │
├────────────────────────────────────────────┤
│  memory/YYYY-MM-DD.md  — 每日日志（追加）   │
│  MEMORY.md                 — 精选长期记忆   │
└────────────────────────────────────────────┘
```

**两个记忆工具：**
- `memory_search` — 语义搜索（semantic recall）
- `memory_get` — 按路径/行号读取

**自动内存刷新（pre-compaction ping）：**
- Session 接近自动压缩时，触发**静默 agentic turn**
- 提醒 model 将持久化记忆写入磁盘
- 然后再压缩上下文

---

### 压缩机制

**Compaction = 将旧对话压缩成摘要，保留到 session 历史中**

```
Before: [old messages] + [compaction point] + [recent messages]
After:  [compaction summary] + [recent messages]
```

- **Auto-compaction** — Session 接近 context window 时自动触发
- **Manual compaction** — `/compact` 命令强制压缩
- **Plugin engines** — 可接入自定义压缩策略（DAG summaries、vector retrieval 等）

---

### 委托架构（Delegate Architecture）

这是 OpenClaw 的高级特性——让 Agent 作为**具名委托**运作：

| 层级 | 能力 |
|---|---|
| **Tier 1** | 只读 + 草稿（不能发送） |
| **Tier 2** | 代表发送（on behalf of） |
| **Tier 3** | 主动执行（按 schedule，无须每次批准） |

**安全模型：**
- Hard blocks（非禁止操作）
- Per-agent tool restrictions
- Sandbox isolation
- Audit trail（日志）

---

### System Prompt 结构

OpenClaw 的 System Prompt 由以下部分组成：

```
┌─────────────────────────────────────────────────┐
│  Tooling          — 当前工具列表 + 简短描述       │
│  Safety           — 安全 guardrail 提醒           │
│  Skills           — 告知模型如何按需加载 skill    │
│  OpenClaw Update  — 如何运行 config.apply/update  │
│  Workspace        — 工作目录                       │
│  Sandbox          — 沙箱信息（启用时）            │
│  Date & Time      — 用户本地时区                   │
│  Reply Tags       — 支持 provider 的回复标签语法   │
│  Heartbeats       — 心跳 prompt 和 ack 行为       │
│  Runtime          — host, OS, node, model, repo   │
│  Reasoning        — 推理可见性 + /reasoning 开关  │
└─────────────────────────────────────────────────┘
```

**Prompt Modes：**
- `full`（默认）：包含所有 sections
- `minimal`：用于 sub-agent，省略 Skills、Memory Recall、OpenClaw Self-Update 等
- `none`：仅包含基础身份行

---

### 插件 Hook 系统

OpenClaw 有两套 Hook 系统：

**1. Internal Hooks（Gateway Hooks）：**
- `agent:bootstrap` — 构建 bootstrap 文件时
- Command hooks: `/new`, `/reset`, `/stop` 等

**2. Plugin Hooks（Agent + Gateway 生命周期）：**

| Hook | 时机 | 用途 |
|---|---|---|
| `before_model_resolve` | session 前 | 覆盖 provider/model |
| `before_prompt_build` | session 加载后 | 注入 prependContext/systemPrompt |
| `before/after_tool_call` | 工具调用前后 | 拦截工具参数/结果 |
| `agent_end` | 运行完成后 | 检查最终消息列表 |
| `before/after_compaction` | 压缩周期 | 观察或注解 |
| `session_start/end` | session 边界 | 生命周期事件 |
| `gateway_start/stop` | Gateway 生命周期 | 启动/停止事件 |

---

## Claude Code 架构深度拆解

### 核心架构：单 Agent CLI

Claude Code 是一个**单 Agent CLI 工具**，设计哲学是"最小干预"。

**核心身份定义：**
```
"You are Claude Code, Anthropic's official CLI for Claude."
```

**核心行为原则：**
1. **Read first** — 不读代码不修改
2. **Minimalism** — 不创建不必要的文件/抽象
3. **Be concise** — 直接给答案，不废话
4. **Verify** — 运行测试确认后再报告完成
5. **Stay focused** — 不做超出需求之外的改进

---

### 工作流

```
Understand → Explore → Plan → Implement → Verify
```

- **Understand** — 明确要解决什么问题
- **Explore** — 探索现有代码库结构
- **Plan** — 用 `/plan` 规划路径
- **Implement** — 写最小必要代码
- **Verify** — 验证方案有效

---

### 工具集设计

Claude Code 的工具集是为**开发者工作流原生设计**的：

| 工具 | 用途 | 设计意图 |
|---|---|---|
| Read | 读文件 | 不让你用 cat |
| Edit | 精准编辑 | 不是全文件重写 |
| Write | 创建文件 | 明确的新建 |
| Glob | 按模式找文件 | 不是用 find |
| Grep | 搜索内容 | 不是用 grep |
| Bash | 执行命令 | 终端能力 |
| Agent | 启动子 Agent | 复杂任务分解 |
| WebSearch/WebFetch | 网页搜索/获取 | 开发者调研用 |

**关键洞察：工具名 = 开发者心智模型**

---

### 风险意识

Claude Code 对危险操作有明确的确认机制：

- 执行破坏性操作（force-push、reset、clean）前必须确认
- 不跳过 hooks 或签名（除非明确要求）
- 只在明确要求时才能修改 commit

---

## 两者核心差异对比

| 维度 | OpenClaw | Claude Code |
|---|---|---|
| **架构类型** | 框架（Gateway + 多 Agent） | 单 Agent CLI |
| **核心定位** | 多 Agent 协作 + 个人助理 | 深度编程搭档 |
| **执行模型** | 层级式任务分解 | 单一 Agent 执行 |
| **多 Agent** | 原生支持（binding 路由） | 不支持 |
| **记忆系统** | Markdown 双层（每日 + 长期） | JSON session 文件 |
| **工具层** | 插件系统 + MCP 兼容 | MCP/Skills |
| **扩展方式** | 插件 Hook | MCP Server |
| **System Prompt** | 组件化（bootstrap 文件注入） | 固定原则集 |
| **上下文管理** | 可插拔 Context Engine | 内置 session 管理 |
| **压缩机制** | 可配置 + 可插件化 | 未公开 |
| **部署方式** | 本地框架 + 多通道 | CLI |
| **适用场景** | 个人助理、多任务管理 | 深度编程任务 |

---

## 参考对比

| 维度 | OpenClaw | Claude Code | MyClaw（目标） |
|------|----------|-------------|----------------|
| 架构类型 | 框架 | CLI | 框架 + CLI 融合 |
| 记忆格式 | Markdown | JSON | Markdown + JSON 双层 |
| 工具层 | 插件系统 | MCP/Skills | 插件 + MCP 兼容 |
| 多 Agent | 支持 | 不支持 | 支持 |
| 编程深度 | 一般 | 强 | 强 |
| 人类可干预性 | 高 | 低 | 高 |
| 上手难度 | 中 | 低 | 低 |

---

## 待细化内容

- [ ] ContextEngine 设计（学习 OpenClaw 的可插拔架构）
- [ ] PermissionEngine 设计（学习 OpenClaw 的 Hook 系统）
- [ ] JobQueue 设计（学习 OpenClaw 的 session lane 序列化）
- [ ] 插件系统接口规范
- [ ] MCP 客户端实现方案
- [ ] 两层同步机制详细设计
- [ ] Stage2 压缩算法设计

## 关键学习点总结

### OpenClaw 的核心优势（值得借鉴）

1. **Gateway 架构** — 统一接入所有消息通道
2. **Context Engine 可插拔** — 允许自定义上下文管理策略
3. **Hook 系统** — 精细的生命周期拦截点
4. **Multi-Agent 路由** — 多 Agent 隔离 + 绑定路由
5. **记忆系统** — 自动 pre-compaction 刷新
6. **Delegate 架构** — 组织级别的委托代理模型
7. **Bootstrap 文件注入** — SOUL.md/AGENTS.md/USER.md 系统

### Claude Code 的核心优势（值得借鉴）

1. **Minimalism 哲学** — 不多做，不少做，刚好做对
2. **开发者原生工具命名** — Read/Edit/Write/Grep 而不是 cat/vi
3. **Verify 优先** — 测试通过才算完成
4. **先读再改** — 不读上下文不修改
5. **Plan 工作流** — 规划先行，实现其后
6. **风险确认机制** — 危险操作前主动确认

### 我们产品的差异化方向

1. **更好的记忆系统** — 结合 OpenClaw 的 Markdown 双层 + Claude Code 的结构化 session
2. **更开放的插件系统** — OpenClaw 的 Hook 架构 + MCP 生态
3. **更智能的任务分解** — 学习 OpenClaw 的 multi-agent + Claude Code 的 verify 机制
4. **更透明的控制** — 管理员可干预、可回滚、可审计
5. **更轻量的部署** — 保留 OpenClaw 的本地部署优势，但简化配置

---

*最后更新：2026-04-01*
