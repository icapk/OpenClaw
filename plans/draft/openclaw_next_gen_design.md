# OpenClaw Next Gen Design
## 融合 OpenClaw × Claude Code Harness，构建新一代 AI Agent 产品

**作者：** 中书省（产品规划层）  
**日期：** 2026-04-01  
**状态：** 深度调研完成，待门下省审议

---

## 一、背景与目标

### 背景

主人（木白）的核心诉求：

> 把 OpenClaw 和 Claude Code 的全部优势整合起来，做一个新的产品，具备两个系统的全部优势。

### 两个系统的核心基因

| 维度 | OpenClaw | Claude Code Harness |
|------|----------|-------------------|
| **架构哲学** | Gateway 中心化Daemon，插件化 | 轻量 harness adapter，多 backend 支持 |
| **运行时** | Pi Agent Core（单嵌入式） | 独立 agent backend adapter |
| **会话模型** | JSONL + session key | SQLite + JSONL 双存储 |
| **记忆系统** | Markdown 文件（MEMORY.md） | Stage1/Stage2 分层压缩记忆 |
| **工具系统** | 固定工具 + Tool Policy | JSON Schema 动态注册 |
| **权限系统** | exec security + allowlist | 白名单 + escalation 提示 |
| **多 Agent** | 三省六部 binding 路由 | Job Queue + Agent Jobs |
| **沟通通道** | channel 插件系统（飞书等） | commentary + final 双通道 |
| **上下文** | Context Engine（legacy/slot） | turn_context 分层注入 |
| **Skills** | AgentSkills 兼容（SKILL.md） | 三级 skills（bundled/managed/workspace） |

### 目标

**新产品代号：** `Wheat`（小麦）

> OpenClaw 是躯体，Harness 是大脑。Wheat = 有机体 + 智能引擎。

---

## 二、产品定位

### 核心价值主张

**Wheat** 是一款具备以下全部能力的 AI Agent 产品：

1. **开放架构**：保留 OpenClaw 的 Gateway Daemon + 插件生态
2. **智能循环**：引入 Claude Code 的完整 agent loop（think → plan → act → observe）
3. **双重记忆**：Markdown 文件记忆（易读可审计）+ SQLite/JSONL 分层压缩（高效）
4. **精细权限**：白名单 + escalation + 审计日志三重保障
5. **动态工具**：固定核心工具 + 按需注册临时工具（JSON Schema）
6. **多 Agent 编排**：OpenClaw 三省六部路由 + Harness Job Queue
7. **全通道覆盖**：OpenClaw 所有 channel + Harness commentary/final 双通道
8. **可观测性**：完整 token 审计、工具调用链、记忆压缩历史

---

## 三、架构总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Wheat Gateway                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │
│  │  Channel    │  │  ACP        │  │  Agent Loop Orchestrator     │  │
│  │  Plugins    │  │  Dispatch   │  │  (Pi Core + Harness Loop)   │  │
│  │  (Feishu,   │  │  (subagent  │  │                             │  │
│  │  Discord..) │  │   routing)  │  │                             │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────────┬──────────────┘  │
│         │                │                          │                 │
│         └────────────────┼──────────────────────────┘                 │
│                          ▼                                            │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │              AgentRuntime (融合层)                              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │  │
│  │  │  Pi Core     │  │  Harness     │  │  Loop Orchestrator   │  │  │
│  │  │  (tools,     │  │  Adapter     │  │  (think/plan/act/    │  │  │
│  │  │  models)     │  │  (turn_ctx,  │  │   observe cycle)      │  │  │
│  │  │              │  │   base_inst) │  │                      │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                          │                                            │
│         ┌────────────────┼────────────────┐                         │
│         ▼                ▼                ▼                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                   │
│  │ Context    │  │ Permission  │  │ Tool       │                   │
│  │ Engine     │  │ Engine     │  │ Router     │                   │
│  │ (融合层)   │  │ (融合层)   │  │ (融合层)   │                   │
│  └────────────┘  └────────────┘  └────────────┘                   │
│                          │                                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                   │
│  │ Memory     │  │ Job Queue   │  │ Comms      │                   │
│  │ System     │  │ (融合层)   │  │ Channel    │                   │
│  │ (三层)    │  │            │  │ (融合层)   │                   │
│  └────────────┘  └────────────┘  └────────────┘                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 架构说明

