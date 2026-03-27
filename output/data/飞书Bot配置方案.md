# 飞书Bot配置方案 - 独立Agent入口

## 当前状态

已配置11个Agent：
- main: 小麦（总管）
- product: 中书省（产品经理）
- reviewer: 门下省（审核官）
- developer: 开发工程师
- tester: 测试工程师
- devops: 运维工程师
- copywriter: 文案
- video: 视频
- operator: 运营
- analyst: 数据分析师
- assistant: 助手

**问题**：当前只有一个飞书Bot，所有Agent共用入口，无法独立访问。

---

## 推荐方案：群组路由

使用单个飞书Bot + 多个群组，每个Agent对应一个群。

### 步骤

#### 1. 创建飞书群组

为每个Agent创建一个飞书群：

| Agent | 群名建议 |
|-------|----------|
| 中书省 | 【中书省】规划中心 |
| 门下省 | 【门下省】审核中心 |
| 开发工程师 | 【研发】开发组 |
| 测试工程师 | 【研发】测试组 |
| 运维工程师 | 【研发】运维组 |
| 文案 | 【运营】文案组 |
| 视频 | 【运营】视频组 |
| 运营 | 【运营】运营组 |
| 数据分析师 | 【职能】数据分析 |
| 助手 | 【职能】助手 |

#### 2. 添加Bot到群组

将当前的飞书Bot添加到每个群。

#### 3. 获取群组ID

在群里@Bot，然后查看日志：

```bash
openclaw logs --follow
```

找到 `chat_id`（格式：`oc_xxx`）。

#### 4. 配置bindings

编辑 `~/.openclaw/openclaw.json`，添加 `bindings` 配置：

```json5
{
  bindings: [
    // 小麦（DM直达）
    {
      agentId: "main",
      match: {
        channel: "feishu",
        peer: { kind: "direct", id: "ou_d369ff78bbec666bba90cabedd4181c7" },
      },
    },
    // 中书省（群组路由）
    {
      agentId: "product",
      match: {
        channel: "feishu",
        peer: { kind: "group", id: "oc_XXX" }, // 替换为实际群ID
      },
    },
    // 门下省
    {
      agentId: "reviewer",
      match: {
        channel: "feishu",
        peer: { kind: "group", id: "oc_XXX" }, // 替换为实际群ID
      },
    },
    // ... 为其他Agent添加类似配置
  ],
}
```

#### 5. 更新群组权限

添加新群到允许列表：

```json5
{
  channels: {
    feishu: {
      groupAllowFrom: [
        "ou_d369ff78bbec666bba90cabedd4181c7", // 保留原有
        "oc_xxx", // 中书省群
        "oc_xxx", // 门下省群
        // ... 添加其他群ID
      ],
    },
  },
}
```

#### 6. 重启Gateway

```bash
openclaw gateway restart
```

---

## 完整配置示例

```json5
{
  channels: {
    feishu: {
      enabled: true,
      appId: "cli_a9f0113d4a395bd7",
      appSecret: "LpffmNaQPc1GObsYwnXWsfp0SsmylF1M",
      connectionMode: "websocket",
      domain: "feishu",
      groupPolicy: "allowlist",
      allowFrom: [
        "ou_d369ff78bbec666bba90cabedd4181c7"
      ],
      groupAllowFrom: [
        "ou_d369ff78bbec666bba90cabedd4181c7",
        // 在这里添加所有Agent群ID
        "oc_xxx", // 中书省
        "oc_xxx", // 门下省
        "oc_xxx", // 开发
        // ...
      ],
    },
  },
  
  bindings: [
    {
      agentId: "main",
      match: {
        channel: "feishu",
        peer: { kind: "direct", id: "ou_d369ff78bbec666bba90cabedd4181c7" },
      },
    },
    {
      agentId: "product",
      match: {
        channel: "feishu",
        peer: { kind: "group", id: "oc_XXX" },
      },
    },
    // ... 其他Agent
  ],
}
```

---

## 主人需要做的

1. **创建群组**：为需要的Agent创建飞书群
2. **添加Bot**：把Bot拉进每个群
3. **获取ID**：在群里@Bot，运行 `openclaw logs --follow` 获取群ID
4. **告诉我群ID**：我会更新配置

---

## 备选方案：多Bot

如果主人希望每个Agent有完全独立的Bot身份（不同头像、名字），可以：

1. 为每个Agent创建独立飞书应用
2. 配置多个Feishu账号
3. 每个Agent有自己的App ID和App Secret

**优点**：完全独立
**缺点**：管理复杂，需创建多个应用

---

_推荐先用群组路由方案，简单实用。_
