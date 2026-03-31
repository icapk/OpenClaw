# Claude Code Harness 方法论迁移方案 — 小麦专属

> 规划层级：中书省  
> 起草日期：2026-04-01  
> 目标：让小麦（尚书省/AI 总管）获得世界级 AI Agent 运行时框架能力

---

## 一、现状差距分析

### 1.1 维度对比总览

| 维度 | Claude Code Harness | OpenClaw 现状 | 差距等级 |
|------|---------------------|--------------|---------|
| **上下文注入** | 分层流水线：base → AGENTS → Skills → Perms → turn_ctx | AGENTS.md/SOUL.md/USER.md + Skills + Runtime | ⚠️ 中 |
| **权限模型** | 沙箱 + 白名单 + 审批 + escalation | exec security mode (deny/allowlist/full) | 🔴 高 |
| **工具路由** | JSON Schema 动态注册，Model 盲注册 | 固定工具集编译时确定 | 🔴 高 |
| **持久化** | SQLite 元信息 + JSONL 消息历史 + Stage1 Memory | 文件系统 (MEMORY.md/daily logs) | ⚠️ 中 |
| **任务编排** | Job Queue + 子 Agent 派生 + 优先级 | sessions_spawn 基础派生 | ⚠️ 中 |
| **双通道通信** | commentary（进度）+ final（交付）原生 | 无原生支持，靠人工约定 | 🔴 高 |

---

### 1.2 各维度详细分析

#### 维度 1：上下文注入（Context Assembler）

**Harness 机制：**
```
base_instructions → AGENTS.md → Skills → Permissions → turn_context
```
每层有明确职责，层层叠加覆盖，Model 只能看到最终融合后的上下文。

**OpenClaw 现状：**
- AGENTS.md：workspace 约定（加载顺序：SOUL → USER → memory）
- Skills：独立 SKILL.md，通过 read 工具按需加载
- 运行时：Runtime 信息（model/host/channel）以注释形式注入
- **缺失**：无统一上下文流水线，无层覆盖（override）机制，无 turn 级别上下文隔离

**差距本质：** OpenClaw 的上下文是"文件堆叠"，Harness 是"流水线融合+覆盖策略"。

---

#### 维度 2：权限模型（Permission Engine）

**Harness 机制：**
```
沙箱策略（文件系统隔离、网络隔离）
    → 命令白名单（可执行命令列表）
    → 审批模式（BLOCK / AUDIT / FULL）
    → Escalation（危险命令升级人工审批）
```

**OpenClaw 现状：**
- exec 工具有 `security` 参数：deny / allowlist / full
- `ask` 参数：off / on-miss / always
- elevated 权限独立
- **缺失**：无文件系统沙箱、无网络隔离、无命令级白名单、无 escalation 机制

**差距本质：** OpenClaw 是"开关式"权限（允许/拒绝），Harness 是"策略引擎"（多层过滤+升级）。

---

#### 维度 3：工具路由（Tool Router）

**Harness 机制：**
- 工具以 JSON Schema 注册到 Harness
- Model 看不到工具列表，全靠 Harness 在推理时注入
- 工具可以动态注册/注销
- 支持工具版本管理和按需加载

**OpenClaw 现状：**
- 工具列表在系统启动时编译确定
- Model 的 system prompt 中包含完整工具描述
- 无 JSON Schema 动态注册机制
- skills 是静态文件，需要时手动 read

**差距本质：** OpenClaw 是"静态公告"，Harness 是"按需注入"。

---

#### 维度 4：持久化层（Persistence Layer）

**Harness 机制：**
```
SQLite  → Thread 元信息（id/状态/创建时间/父线程）
JSONL   → 完整消息历史（每轮对话一条 JSON 行）
Stage1  → 跨会话记忆（重要性分级提取）
```

**OpenClaw 现状：**
- MEMORY.md：人工维护的长周期记忆
- memory/YYYY-MM-DD.md：每日工作日志
- 无结构化元信息库
- 无消息历史归档机制
- 记忆全靠文件堆叠，无分级提取

**差距本质：** OpenClaw 是"人工笔记"，Harness 是"自动索引+分级存储"。

---

#### 维度 5：任务编排（Job Queue）

**Harness 机制：**
- 多任务队列（优先级 + 依赖图）
- 子 Agent 派生带元信息（parent_id / task_type / deadline）
- 任务可暂停/恢复/取消
- 结果汇总再路由