- **Gateway**（OpenClaw 原有）：管理所有 channel 连接、WebSocket 协议、会话路由
- **AgentRuntime**（融合层）：将 Pi Core 的固定工具/模型能力与 Harness 的循环执行能力融合
- **ContextEngine**（融合）：OpenClaw workspace 规范 + Harness turn_context 分层注入
- **PermissionEngine**（融合）：OpenClaw exec security + Harness 白名单/escalation
- **ToolRouter**（融合）：OpenClaw 固定工具 + Harness JSON Schema 动态注册
- **MemorySystem**（三层）：OpenClaw Markdown 文件 + Harness Stage1/Stage2 分层
- **JobQueue**（融合）：OpenClaw sessions_spawn + Harness Job/Agent Jobs 调度
- **CommunicationChannel**（融合）：OpenClaw channel 插件 + Harness commentary/final

---

## 四、模块详细设计

### 4.1 AgentRuntime（融合 Pi Core + Harness Loop）

**是什么：** Agent 的核心执行引擎，统一管理单轮对话循环。

**解决什么问题：**
- OpenClaw: Pi Core 提供了可靠的工具调用，但循环控制相对简单
- Harness: 提供了完整的 think/plan/act/observe 循环，但缺少持久化层和 channel 集成
- 融合目标：让 Pi Core 在 Harness 循环框架内执行，同时保留 OpenClaw 的 channel 输出能力

**核心 API：**
```typescript
interface AgentRuntime {
  // 启动一个完整 agent 运行
  run(params: RunParams): AsyncIterable<RunEvent>
  
  // 融合层的循环状态机
  runLoop(params: LoopParams): Promise<LoopResult>
  
  // 融合 Pi tools + Harness tool router
  executeTool(call: ToolCall): Promise<ToolResult>
  
  // 处理 commentary（中间思考）和 final（最终输出）
  emitCommentary(delta: string): void
  emitFinal(message: FinalMessage): void
}

interface LoopParams {
  sessionKey: string
  turnContext: TurnContext      // Harness turn_context
  baseInstructions: string      // Harness base_instructions
  tools: ToolDefinition[]       // 合并后的工具列表
  permissionEngine: PermissionEngine
  memorySystem: MemorySystem
  commentaryChannel: Writable  // 中间输出通道
  finalChannel: Writable        // 最终输出通道
}
```

**循环流程（融合后）：**

```
用户消息
    ↓
TurnContext 组装（Harness）
    ↓
BaseInstructions 注入
    ↓
┌─ Think 阶段 ─────────────┐
│  Pi Core 模型推理        │
│  输出：思考文本 → commentary channel │
│  输出：tool_calls → ToolRouter      │
│         ↓                            │
├─ Act 阶段 ──────────────┤
│  ToolRouter 执行工具    │
│  结果注入 turn_context  │
│         ↓                            │
├─ Observe 阶段 ──────────┤
│  MemorySystem 更新      │
│  JobQueue 检查          │
│         ↓                            │
└─ Final 阶段 ────────────┘
    输出 → final channel
    session 持久化
```

---

### 4.2 ContextEngine（融合 workspace 规范 + Harness 分层注入）

**是什么：** 管理对话上下文的组装、注入和压缩。

**解决什么问题：**
- OpenClaw 的 legacy context engine 采用"传 pass-through"，没有真正的智能注入策略
- Harness 的 turn_context 有完整的分层注入（system、stage1 memory、stage2 memory、turn content）
- 融合目标：建立明确的分层注入策略，同时支持 OpenClaw 的 bootstrap 文件系统

