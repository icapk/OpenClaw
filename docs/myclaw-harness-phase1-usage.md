# MyClaw Harness Phase 1 — Usage Guide

> For 小麦（MyClaw）团队  
> Phase 1 交付物说明文档

---

## Overview

Phase 1 实现了两大核心能力：

| 组件 | 位置 | 功能 |
|------|------|------|
| **ContextAssembler** | `~/MyClaw/src/context/context-assembler.ts` | 7层上下文流水线，可配置开关 |
| **Stage1 Memory** | `~/MyClaw/src/memory/stage1-memory-automation.ts` | 每日日志自动提取合并 |

---

## 1. ContextAssembler（上下文组装器）

### 1.1 什么是 ContextAssembler？

将 OpenClaw 的文件堆叠升级为**流水线融合**：

```
[base_context]        → OpenClaw 内置（系统提示/版本）
    ↓
[workspace_context]   → AGENTS.md + SOUL.md + USER.md + IDENTITY.md + TOOLS.md
    ↓
[memory_context]      → MEMORY.md（精选片段 Relevance 召回）
    ↓
[skill_context]       → 相关 Skills（按需加载，非全量）
    ↓
[session_context]      → 本次 turn 的 user message + recent history
    ↓
[permission_context]   → 当前会话的权限级别（FULL/AUDIT/DENY）
    ↓
[inject_context]       → 最终融合上下文 → Model
```

### 1.2 开启/关闭

**默认关闭**（保留现有行为）。

**方式一：环境变量**
```bash
export MYCLAW_CONTEXT_ASSEMBLER_ENABLED=true
```

**方式二：代码**
```typescript
import { ContextAssembler } from './context/context-assembler';

const assembler = new ContextAssembler({ enabled: true });
```

**方式三：在 MyClawCore 中使用**
```typescript
// MyClawCore 会自动读取 MYCLAW_CONTEXT_ASSEMBLER_ENABLED 环境变量
export MYCLAW_CONTEXT_ASSEMBLER_ENABLED=true
```

### 1.3 配置参数

```typescript
const assembler = new ContextAssembler({
  enabled: false,           // 默认关闭
  tokenBudget: 8000,         // Token 预算上限
  charsPerToken: 4,          // 每 token 字符数估算
  layers: {
    base:      { enabled: true,  priority: 100, canOverride: false },
    workspace: { enabled: true,  priority: 90,  canOverride: true  },
    memory:    { enabled: true,  priority: 80,  canOverride: true  },
    skill:     { enabled: true,  priority: 70,  canOverride: true  },
    session:   { enabled: true,  priority: 60,  canOverride: true  },
    permission:{ enabled: true,  priority: 50,  canOverride: true  },
    inject:    { enabled: true,  priority: 40,  canOverride: true  },
  },
});
```

| 参数 | 说明 |
|------|------|
| `enabled` | 是否启用（默认 false） |
| `tokenBudget` | 上下文总 token 上限 |
| `priority` | 层优先级（越高越重要，budget 不足时优先裁剪低优先级） |
| `canOverride` | 该层是否可以覆盖之前层的内容 |

### 1.4 Token 预算裁剪

当总上下文超过 `tokenBudget` 时，按优先级从低到高裁剪：

1. `permission` 层先被裁剪
2. 然后 `session` 历史
3. 然后 `skill` 内容
4. 然后 `memory` 内容
5. `workspace` 和 `base` 通常不会被裁剪（高优先级）

### 1.5 集成到 MyClawCore

```typescript
import { MyClawCore } from './index';

const core = new MyClawCore({
  workspaceDir: '~/.openclaw/workspace',
  sessionKey: 'session:2026-04-06',
});

// 当 MYCLAW_CONTEXT_ASSEMBLER_ENABLED=true 时自动使用 7 层流水线
// 否则回退到旧的 L0-L3 assembler
const prompt = await core.assembleContext({
  baseInstructions: 'You are 小麦.',
  currentInput: '帮我分析今天的运营数据',
  availableTools: ['read', 'exec', 'web_search'],
  injectMemory: true,
});
```

### 1.6 API

```typescript
// 检查是否启用
assembler.isEnabled(); // → boolean

// 启用
assembler.enable();

// 禁用（回退到旧行为）
assembler.disable();

// 获取配置
assembler.getConfig(); // → AssemblerConfig

// 更新配置
assembler.updateConfig({ tokenBudget: 12000 });

// 组装上下文
const ctx = await assembler.assemble({
  workspaceDir: '~/.openclaw/workspace',
  sessionKey: 'session:xxx',
  baseInstructions: '...',
  injectedMemory: ['memory content'],
  currentInput: '...',
  availableTools: ['read', 'exec'],
  activeSkills: ['coding-agent', 'github'],
  skillContents: new Map([['coding-agent', '...']]),
  sessionHistory: messages,
  permissionLevel: 'AUDIT',
  allowedCommands: ['git', 'npm'],
  blockedCommands: ['rm -rf /', 'dd'],
});

// 从组装结果构建 system prompt
const prompt = assembler.buildSystemPrompt(ctx);
```

---

## 2. Stage1 Memory 自动化

### 2.1 原理

告别手动维护 MEMORY.md！

```
每日触发（或每 N 个 session）：
    1. 读取近 N 天的 daily logs（memory/YYYY-MM-DD.md）
    2. 提取高价值片段（决策/约定/发现）
    3. 去重合并到 MEMORY.md
    4. 老旧 daily log 归档到 JSONL
    5. 删除源文件（节省空间）
```

### 2.2 提取规则