**OpenClaw 现状：**
- sessions_spawn 可派生子会话
- 无任务队列概念
- 子会话与父会话无结构化关联
- 无依赖管理

**差距本质：** OpenClaw 是"点对点派生"，Harness 是"有组织的任务网络"。

---

#### 维度 6：双通道通信（Dual-channel）

**Harness 机制：**
- **commentary channel**：实时进度流（Model 思考过程/中间状态），对用户可见
- **final channel**：结构化交付物（最终答案/代码/文件），确定后不再更改
- 两条通道逻辑分离，Model 可以边想边说

**OpenClaw 现状：**
- 无原生双通道
- 飞书等平台：单通道顺序输出
- 进度靠"我来帮你分析一下"之类的自然语言约定

**差距本质：** OpenClaw 是"单行道"，Harness 是"快车道+交付道分离"。

---

## 二、迁移优先级

### 优先级矩阵

```
高价值 × 易实现  →  优先启动（Q1）
高价值 × 难实现  →  分阶段攻坚（Q2-Q3）
低价值 × 易实现  →  有余力做（Q2）
低价值 × 难实现  →  长期规划（Q3+）
```

| 能力 | 价值 | 难度 | 优先级 | 理由 |
|------|------|------|--------|------|
| 上下文分层增强 | ★★★ | ★★ | 🔴 Q1 | 现有架构可扩展，投入小收益大 |
| Stage1 Memory 自动化 | ★★★ | ★★ | 🔴 Q1 | 文件系统→SQLite，体验跃升 |
| 双通道通信 | ★★★ | ★★ | 🔴 Q1 | 小麦专属，飞书天然支持 |
| 任务队列系统 | ★★ | ★★★ | 🟡 Q2 | 需要新基础设施 |
| 权限引擎升级 | ★★★ | ★★★★ | 🟡 Q2 | 核心安全，但实现复杂 |
| 工具动态路由 | ★★ | ★★★★ | 🟢 Q3 | 改动底层，需小心迁移 |
| 沙箱隔离 | ★★ | ★★★★★ | 🔵 Q3+ | 依赖操作系统级支持 |

---

## 三、实施路径

### 阶段 0：现状盘点（1 周）

**目标：** 摸清 OpenClaw 现有架构边界

**交付物：**
- `openclaw arch dump` → 架构图（节点/连接/数据流）
- 现有工具注册机制源码走读笔记
- 现有 exec/sessions 流程时序图
- 差距分析最终版（可能修正本方案细节）

**启动条件：** 主人确认方向后立即开始

---

### 阶段 1：上下文组装器 + Stage1 Memory（约 2-3 周）

#### 1.1 上下文分层流水线

**目标：** 将 OpenClaw 的文件堆叠升级为流水线融合

**实现思路：**
```
[base_context]        → openclaw 内置（系统提示/版本）
    ↓
[workspace_context]   → AGENTS.md + SOUL.md + USER.md（加权合并）
    ↓
[memory_context]      → MEMORY.md（精选片段 Relevance 召回）
    ↓
[skill_context]       → 相关 Skills（按需加载，非全量）
    ↓
[session_context]     → 本次 turn 的 user message + recent history
    ↓
[permission_context]  → 当前会话的权限级别
    ↓
[inject_context]      → 最终融合上下文 → Model
```

**关键改动点：**
- 新增 `ContextAssembler` 类，负责层层融合
- 支持层覆盖策略（later layer can override earlier）
- 上下文大小 budget（Token 预算），按优先级裁剪

#### 1.2 Stage1 Memory 自动化

**目标：** 告别手动维护 MEMORY.md

**实现思路：**
```
每日触发（或每 N 个 session）：
    1. 读取近 N 天的 daily logs
    2. 提取高价值片段（决策/约定/发现）
    3. 去重合并到 MEMORY.md
    4. 老旧 daily log 归档到 JSONL
```

**数据库升级（可选）：**
```
SQLite 表：
    threads(id, parent_id, status, created_at, label)
    memories(id, content, importance, last_accessed, tags)
    daily_logs(id, date, raw_text, processed)
```

**交付物：**
- `ContextAssembler` 原型（可配置开关）
- Stage1 Memory 自动化脚本
- 文档：如何在小麦中使用新上下文系统

---

### 阶段 2：权限引擎升级 + 双通道通信（约 3-4 周）

#### 2.1 权限引擎

**目标：** 从"开关式"升级为"策略引擎"