**核心 API：**
```typescript
interface ContextEngine {
  // 四层上下文组装
  assemble(params: AssembleParams): AssembledContext
  
  // 当上下文窗口满时压缩
  compact(params: CompactParams): CompactResult
  
  // 处理新增消息
  ingest(message: Message): IngestResult
  
  // 构建 turn_context（Harness 格式）
  buildTurnContext(session: Session): TurnContext
}

interface AssembleParams {
  sessionKey: string
  tokenBudget: number
  bootstrapFiles?: BootstrapFile[]  // OpenClaw workspace 文件
  turnContext?: TurnContext          // Harness turn_context
}

interface TurnContext {
  system: {
    baseInstructions: string        // 工具定义、权限规则、协议
    workspace规范?: string          // OpenClaw 特有：AGENTS.md/SOUL.md
  }
  stage1: {
    compressedHistory: string       // SQLite/JSONL 中的压缩历史摘要
    recentMemories: MemoryEntry[]   // 最近 N 条记忆
  }
  stage2: {
    sessionHistory: Message[]       // 当前 session 的消息历史（可截断）
  }
  turn: {
    currentInput: string
    availableTools: ToolDefinition[]
    activeJobs: Job[]
  }
}
```

**分层注入策略（融合后）：**

| 层级 | 来源 | 注入时机 | Token 预算 |
|------|------|----------|------------|
| L0: System | base_instructions + OpenClaw bootstrap | 每次运行 | 固定上限 |
| L1: Stage1 | 压缩后的记忆摘要（SQLite） | 每次运行 | 可配置 |
| L2: Stage2 | 当前 session 消息历史 | 每次运行 | 弹性 |
| L3: Turn | 当前轮输入 + 工具定义 | 每次运行 | 按需 |

---

### 4.3 PermissionEngine（融合 exec security + Harness 白名单/escalation）

**是什么：** 管理命令执行的权限控制，包括白名单、escalation 和审批流程。

**解决什么问题：**
- OpenClaw 有 exec 安全策略，但缺少 escalation 机制（用户交互式审批）
- Harness 有完整的 allowlist + escalation 流程，但缺少与 OpenClaw channel 的集成
- 融合目标：建立从 allowlist → escalation → approval → 执行 → 审计的完整链路

**核心 API：**
```typescript
interface PermissionEngine {
  // 检查命令是否在白名单
  checkAllowlist(command: string): AllowlistResult
  
  // 请求 escalation（需要用户确认）
  requestEscalation(params: EscalationParams): Promise<EscalationResult>
  
  // 执行经过审批的命令
  executeApproved(command: string, context: ExecContext): Promise<ExecResult>
  
  // 审计日志
  audit(event: AuditEvent): void
}

interface AllowlistResult {
  decision: 'allow' | 'deny' | 'escalate'
  reason?: string
}

interface EscalationParams {
  command: string
  context: ExecContext
  channel: 'feishu' | 'discord' | 'telegram' | 'cli'
  userId: string
  message?: string  // 用户提供的说明
}
```

**权限分级（融合后）：**

```
Level 0: 内置安全（Always Deny）
  - 破坏性系统命令
  - 凭据修改命令

Level 1: 白名单自动允许
  - read, ls, cat 等无害命令
  - 配置好的 allowlist 命令

Level 2: 需 escalation 确认
  - exec 类命令（带参数）
  - 文件写入类命令

Level 3: 需显式审批（Approve On Use）
  - 首次执行的命令
  - 新工具注册

Level 4: 永久拒绝（Safety Block）
  - 凭据/密钥读取
  - 外部网络请求（白名单外）
```

**审批流程：**

```
命令执行请求
    ↓
PermissionEngine.checkAllowlist
    ↓
┌─ allow → 直接执行
│
├─ deny → 返回拒绝原因
│
└─ escalate → 发送到 channel（飞书等）
               用户在 channel 中审批
               /approve 或 /deny
               ↓
          执行或拒绝
          ↓
     审计日志记录
```

---

### 4.4 ToolRouter（融合固定工具 + JSON Schema 动态注册）

**是什么：** 统一管理所有工具的注册、调用和结果处理。

