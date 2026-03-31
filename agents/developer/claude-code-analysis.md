# Claude Code 架构分析报告

## 1. 源码发现

**Claude Code（OpenAI Codex CLI）** 安装位置：
- 主程序：`/opt/homebrew/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/codex/codex`
- 本地配置：`~/.codex/`
- 版本：0.117.0

**源码泄露事件**（2026年3月31日）：Anthropic 的 Claude Code 通过 npm source map 文件意外暴露了完整源码——1,900 个 TypeScript 文件，超 512,000 行代码。泄露内容包括 LLM API 调用引擎、流式响应处理、工具调用循环、思考模式、重试逻辑、Token 计数、权限模型等核心组件。

---

## 2. Agent 架构

### 2.1 核心设计理念

Claude Code 采用 **Agentic Loop（自主代理循环）** 架构，核心由两部分组成：

1. **Model（模型）** — 负责推理和决策
2. **Tools（工具）** — 负责在真实环境中执行操作

Claude Code 本质上是一个 **Agentic Harness（代理控制框架）**，它将语言模型转化为具备编程能力的智能体：

- 提供工具（Tools）
- 管理上下文（Context Management）
- 提供执行环境（Execution Environment）

### 2.2 Agent 循环机制

```
用户请求 → 模型推理 → 工具调用 → 执行结果 → 反馈给模型 → 继续推理 → ...
```

- **持久性（Persistence）**：持续工作直到任务完整解决，不在分析或部分修复时停止
- **自主性（Autonomy）**：除非用户明确要求暂停，否则自动推进
- **响应式（Responsiveness）**：定期向用户发送中间进度更新（约20-30秒一次）

### 2.3 双通道通信

Claude Code 通过两个通道与用户交互：

| 通道 | 用途 |
|------|------|
| `commentary` | 中间进度更新，持续向用户报告工作进展 |
| `final` | 最终答案，任务完成后的完整交付 |

---

## 3. 工具调用系统

### 3.1 工具类型

Claude Code 支持多种工具，形成完整的开发能力矩阵：

| 工具 | 功能 |
|------|------|
| `apply_patch` | 文件编辑（freeform patch 格式） |
| Shell | 执行终端命令（`rg` 优先于 `grep`） |
| Web Search | 网页搜索（支持 text 和 text_and_image） |
| `update_plan` | 任务计划管理与进度追踪 |
| Read | 文件读取 |
| Write | 文件创建 |

### 3.2 并行工具调用

- **多工具并行**（`multi_tool_use.parallel`）：支持同时发起多个独立的工具调用
- 特别适用于并行文件读取、搜索、shell 命令等
- 避免使用 `echo "====";` 这样的命令连接方式（影响用户体验）

### 3.3 思考模式

- 支持 **Reasoning Summaries**（推理摘要）
- 可配置的 verbosity 级别（`low`, `medium`, `high`, `xhigh`）
- 模型支持多种思考深度等级，适用于不同复杂度任务

### 3.4 Task Tool（任务工具）

Claude Code 最强大的特性之一 — **子 Agent 编排系统**：

- 能生成专门的"同事"——自主子代理
- 子代理可独立工作，同时主代理继续其他任务
- 实现复杂多步操作的并行处理

---

## 4. 上下文管理体系

### 4.1 上下文构成

在每次 LLM 调用前，Claude Code 从多个来源组装上下文：

```
系统提示 (System Prompt)
    ↓
git 状态和仓库元数据
    ↓
CLAUDE.md 文件（项目指令）
    ↓
用户设置 (User Settings)
    ↓
记忆文件 (Memory Files)
    ↓
MCP 资源 (Model Context Protocol)
    ↓
模型消息 (Model Messages)
```

### 4.2 上下文窗口

- **总窗口**：272,000 tokens
- **有效利用率**：95%（即 ~258,400 tokens 可用）
- **截断策略**：10,000 tokens 截断限制（mode: tokens）
- 支持文本和图像输入（`text`, `image`）

### 4.3 AGENTS.md 规范

仓库中的 `AGENTS.md` 文件是指引 AI 工作的配置文件：

- 作用域为文件所在目录的整个目录树
- 每当修改文件时，必须遵守该文件作用域内任何 `AGENTS.md` 的指令
- 更深嵌套的 `AGENTS.md` 在冲突时优先
- 根目录的 AGENTS.md 包含在 developer message 中，无需重新读取

---

## 5. 代码生成策略

### 5.1 补丁式编辑

使用 `apply_patch` 工具的 freeform 格式：

```
*** Begin Patch
*** Update File: path/to/file.py
@@ def example():
-old code
+new code
*** End Patch
```

### 5.2 编辑约束