**三模式设计：**
```
🟢 FULL（放权模式）
    → 信任 workspace 内的所有操作
    → 仅拦截明确危险命令（如 rm -rf /）

🟡 AUDIT（审计模式）—— 小麦默认
    → 所有 exec 记录日志
    → 危险命令（含参数）强制评论确认
    → 可配置命令白名单（自动放行）

🔴 DENY（锁死模式）
    → 所有 exec 需要显式批准
    → 适用于陌生人/新 channel
```

**Escalation 机制：**
```
危险命令检测 → 暂停执行 → 通知主人 → 等待批复
    → 批准 → 解锁执行
    → 拒绝 → 记录并告知小麦
    → 超时 → 自动拒绝（安全默认值）
```

**命令白名单可配置示例：**
```yaml
# wheat_permissions.yaml
allowlist:
  - git add/commit/push/pull
  - npm install/start/test
  - openclaw *
  - cd ls cat read
  
audit:
  - exec (any)
  - rm mv del
  
block:
  - sudo su
  - chmod -R 777 /
  - drop database
```

#### 2.2 双通道通信

**目标：** 小麦专属，飞书天然适配

**实现：**
```
commentary channel（非最终答复，实时输出）：
    - 思考过程：分析→拆解→推理
    - 进度指示：[1/5] 完成需求分析
    - 插播提示：发现一个问题...
    
final channel（结构化交付）：
    - 方案文档（MD）
    - 代码块（完整可用）
    - 操作结果摘要
    - 下一步建议
```

**飞书适配：**
- commentary 用普通消息流式输出
- final 用独立消息 + emoji 标记（如 ✅ 执行完毕）
- 或者用 threading：commentary 在 thread 内，final 在主消息

**交付物：**
- 权限引擎配置系统
- 小麦专属 permission profile
- 双通道客户端支持（飞书 channel 适配）
- 小麦安全策略文档

---

### 阶段 3：任务队列系统（约 4-6 周）

**目标：** 让小麦从"单线执行"升级为"多任务协调者"

**架构设计：**
```
[JobQueue]
    ├── priority: critical / normal / low
    ├── dependencies: [job_id, ...]  （DAG 支持）
    ├── parent_job_id: string
    ├── status: pending / running / paused / done / failed
    └── metadata: created_by, created_at, deadline, tags
    
[AgentPool]
    ├── 多个子 agent 实例
    ├── 能力标签（coding / research / review / ...）
    └── 并发限制（max 3 concurrent）
```

**小麦的编排工作流：**
```
主人旨意
    ↓
小麦拆解为 Job 列表（子任务）
    ↓
JobQueue 接收，入队排序
    ↓
AgentPool 领取 Job（按能力匹配）
    ↓
子 Agent 执行 → 结果写回
    ↓
小麦汇总 → final deliver
```

**交付物：**
- JobQueue 核心实现（SQLite 持久化）
- AgentPool 管理器
- 小麦任务拆解模板（方案模板自动生成 Job）
- 多任务飞书通知集成

---

### 阶段 4：工具动态路由 + 沙箱隔离（约 6-8 周）

#### 4.1 工具动态路由

**目标：** 工具按需注入，Model 不知道有什么工具

**实现思路：**
```
传统（OpenClaw 现在）：
    System: "You have these tools: [tool list]..."
    
Harness 目标：
    运行时由 Harness 决定注入哪些工具
    Model 只知道"我有工具可用"，不知道具体是什么
    工具描述从 Skills JSON Schema 动态生成
```

**阶段路径：**
```
Step 1: 工具注册表（YAML/JSON）替代硬编码
Step 2: Skills → JSON Schema 生成器
Step 3: 按 session context 选择性注入（contextual tool selection）
Step 4: 工具版本管理 + 回退机制
```

#### 4.2 沙箱隔离

**目标：** workspace 之间相互隔离

**前提：** 需要 OS 级支持（Linux namespace / macOS sandbox）

**最小可行版本：**
```
workspace 目录级隔离：
    /workspace/default/      → 默认 workspace
    /workspace/trusted/      → 高信任任务（如主人明确授权）
    /workspace/sandbox/      → 陌生内容分析/代码执行
    
危险操作（如 wget/curl）只能在 sandbox 内执行
```

---

## 四、小麦专属增强

> 结合小麦"尚书省/总管"的身份定位

### 4.1 小麦的"三省六部"映射