**解决什么问题：**
- OpenClaw 工具系统相对固定，扩展需要修改源码或 skill
- Harness 工具通过 JSON Schema 动态注册，支持临时工具
- 融合目标：保留 OpenClaw 的核心工具，同时支持 Harness 风格的动态工具注册

**核心 API：**
```typescript
interface ToolRouter {
  // 注册固定工具（OpenClaw 原生）
  registerFixedTool(tool: FixedTool): void
  
  // 注册动态工具（Harness 风格）
  registerDynamicTool(schema: ToolSchema): string  // 返回 tool_id
  
  // 查找工具
  resolveTool(name: string): ToolDefinition | undefined
  
  // 执行工具调用
  execute(call: ToolCall): Promise<ToolResult>
  
  // 列出所有可用工具（用于 prompt injection）
  listTools(): ToolDefinition[]
}

interface ToolSchema {
  name: string
  description: string
  input_schema: JSONSchema7
  handler: (params: unknown) => Promise<unknown>
  ttl?: number  // 临时工具自动过期时间
}
```

**工具分类（融合后）：**

| 类型 | 来源 | 示例 | 生命周期 |
|------|------|------|----------|
| Fixed | OpenClaw Pi Core | read, write, exec, edit | 常驻 |
| Skill | OpenClaw SKILL.md | gh-issues, apple-notes | 按需加载 |
| Dynamic | Harness JSON Schema | 临时任务工具 | TTL 后自动注销 |
| MCP | MCP Server | mcp__github__issues_list | MCP 连接生命周期 |

---

### 4.5 MemorySystem（三层融合架构）

**是什么：** 统一管理 Agent 的记忆存储和检索。

**解决什么问题：**
- OpenClaw: MEMORY.md + memory/YYYY-MM-DD.md，优点是易读可审计，缺点是检索效率低
- Harness: SQLite + JSONL 两层存储，优点是压缩率高，缺点是不可直接阅读
- 融合目标：建立三层记忆系统，同时满足可审计性和高效性

**三层架构：**

```
Layer 1: Working Memory（工作记忆）
  存储：当前 session 消息历史（内存 + JSONL）
  特点：高速读写，按 session 隔离
  OpenClaw 兼容：完全复用 JSONL 格式

Layer 2: Compressed Memory（压缩记忆）
  存储：SQLite（OpenClaw 已有 session store 扩展）
  特点：Stage1 压缩（会话摘要）、Stage2 压缩（跨会话知识提取）
  触发时机：session 结束时 / compaction 时

Layer 3: Persistent Memory（持久记忆）
  存储：MEMORY.md + memory/*.md（Markdown 文件）
  特点：人类可读、可直接编辑、可版本控制
  访问：通过 memory_search 和 memory_get 工具
```

**核心 API：**
```typescript
interface MemorySystem {
  // 写入工作记忆（OpenClaw 兼容）
  writeWorking(sessionKey: string, message: Message): void
  
  // Stage1 压缩（会话摘要）
  compressSession(sessionKey: string): CompressedSummary
  
  // Stage2 压缩（知识提取）
  extractKnowledge(compressedSummaries: CompressedSummary[]): KnowledgeEntry
  
  // 持久化记忆读写
  readPersistent(query: string): MemoryEntry[]
  writePersistent(entry: MemoryEntry): void
  
  // 语义检索
  search(query: string, topK: number): SearchResult[]
}
```

**Stage1 压缩算法（融合 Harness）：**

```typescript
interface Stage1Compression {
  // 输入：一段会话历史（Message[]）
  // 输出：压缩摘要

  // 算法步骤：
  // 1. 按 turn 分割消息
  // 2. 每个 turn 提取：意图 + 关键决策 + 工具调用结果
  // 3. 合并相邻相似意图
  // 4. 生成 <500 token 的摘要
  // 5. 保留：文件名、函数名、关键参数（opaque identifiers）
  
  compress(messages: Message[]): CompressedSummary
}
```

**Stage2 压缩算法（融合 Harness）：**

