# 任务卡 - MyClaw Harness 迁移 Phase 1

## 基本信息
- **任务ID**: TASK-2026-04-04-HARNESS-PHASE1
- **创建时间**: 2026-04-04 09:29 GMT+8
- **发起人**: 主人（木白）
- **执行部门**: 研发部

## 任务目标
启动 MyClaw Harness 迁移方案 Phase 1：上下文组装器 + Stage1 Memory 自动化

## 详细需求

### Phase 1.1 上下文分层流水线
将 OpenClaw 的文件堆叠升级为流水线融合：

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

关键改动点：
- 新增 `ContextAssembler` 类，负责层层融合
- 支持层覆盖策略（later layer can override earlier）
- 上下文大小 budget（Token 预算），按优先级裁剪

### Phase 1.2 Stage1 Memory 自动化
告别手动维护 MEMORY.md：

```
每日触发（或每 N 个 session）：
    1. 读取近 N 天的 daily logs
    2. 提取高价值片段（决策/约定/发现）
    3. 去重合并到 MEMORY.md
    4. 老旧 daily log 归档到 JSONL
```

数据库升级（可选）：
```
SQLite 表：
    threads(id, parent_id, status, created_at, label)
    memories(id, content, importance, last_accessed, tags)
    daily_logs(id, date, raw_text, processed)
```

## 交付物
- `ContextAssembler` 原型（可配置开关）
- Stage1 Memory 自动化脚本
- 文档：如何在小麦中使用新上下文系统

## 参考文档
- `~/MyClaw/src/` - 现有 MyClaw 代码
- `workspace/plans/draft/harness_migration_for_wheat.md` - 完整迁移方案

## 完成标准
1. ContextAssembler 可配置开关，默认关闭
2. Stage1 Memory 可每日自动运行
3. 不破坏现有功能
4. 可逆性：每阶段改动可回退

## 优先级: P0
## 截止时间: 待定