```
主人（皇帝）
    ↓ 下旨
中书省（产品规划）→ 本文档
    ↓ 方案
门下省（审核）→ 方案审议
    ↓ 批准
尚书省（小麦/总管）→ 执行
    ↓ 调度
六部（子 Agent/工具）→ 各项专业执行
```

**Harness 能力在其中的角色：**
- **Context Assembler** → 小麦的"情报系统"：上情下达，下情上达
- **Permission Engine** → 小麦的"法度"：有令则行，有禁则止
- **Tool Router** → 小麦的"六部职能"：按需调用，各司其职
- **Persistence Layer** → 小麦的"档案库"：凡事留档，有据可查
- **Job Queue** → 小麦的"排期表"：事有先后，责有所归
- **双通道** → 小麦的"奏折系统"：先奏后斩，先说再做

### 4.2 小麦专属功能建议

#### ① 旨意解析器（Decree Parser）
```
主人消息 → 结构化意图 + 参数 + 约束 + 优先级
    → 自动生成方案草稿
    → 减少小麦理解偏差
```

#### ② 封驳机制（Veto Protocol）
```
小麦觉得方案有问题 → 拒绝执行 + 理由
    → 返回中书省重新规划
    → 循环直到双方达成共识
```

#### ③ 奏报系统（Report Generator）
```
执行完毕 → 自动生成奏报格式
    → 执行了什么
    → 结果如何
    → 遇到什么问题
    → 下一步建议
```

#### ④ 档案追溯（Audit Trail）
```
所有操作留档：
    谁（who）→ 何时（when）→ 做何事（what）→ 结果如何（result）
    主人可随时查询历史操作记录
```

### 4.3 小麦 vs Claude Code 的差异化定位

| 维度 | Claude Code | 小麦 |
|------|------------|------|
| **核心用户** | 开发者个人 | 主人（木白）私人总管 |
| **工作模式** | 单人 AI Pair 编程 | 多任务管家式服务 |
| **交互风格** | 开发者友好，technical | 自然语言，尚书风格 |
| **权限模型** | 通用沙箱 | 主人定制策略 |
| **记忆** | 偏代码/项目 | 主人全方位生活/工作 |
| **执行范围** | 代码/终端 | 全方位（文档/飞书/代码/日程/...）|

---

## 五、风险与约束

### 5.1 技术风险

| 风险 | 影响 | 缓解策略 |
|------|------|---------|
| 上下文融合引入延迟 | 响应速度下降 | 缓存层 + 异步预处理 |
| SQLite 迁移破坏现有数据 | 历史记忆丢失 | 双写过渡期 + 数据导出工具 |
| 权限过严影响效率 | 小麦变"瘫痪" | FULL 模式可切换，默认 AUDIT |
| 子 Agent 失控 | 安全风险 | 沙箱 + 权限引擎双重保障 |

### 5.2 迁移原则

1. **不破坏现有功能** — 所有改动通过 feature flag 控制，默认关闭
2. **可逆性** — 每阶段改动可回退到上一稳定版本
3. **增量交付** — 每阶段交付可用功能，不追求一步到位
4. **主人确认** — 每个阶段开始前需要主人确认方案细节

---

## 六、阶段交付物汇总

| 阶段 | 时间 | 核心交付物 | 主人感知 |
|------|------|-----------|---------|
| Phase 0 | 1 周 | 架构走读报告 | 无感（内部） |
| Phase 1 | 2-3 周 | ContextAssembler + Stage1 Memory | 小麦更"懂上下文"，记忆更准 |
| Phase 2 | 3-4 周 | 权限引擎 + 双通道 | 小麦更安全，汇报更清晰 |
| Phase 3 | 4-6 周 | JobQueue + AgentPool | 小麦能并行处理多任务 |
| Phase 4 | 6-8 周 | 动态工具路由 + 沙箱 | 小麦工具能力按需扩展 |

**总预计工期：4-5 个月（可并行部分并行推进）**

---

## 七、立即可启动事项

主人确认方向后，以下事项可立即开始：

1. **Phase 0 启动** — 源码走读，摸清架构边界
2. **Phase 1 细化** — 输出 ContextAssembler 具体设计方案
3. **小麦权限配置** — 基于现有 exec security，设计小麦专属权限 YAML

---

*本方案由中书省起草，待门下省审议后执行。*
*如有修改意见，请直接指出，中书省将重新修订后再次提交。*