```typescript
interface Stage2Compression {
  // 输入：多个 Stage1 摘要
  // 输出：跨会话知识条目

  // 算法步骤：
  // 1. 按主题聚类 Stage1 摘要（简单关键词匹配）
  // 2. 每个簇提取：主题 + 模式 + 关键事实
  // 3. 与已有 Knowledge Base 合并（去重）
  // 4. 保留可检索的向量表示（可选）
  
  extract(summaries: CompressedSummary[]): KnowledgeEntry[]
}
```

---

### 4.6 JobQueue（融合 sessions_spawn + Harness Job/Agent Jobs）

**是什么：** 管理后台任务调度和子 Agent 执行。

**解决什么问题：**
- OpenClaw 有 sessions_spawn 和 subagent 机制，但功能相对简单
- Harness 有完整的 Job Queue + Agent Jobs 调度（multi-tier priority）
- 融合目标：建立支持多优先级、可抢占、有限并发的任务队列

**核心 API：**
```typescript
interface JobQueue {
  // 提交任务
  submit(job: Job): JobId
  
  // 提交 Agent Job（子 agent 运行）
  submitAgentJob(job: AgentJob): AgentJobId
  
  // 查询状态
  getStatus(jobId: JobId): JobStatus
  
  // 取消任务
  cancel(jobId: JobId): void
  
  // 获取队列快照（调试用）
  snapshot(): QueueSnapshot
}

interface Job {
  id: JobId
  type: 'task' | 'agent'
  priority: 'low' | 'normal' | 'high' | 'critical'
  payload: TaskPayload | AgentPayload
  createdAt: number
  ttl?: number
}

interface AgentJob extends Job {
  type: 'agent'
  payload: {
    agent: string           // agent id
    task: string             // 任务描述
    model?: string           // 可选指定模型
    workspace?: string        // 可选指定 workspace
    timeout?: number          // 超时时间
    spawnMode: 'run' | 'session'
  }
}
```

**调度算法（融合 Harness）：**

```
优先级队列（Multi-Tier Priority Queue）

Tier 0: Critical（立即执行，无并发限制）
  - 用户显式请求（/run）
  - 紧急警报处理

Tier 1: High
  - 前台交互任务
  - 最多并发数: agents.defaults.maxConcurrent

Tier 2: Normal（默认）
  - 常规任务
  - 最多并发数: 4

Tier 3: Low
  - 后台任务（compaction、memory flush）
  - 最多并发数: 2

调度规则：
1. 同一 tier 内 FIFO
2. 高优先级任务可抢占低优先级（需配置）
3. 每个 session 同时只有 1 个活跃任务（lane 机制复用）
4. 全局并发上限由 agents.defaults.maxConcurrent 控制
```

---

### 4.7 CommunicationChannel（融合 channel 插件 + commentary/final 双通道）

**是什么：** 管理 Agent 与外部的消息通信。

**解决什么问题：**
- OpenClaw 有完整的 channel 插件系统（飞书、Discord、Telegram 等）
- Harness 有 commentary（中间思考）和 final（最终输出）的区分
- 融合目标：channel 系统负责路由，commentary/final 系统负责内容格式化

**核心 API：**
```typescript
interface CommunicationChannel {
  // 发送 commentary（中间思考）
  sendCommentary(sessionKey: string, delta: CommentaryDelta): void
  
  // 发送 final message（最终输出）
  sendFinal(sessionKey: string, message: FinalMessage): void
  
  // 注册 channel（OpenClaw channel 插件接口）
  registerChannel(channel: ChannelPlugin): void
  
  // 路由消息到对应 agent
  routeInbound(envelope: InboundEnvelope): RouteResult
}

interface CommentaryDelta {
  type: 'text' | 'tool_start' | 'tool_end' | 'think' | 'error'
  content: string
  toolCallId?: string
  timestamp: number
}

interface FinalMessage {
  text: string
  attachments?: Attachment[]
  replyTo?: string  // 消息 ID，用于 threading
  channelSpecific?: ChannelSpecificPayload
}
```

**Channel 路由（OpenClaw 复用）：**