- 默认使用 ASCII，仅在有明确理由时引入非 ASCII
- 避免无意义的注释（"将值赋给变量"这类）
- 不使用 Python 读写文件，优先用 shell 命令或 `apply_patch`
- 禁止使用破坏性命令（`git reset --hard` 等）
- 代码审查优先发现 bug、风险、行为回归和缺失测试

### 5.3 前端开发策略

- 避免"AI slop"——安全、平均的布局
- 字体：使用有表现力的字体，避免系统默认栈
- 颜色：避免紫色偏见和暗色模式偏见
- 动画：少量有意义的动画（页面加载、交错显示）
- 背景：使用渐变、形状或微妙图案，不依赖纯色
- React：偏好现代模式（useEffectEvent, startTransition, useDeferredValue）

---

## 6. 支持的模型

Claude Code 是一个多模型平台，支持多种 GPT-5 系列模型：

| 模型 | 类型 | Context | 并行工具调用 |
|------|------|---------|-------------|
| GPT-5.4 | 通用 | 272K | ✓ |
| GPT-5.3-Codex | Codex优化代理编码 | 272K | ✓ |
| GPT-5.2-Codex | 前沿代理编码 | 272K | ✓ |
| GPT-5.1-Codex-Max | Codex深度推理 | 272K | ✗ |
| GPT-5.1-Codex | Codex优化 | 272K | ✗ |
| GPT-5.1 | 通用+长时代理 | 272K | ✓ |
| GPT-5-Codex | Codex优化 | 272K | ✗ |
| GPT-5 | 通用 | 272K | ✗ |
| GPT-5.1-Codex-mini | 轻量级 | 272K | ✗ |
| GPT-5-Codex-mini | 轻量级 | 272K | ✗ |

**默认模型优先级**：GPT-5.4（最新）→ GPT-5.3-Codex（主力）

---

## 7. 技术亮点与优势

### 7.1 为什么 Claude Code 是"最厉害的 AI"？

#### ① 端到端自主能力
- 不只生成代码，而是**持续执行直到任务完成**
- 从需求到验证的完整闭环，无需人工干预

#### ② 超长上下文 + 95% 有效利用率
- 272K context window，95% 有效利用（业界最高水平之一）
- 能够深入理解整个代码库，而非单文件

#### ③ 多模型灵活切换
- 支持从 GPT-5.4 到 GPT-5-Codex-mini 的完整模型谱系
- 根据任务复杂度选择最优模型（成本与能力的平衡）

#### ④ 子 Agent 并行编排
- Task Tool 让复杂任务可以分解给多个专业子代理
- 主代理保持响应用户，子代理独立工作

#### ⑤ 专为开发者设计的工具链
- `rg` 优先搜索、freeform patch 编辑、shell 命令执行
- 深度集成 git 工作流和代码审查

#### ⑥ 双通道透明沟通
- commentary 持续更新进度，不让用户等待时焦虑
- final 提供结构化、可追溯的交付

#### ⑦ 记忆与上下文持久化
- `~/.codex/memory/` 中的长期记忆
- `CLAUDE.md` 项目级上下文
- MCP 资源扩展

#### ⑧ 开箱即用的 Skills 系统
- 系统技能（.system/）、供应商导入技能、用户安装技能
- 可扩展的技能生态

#### ⑨ 前端设计智能化
- 不是生成"安全平庸"的 UI，而是有意图的、令人惊喜的设计
- 避免 AI slop，强调视觉方向、字体选择、动画质量

#### ⑩ 精细化任务管理
- `update_plan` 工具追踪步骤和进度
- exactly one `in_progress` 状态的管理规范

---

## 8. 安全与权限模型

Claude Code 内置多层安全机制：

- **Approval Modes**：never / on-failure / untrusted / on-request
- 非交互模式（never/on-failure）下可主动运行测试和 lint
- 交互模式（untrusted/on-request）下等待用户确认后再执行
- **禁止破坏性操作**：除非明确请求，否则不执行 `git reset --hard`
- Dirty git 工作树处理：识别非自身变更，不随意 revert

---

## 9. 总结

Claude Code 的强大之处不在于某个单一特性，而在于**一整套精心设计的工程系统**：

1. **Agent 架构**：Model + Tools 的自主循环，持续到任务完成
2. **工具生态**：文件操作、shell 命令、Web 搜索、子 Agent 编排的完整工具箱
3. **上下文管理**：272K tokens 窗口 + 多层上下文注入 + 记忆持久化
4. **用户体验**：commentary/final 双通道、进度追踪、AGENTS.md 规范
5. **多模型支持**：GPT-5 完整谱系，按需选择
6. **Skills 扩展**：系统级和用户级技能扩展机制

Claude Code 不是在"回答问题"，而是在"帮你完成工作"——这才是它被称为"最厉害 AI"的根本原因。
