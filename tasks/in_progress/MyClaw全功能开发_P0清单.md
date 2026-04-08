# MyClaw 全功能开发任务清单

> 创建时间：2026-04-07 17:29
> 负责人：开发 Agent
> 依据：主人命令「先把 myclaw 项目里面没有完成的功能全部开发完」

---

## P0 - 核心 Harness（必须完成）

- [ ] Harness 真正接入 Electron main 进程
- [ ] autonomous-runner 自主循环
- [ ] QueueController 任务队列
- [ ] Commentary 实时推送

## P0 - 并行 Agent

- [ ] 多 Agent 同时工作
- [ ] Task Tool 子任务分发

## P0 - 代码审查修复

- [ ] 修复 createHarnessIpcBridge
- [ ] 添加并行 agent 支持
- [ ] 改进 memory recall

## P1 - 记忆系统

- [ ] 记忆系统 V2 集成
- [ ] Session 开始召回
- [ ] Session 结束保存

## P1 - 代码优化

- [ ] 提取重复的 isTaskComplete
- [ ] 改进错误处理
- [ ] 添加类型定义

## P2 - PM Skills

- [ ] PRD 评审
- [ ] 需求分析
- [ ] 优先级排序
- [ ] 会议纪要

## P2 - 三省六部工作流

- [ ] 中书省/门下省/尚书省
- [ ] 工作流调度

## P2 - 飞书集成

- [ ] Webhook 接收
- [ ] 消息推送
- [ ] Commentary 推送

---

## 执行要求

1. 按 P0 → P1 → P2 顺序开发
2. 每个功能完成后更新本文件状态
3. 完成后汇总结果交给小麦审核