```
Inbound Message
    ↓
Binding Resolution（按优先级）
  1. peer match（精确匹配）
  2. parentPeer match
  3. guildId + roles
  4. guildId
  5. accountId match
  6. channel fallback
    ↓
Agent Selection
    ↓
Session Key Resolution
    ↓
AgentRuntime.run()
    ↓
commentary → stream to channel（如支持）
final → deliver reply
```

---

### 4.8 SkillsSystem（融合 OpenClaw Skills + Harness 三级 Skills）

**是什么：** 管理 Agent 可用技能的定义、加载和执行。

**解决什么问题：**
- OpenClaw 使用 AgentSkills 兼容格式（SKILL.md + YAML frontmatter）
- Harness 有类似的三级 skills 系统
- 融合目标：统一 skills 格式和加载优先级

**核心 API：**
```typescript
interface SkillsSystem {
  // 加载 skills 目录
  loadSkills(workspaceDir: string): Skill[]
  
  // 过滤可用的 skills（按 config/env/binary 检查）
  filterSkills(skills: Skill[], context: SkillContext): Skill[]
  
  // 解析 SKILL.md
  parseSkill(content: string): ParsedSkill
  
  // 构建 skills prompt（注入 system prompt）
  buildSkillsPrompt(skills: Skill[]): string
  
  // 执行 skill 命令（通过 /skill command）
  executeSkillCommand(skill: Skill, command: string, args: string[]): Promise<string>
}
```

**加载优先级（完全复用 OpenClaw）：**

```
workspace/skills/（最高）
  ↓
workspace/.agents/skills/
  ↓
~/.agents/skills/
  ↓
~/.openclaw/skills/
  ↓
bundled skills（npm 包）
  ↓
skills.load.extraDirs（最低）
```

**SKILL.md 格式（增强版）：**

```markdown
---
name: gh-issues
description: Fetch GitHub issues, spawn sub-agents to implement fixes and open PRs
triggers:
  - "/gh-issues"
  - "github issues"
  - "fetch issues"
requires:
  binary: gh
  env:
    GITHUB_TOKEN: secret
tier: critical  # 优先级：critical/high/normal/low
---

# Skill Content
```

---

## 五、关键创新点

### 5.1 相比 OpenClaw 新增的能力

| 能力 | 说明 |
|------|------|
| **完整 Agent Loop** | think → plan → act → observe 循环，commentary 实时输出 |
| **动态工具注册** | 按需注册 TTL 工具，无需重启 |
| **Stage1/Stage2 压缩** | 高效记忆管理，解决长会话 token 爆炸问题 |
| **双通道通信** | commentary（中间）+ final（最终），channel 友好 |
| **Job Queue 调度** | 多优先级、可抢占、有限并发 |
| **Escalation 审批** | 交互式权限审批，无需离开 channel |
| **Agent Jobs** | 子 agent 运行，支持 session/run 两种模式 |

### 5.2 相比 Claude Code Harness 新增的能力

| 能力 | 说明 |
|------|------|
| **持久化 session** | JSONL transcript，跨 session 连续性 |
| **Workspace 规范** | AGENTS.md/SOUL.md/USER.md 文件系统 |
| **Channel 生态** | 飞书、Discord、Telegram、WhatsApp 等全通道 |
| **多 Agent 路由** | 三省六部 binding 机制 |
| **Skills 生态** | ClawHub 共享 skills 市场 |
| **工具政策** | Tool Policy 管道（OpenClaw 固定工具链） |
| **完整审计日志** | 所有 exec、permission、tool 调用完整记录 |
| **Gateway Daemon** | 常驻进程，支持 cron/heartbeat/automation |

### 5.3 两者融合产生的化学反应

1. **Harness 智能 × OpenClaw 持久**
   - Harness 的循环推理能力 + OpenClaw 的 session 持久化 = 更聪明且有记忆的 Agent

2. **动态工具 × 固定安全**
   - Harness 动态注册 + OpenClaw Tool Policy = 灵活且安全的工具系统

3. **分层记忆 × Markdown 可审计**
   - Harness Stage1/Stage2 压缩 + OpenClaw MEMORY.md = 高效且可读的长期记忆