| 类型 | 质量 | 模式示例 |
|------|------|---------|
| **决策** | 高 | "decided to", "chose to", "agreed to", "结论" |
| **事实** | 高 | "the goal is", "we are working on", "key point" |
| **偏好** | 高 | "i prefer", "my habit is", "i always" |
| **任务** | 中 | "TODO:", "need to", "next step", "pending" |

### 2.3 每日自动运行

**Crontab 设置**
```bash
crontab -e
# 添加这一行：每天早上6点运行
0 6 * * * /Users/a1/.openclaw/scripts/daily-memory-consolidation.sh >> /Users/a1/.openclaw/logs/memory-consolidation.log 2>&1
```

**手动运行**
```bash
# 完整运行
~/.openclaw/scripts/daily-memory-consolidation.sh --days 7 --verbose

# 预览（不修改任何文件）
~/.openclaw/scripts/daily-memory-consolidation.sh --dry-run --days 7 --verbose

# 只看3天
~/.openclaw/scripts/daily-memory-consolidation.sh --days 3
```

### 2.4 日志位置

- 运行日志：`~/.openclaw/logs/memory-consolidation.log`
- 归档 JSONL：`~/.openclaw/workspace/memory/archive/YYYY-MM-DD.jsonl`

### 2.5 可逆性

所有被处理的 daily log 都先归档再删除。要恢复：
```bash
# 从 JSONL 读取并写回 markdown
cat ~/.openclaw/workspace/memory/archive/2026-04-02.jsonl | jq -r '.content' > ~/.openclaw/workspace/memory/2026-04-02.md
```

### 2.6 API 使用

```typescript
import { runConsolidation } from './memory/stage1-memory-automation';

const result = await runConsolidation({
  workspaceDir: '~/.openclaw/workspace',
  lookbackDays: 7,
  minQuality: 0.4,       // 0-1，默认 0.4
  archive: true,          // 归档到 JSONL
  dryRun: false,          // 预览模式
  verbose: true,
});

console.log(`处理 ${result.processed} 个日志文件`);
console.log(`合并 ${result.merged} 个片段`);
console.log(`去重跳过 ${result.skipped} 个`);
console.log(`归档 ${result.archived} 个日志`);
if (result.errors.length > 0) {
  console.error('错误:', result.errors);
}
```

---

## 3. 在小麦中使用

### 3.1 完整示例

```typescript
import MyClawCore, { ContextAssembler } from './index';

// 创建核心实例
const core = new MyClawCore({
  workspaceDir: '~/.openclaw/workspace',
  sessionKey: 'wheat:2026-04-06:morning',
  commentaryChannel: 'feishu',
  feishuChatId: 'oc_xxxxx',
});

// 获取带上下文的 system prompt
const prompt = await core.assembleContext({
  baseInstructions: `你是小麦，Michael 的专属总管。`,
  currentInput: userMessage,
  availableTools: ['read', 'write', 'exec', 'web_search'],
  injectMemory: true,  // 自动注入相关记忆
});

console.log(prompt); // → 7层融合后的完整上下文
```

### 3.2 调试模式

```bash
# 查看 ContextAssembler 是否启用
export MYCLAW_CONTEXT_ASSEMBLER_ENABLED=true
node -e "
const { ContextAssembler } = require('./dist/context/context-assembler');
const a = new ContextAssembler();
console.log('Enabled:', a.isEnabled());
console.log('Config:', JSON.stringify(a.getConfig(), null, 2));
"
```

---

## 4. 测试

```bash
cd ~/MyClaw

# 测试 ContextAssembler
npm test -- --testPathPattern=context-assembler

# 测试 Stage1 Memory
npm test -- --testPathPattern=stage1-memory-automation

# 端到端测试（dry-run）
node dist/memory/stage1-memory-automation.js \
  --workspace ~/.openclaw/workspace \
  --days 7 \
  --dry-run \
  --verbose
```

---

## 5. 架构总览

```
小麦（MyClawCore）
    ↓
ContextAssembler（7层流水线）
    ├── L0: base_context      ← OpenClaw 内置
    ├── L1: workspace_context ← AGENTS.md / SOUL.md / USER.md
    ├── L2: memory_context    ← MEMORY.md（自动召回）
    ├── L3: skill_context     ← 当前技能内容
    ├── L4: session_context   ← 最近对话历史
    ├── L5: permission_context← 权限级别
    └── L6: inject_context    ← 最终 prompt → Model

Stage1 Memory 自动化
    ├── 读取 memory/YYYY-MM-DD.md
    ├── 提取决策/事实/任务片段
    ├── 去重（against MEMORY.md）
    ├── 合并到 MEMORY.md
    └── 归档到 JSONL + 删除源文件
```

---

## 6. 常见问题

**Q: ContextAssembler 默认关闭，如何开启？**
A: 设置环境变量 `MYCLAW_CONTEXT_ASSEMBLER_ENABLED=true`，或在代码中 `new ContextAssembler({ enabled: true })`。

**Q: 开启后会影响现有功能吗？**
A: 不会。ContextAssembler 是可插拔的，默认使用旧的 L0-L3 assembler。只有明确开启后才使用新的 7 层流水线。

**Q: daily log 归档后还能恢复吗？**
A: 能。所有 daily log 先归档到 `memory/archive/YYYY-MM-DD.jsonl`，然后才删除源文件。可以用 `jq` 从 JSONL 恢复。

**Q: Token 预算不足时哪些内容会被裁剪？**
A: 按优先级从低到高裁剪：permission → session → skill → memory → workspace → base。base 层永不裁剪。

---

_Phase 1 交付物 · 2026-04-06_