4. **多优先级任务 × 全通道通知**
   - Harness Job Queue + OpenClaw channel 系统 = 智能调度 + 全通道送达

5. **Escalation × channel 审批**
   - Harness 权限 escalation + OpenClaw channel 插件 = 无需 CLI 的交互式审批

---

## 六、迁移路径

### 6.1 从 OpenClaw 迁移

OpenClaw 用户迁移到 Wheat 是**平滑升级**，核心 API 完全兼容。

**阶段 1：基础设施准备（2 周）**
- 扩展 session store 支持 SQLite（新增表）
- 实现 Stage1/Stage2 压缩接口
- 实现 AgentRuntime 融合层（保留 Pi Core 作为默认）

**阶段 2：并行运行（2 周）**
- Feature flag 控制新旧实现切换
- 新实现作为可选插件加载
- 监控稳定性和性能差异

**阶段 3：全面切换（1 周）**
- 默认启用新实现
- 旧实现标记为 deprecated
- 清理废弃代码

### 6.2 从 Claude Code Harness 迁移

Harness 用户迁移需要数据迁移和配置转换。

**配置转换：**
```json5
// Harness 配置
{
  "base_instructions": "...",
  "allowlist": ["read", "ls"],
  "escalate_commands": ["exec"],
  "tools": [...]
}

// Wheat 配置（等价）
{
  "agents": {
    "list": [{
      "id": "main",
      "tools": {
        "allow": ["read", "ls"],
        "escalate": ["exec"]
      }
    }]
  },
  "tools": {
    // Harness JSON Schema tools 映射到这里
  }
}
```

**记忆迁移：**
```bash
# 将 Harness SQLite 导入 Wheat
wheat migrate --from harness --sqlite ./harness.db --output ./workspace/memory/

# 将 JSONL transcript 导入 Wheat
wheat migrate --from harness --jsonl ./transcripts/ --output ~/.openclaw/agents/main/sessions/
```

---

## 七、优先级矩阵

### 7.1 模块优先级

| 模块 | 优先级 | 理由 |
|------|--------|------|
| AgentRuntime | P0 | 核心，所有功能依赖 |
| ContextEngine | P0 | 影响所有运行的质量 |
| MemorySystem | P1 | 长会话稳定性关键 |
| ToolRouter | P1 | 日常使用频率最高 |
| PermissionEngine | P1 | 安全关键，不可或缺 |
| JobQueue | P2 | 后台任务，可渐进 |
| CommunicationChannel | P2 | 已有 OpenClaw channel |
| SkillsSystem | P2 | 复用现有实现 |

### 7.2 实施路线图

**Q1（1-3月）：核心融合**
- AgentRuntime 融合层完成
- ContextEngine Stage1 压缩上线
- Pi Core + Harness Loop 并行运行

**Q2（4-6月）：能力增强**
- Stage2 压缩 + MemorySystem 三层架构
- ToolRouter 动态注册上线
- PermissionEngine escalation 完成

**Q3（7-9月）：规模化**
- JobQueue 调度算法上线
- CommunicationChannel commentary 支持
- SkillsSystem 增强版

**Q4（10-12月）：生态完善**
- ClawHub 集成
- Gateway 插件市场
- 多 Agent 协作优化

---

## 八、OpenClaw 当前短板分析

基于源码分析，OpenClaw 在以下方面存在改进空间：

### 8.1 Context Engine（legacy）

**问题：** 纯 pass-through，不做真正的智能上下文管理。compaction 只有简单的 summarization，没有分层策略。

**改进：** 引入 Harness turn_context 分层注入，实现 Stage1/Stage2 压缩。

### 8.2 Agent Loop

**问题：** OpenClaw 的循环是"prompt → model → tools → done"，没有 Harness 的 think/plan/act/observe 结构化循环。commentary 只能通过 verbose tool summary 实现，不够结构化。

**改进：** 引入结构化 agent loop，commentary channel 作为一级输出。

### 8.3 记忆系统

**问题：** MEMORY.md 全靠模型自觉写入，没有主动的知识提取和压缩机制。长 session token 爆炸问题只能靠 compaction 解决。

**改进：** Stage1（会话摘要）+ Stage2（知识提取）+ Stage3（持久化）三层架构。

### 8.4 权限系统

**问题：** exec security 有 allowlist，但 escalation 机制不完善（需要 CLI approve，不支持 channel 内审批）。

**改进：** channel 内 escalation + approval 流程。

### 8.5 工具注册

**问题：** 工具是固定的，扩展需要 skill 或修改源码。Harness 的 JSON Schema 动态注册更灵活。

**改进：** ToolRouter 支持动态工具注册 + TTL 自动注销。

### 8.6 任务调度

**问题：** sessions_spawn 是简单的 session fork，没有优先级和并发控制。

**改进：** 引入 multi-tier Job Queue，支持优先级和并发限制。

---

## 九、附录

### A. 模块边界清晰说明

```
AgentRuntime
  职责：管理单次 agent 运行的完整生命周期
  不管：session 持久化（MemorySystem 管）、channel 路由（CommunicationChannel 管）
  边界清晰：接收 TurnContext，输出 RunEvent

ContextEngine
  职责：管理上下文组装、压缩、注入
  不管：记忆内容生成（由 AgentRuntime 模型生成）
  边界清晰：输入 Message[]，输出 AssembledContext

PermissionEngine
  职责：命令级别的权限判断和审批
  不管：channel 消息过滤（CommunicationChannel 管）
  边界清晰：输入 Command，输出 AllowlistResult | EscalationResult

ToolRouter
  职责：工具的注册、查找、执行
  不管：权限判断（PermissionEngine 管）、结果格式化
  边界清晰：输入 ToolCall，输出 ToolResult

MemorySystem
  职责：记忆的存储、压缩、检索
  不管：上下文组装（ContextEngine 管）
  边界清晰：输入 Message[]，输出 MemoryEntry[]

JobQueue
  职责：后台任务的提交、调度、执行
  不管：任务内容（由调用方决定）
  边界清晰：输入 Job，输出 JobStatus

CommunicationChannel
  职责：消息的 channel 路由和格式化输出
  不管：agent 执行逻辑
  边界清晰：输入 InboundEnvelope，输出 OutboundMessage

SkillsSystem
  职责：skill 的加载、过滤、执行
  不管：skill 命令的 agent 逻辑
  边界清晰：输入 SkillName，输出 SkillResult
```

### B. OpenClaw 源码关键路径参考

| 功能 | 源码路径 |
|------|----------|
| Agent Loop | `dist/agents/pi-embedded-runner/` |
| Session 管理 | `dist/agents/session-*` |
| System Prompt | `dist/agents/system-prompt*` |
| Skills | `dist/agents/skills/` |
| Channel 插件 | `dist/channels/plugins/` |
| Feishu 扩展 | `dist/extensions/feishu/` |
| ACP Dispatch | `dist/acp/control-plane/` |
| Gateway 核心 | `dist/gateway/` |
| Plugin SDK | `dist/plugin-sdk/src/` |
| Config Schema | `dist/config/` |

### C. 融合度评估

| 融合点 | OpenClaw 占比 | Harness 占比 | 说明 |
|--------|---------------|--------------|------|
| AgentRuntime | 40% | 60% | Harness Loop 框架主导，Pi Core 提供工具执行 |
| ContextEngine | 20% | 80% | Harness turn_context 分层是核心 |
| PermissionEngine | 50% | 50% | OpenClaw exec security + Harness escalation |
| ToolRouter | 50% | 50% | OpenClaw 固定工具 + Harness 动态注册 |
| MemorySystem | 40% | 60% | Harness Stage1/Stage2 + OpenClaw Markdown |
| JobQueue | 30% | 70% | Harness 调度算法 + OpenClaw session fork |
| CommunicationChannel | 80% | 20% | OpenClaw channel 系统 + commentary |
| SkillsSystem | 90% | 10% | 几乎全部复用 OpenClaw |

---

**下一步：** 提交门下省审议，等待准奏后进入尚书省执行。
