# TrendRadar 热点监控工具 — 部署与运营落地方案

> 整理自《写公众号没灵感？这个 50K Star 开源工具把热点主动推到我面前》
> 工具地址：https://github.com/sansan0/TrendRadar
> 更新时间：2026-04-03

---

## 一、工具核心能力

| 能力 | 说明 |
|------|------|
| **平台覆盖** | 知乎、抖音、B站、微博、今日头条、百度热搜、微信搜一搜、36氪、少数派、IT之家等 11+ 平台 |
| **关键词过滤** | 支持多组关键词，支持 AND/OR 逻辑 |
| **AI 筛选 & 翻译** | 可调用 LLM 对内容打分，过滤低价值噪音，支持翻译 |
| **AI 简报** | 自动生成热点分析简报 |
| **RSS 订阅** | 支持自定义 RSS 源接入 |
| **推送渠道** | 飞书、企业微信、钉钉、Telegram、邮件、ntfy、 Barker（iOS）等 |
| **部署方式** | Docker / Docker Compose，30 秒完成部署 |
| **License** | GPL-3.0，开源免费 |

---

## 二、部署方案

### 方案 A：本地 Mac/Windows Docker 部署（推荐运营快速验证）

**适用场景：** 先在本地跑通，后续再迁移到服务器。

**前置条件：**
- 安装 Docker Desktop（Mac: `brew install --cask docker`）
- 飞书群机器人 Webhook URL（见第三章）

**步骤：**

```bash
# 1. 创建一个工作目录
mkdir -p ~/trendradar && cd ~/trendradar

# 2. 创建 docker-compose.yml
cat > docker-compose.yml << 'EOF'
services:
  trendradar:
    image: wantcat/trendradar:latest
    container_name: trendradar
    restart: unless-stopped
    ports:
      - "8000:8000"   # Web UI
    volumes:
      - ./data:/app/data
      - ./config.yaml:/app/config.yaml:ro
    environment:
      - TZ=Asia/Shanghai
EOF

# 3. 创建配置文件（见第四章模板）
cat > config.yaml << 'EOF'
# 完整配置模板见第四章
EOF

# 4. 启动
docker compose up -d

# 5. 访问 Web UI
open http://localhost:8000
```

---

### 方案 B：云服务器 Docker Compose 部署（推荐生产使用）

**适用场景：** 24 小时运行，稳定推送，适合正式运营。

**服务器要求：**
- CPU: 1核+
- 内存: 1GB+
- 系统: Ubuntu 22.04 / Debian 12
- 有公网 IP 或配置内网穿透

**服务器部署步骤：**

```bash
# 1. 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker

# 2. 创建目录
sudo mkdir -p /opt/trendradar && cd /opt/trendradar
sudo chown -R $(id -u):$(id -g) /opt/trendradar

# 3. 编写 docker-compose.yml
cat > docker-compose.yml << 'EOF'
services:
  trendradar:
    image: wantcat/trendradar:latest
    container_name: trendradar
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./config.yaml:/app/config.yaml:ro
    environment:
      - TZ=Asia/Shanghai
    # 可选：定时任务方式（不用内置调度）
    # cron: "0 8,12,18 * * *"  # 每天 8/12/18 点推送
EOF

# 4. 写入 config.yaml（见第四章）

# 5. 启动
docker compose up -d

# 6. 查看日志确认正常运行
docker logs -f trendradar
```

**配置定时抓取（推荐）：**
TrendRadar 支持两种调度模式：
1. **内置定时调度**：在 `config.yaml` 中配置 `schedule` 字段
2. **外部 cron 触发**：通过服务器 cron 调用 API 触发抓取

建议使用外部 cron，灵活控制时间：
```bash
# crontab -e
0 8,12,18 * * * curl -s http://localhost:8000/api/trigger > /tmp/trendradar.log 2>&1
```

---

## 三、飞书推送配置

### 3.1 创建飞书群机器人

1. 打开飞书群 → 群设置 → 群机器人 → 添加机器人
2. 选择「自定义机器人」→ 设置机器人名称（如"热点雷达"）
3. 复制 Webhook URL，格式：`https://open.feishu.cn/open-apis/bot/v2/hook/xxx`

### 3.2 config.yaml 飞书配置模板

```yaml
notify:
  enabled: true
  channels:
    - type: feishu
      webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_ID"
      # 可选：是否开启 AI 总结
      ai_summary: true
      # 可选：消息最大条数（控制推送量）
      max_items: 10
```

### 3.3 飞书消息卡片效果

TrendRadar 推送的飞书消息为卡片格式，包含：
- 热点标题
- 平台来源标签（抖音/知乎/B站等）
- 摘要/AI分析
- 点击跳转链接

---

## 四、关键词配置（AI/Agent/内容创作方向）

### 4.1 推荐关键词库

根据运营需求（AI、Agent、内容创作），建议配置以下关键词分组：

```yaml
keywords:
  # 核心关键词（必须监控）
  core:
    - AI
    - 人工智能
    - 大模型
    - LLM
    - ChatGPT
    - GPT
    - Claude
    - DeepSeek
    - Agent
    - Agentic AI
    - RAG
    - AIGC
    - 生成式AI

  # 内容创作相关
  content:
    - 公众号
    - 小红书运营
    - 内容创作
    - 爆款
    - 10万+
    - 选题
    - 写作技巧
    - 新媒体

  # 工具与产品
  tools:
    - Cursor
    - Claude Code
    - OpenClaw
    - Coze
    - Dify
    - LangFlow
    - n8n
    - Zapier
    - NotebookLM

  # 行业动态
  industry:
    - OpenAI
    - Anthropic
    - Google AI
    - 字节跳动
    - 百度AI
    - 阿里云
    - 腾讯AI
    - 英伟达
    - 黄仁勋
    -奥特曼

  # 排除词（减少噪音）
  exclude:
    - 股票推荐
    - 投资理财
    - 医疗美容广告
```

### 4.2 关键词配置格式

```yaml
# config.yaml 中的 keywords 部分
keywords:
  # 包含任一关键词即命中（OR 逻辑）
  include:
    - AI
    - 人工智能
    - 大模型
    - Agent
    - AIGC
    - ChatGPT
    - GPT
    - Claude
    - DeepSeek
    - 公众号运营
    - 小红书运营
    - 内容创作
    - Cursor
    - OpenClaw
    - 新媒体运营
    - 爆款文章
  # 排除词（命中 include 但同时命中 exclude 则过滤）
  exclude:
    - 股票
    - 投资
    - 美容广告
    - 游戏广告
```

---

## 五、完整 config.yaml 模板

```yaml
# TrendRadar 完整配置模板
# 路径: /opt/trendradar/config.yaml

app:
  # Web UI 端口
  port: 8000
  # 语言
  language: zh

# 数据源配置（全部启用）
sources:
  zhihu: true
  douyin: true
  bilibili: true
  weibo: true
  toutiao: true
  baidu: true
  weixin: true       # 微信搜一搜
  kekr: true         # 36氪
  sspai: true        # 少数派
  ithome: true       # IT之家
  rss: true          # RSS 订阅（需额外配置）

# 关键词过滤
keywords:
  include:
    - AI
    - 人工智能
    - 大模型
    - LLM
    - Agent
    - AIGC
    - ChatGPT
    - GPT
    - Claude
    - DeepSeek
    - 公众号运营
    - 小红书运营
    - 内容创作
    - 新媒体
    - Cursor
    - OpenClaw
    - 爆款
  exclude:
    - 股票推荐
    - 投资理财
    - 美容广告

# RSS 订阅源（可选）
rss_sources:
  - https://www.aisharenet.com/feed/    # AI 科技
  - https://36kr.com/feed                # 36氪

# AI 筛选配置
ai:
  enabled: true
  # 支持 OpenAI / Claude / DeepSeek 等
  provider: deepseek
  api_key: "YOUR_API_KEY"
  model: "deepseek-chat"
  # AI 筛选阈值（0-100）
  score_threshold: 60
  # 是否翻译外文
  translate: true
  # 是否生成摘要
  summary: true

# 推送配置
notify:
  enabled: true
  channels:
    - type: feishu
      webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_ID"
      ai_summary: true
      max_items: 8       # 每次推送最多 8 条
      mention_all: false # 是否 @所有人

# 调度配置
schedule:
  # cron 表达式（每天 8点、12点、18点推送）
  cron: "0 8,12,18 * * *"
  # 间隔模式（每 4 小时一次）
  interval_hours: 4
```

---

## 六、运营流程设计

### 6.1 每日运营时间表

| 时间 | 动作 | 说明 |
|------|------|------|
| 08:00 | 推送早报 | 筛选昨夜今晨热点，为当天选题热身 |
| 12:00 | 推送午报 | 午间快速浏览，抓取上午爆款线索 |
| 18:00 | 推送晚报 | 整理全天热点，可用于晚间创作 |
| 随时 | 手动触发 | 发现突发热点时，随时手动触发抓取 |

### 6.2 内容创作工作流

```
TrendRadar 推送热点
    ↓
运营人员筛选有价值热点
    ↓
进入内容选题会
    ↓
确定当日创作方向
    ↓
文案/视频制作
    ↓
发布至公众号/小红书
    ↓
收集数据反馈
```

### 6.3 飞书推送消息处理SOP

1. **收到推送** → 飞书群收到 TrendRadar 卡片消息
2. **快速浏览** → 扫视标题+摘要，判断有无创作灵感
3. **标记热点** → 有价值的热点，复制到 Notion/飞书文档暂存
4. **二次搜索** → 用关键词去微博/知乎进一步搜索，扩展素材
5. **进入创作** → 开启文案 Agent，进行爆款写作

### 6.4 关键词迭代优化

- **每周复盘**：在飞书文档记录本周哪些关键词命中率高
- **每月调整**：根据阅读量数据，调整关键词权重
- **热点盲区**：如果某次爆款没有被捕获，补充新关键词

---

## 七、进阶配置

### 7.1 AI 简报生成

```yaml
ai:
  enabled: true
  provider: deepseek
  api_key: "YOUR_DEEPSEEK_API_KEY"
  model: "deepseek-chat"
  prompt_template: |
    你是一个资深新媒体编辑。请对以下热点进行简短点评，
    指出哪些适合做公众号/小红书选题，为什么。
    输出格式：热点标题 + 点评（100字内）+ 适合平台。
```

### 7.2 RSS 补充源

除自有平台外，可接入优质 RSS 补充 AI 方向内容：

```yaml
rss_sources:
  - https://www.aisharenet.com/feed/
  - https://36kr.com/feed
  - https://feeds.feedburner.com/36kr
  - https://www.producthunt.com/feed
  - https://hnrss.org/frontpage
```

### 7.3 多账号/多频道推送

如需同时推送到多个飞书群：

```yaml
notify:
  channels:
    - type: feishu
      name: "运营组"
      webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/HOOK_ID_1"
      keywords_include: ["AI", "Agent", "大模型"]
    - type: feishu
      name: "技术组"
      webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/HOOK_ID_2"
      keywords_include: ["开源", "GitHub", "代码", "编程"]
```

---

## 八、常见问题

| 问题 | 解决方案 |
|------|----------|
| 推送消息太多 | 调低 `max_items`，提高 `score_threshold` |
| 飞书收不到消息 | 检查 Webhook URL 是否正确，机器人是否未被禁用 |
| AI 筛选无效 | 确认 API Key 有效，`enabled: true` 已配置 |
| 热点抓取为空 | 检查关键词是否太窄，先用通用词测试 |
| Docker 启动失败 | `docker logs trendradar` 查看错误日志 |

---

## 九、下一步行动清单

- [ ] **Day 1**：在本地 Mac 上用 Docker 部署 TrendRadar，跑通基本流程
- [ ] **Day 1**：申请飞书群机器人，拿到 Webhook URL
- [ ] **Day 1**：配置初始关键词，启动测试推送
- [ ] **Day 2**：如有云服务器，迁移到服务器，配置定时任务
- [ ] **Day 2**：配置 DeepSeek API Key，开启 AI 筛选和简报
- [ ] **Day 3**：根据实际推送效果，调整关键词和过滤规则
- [ ] **Weekly**：复盘热点捕获效果，持续优化关键词库

---

## 十、相关资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/sansan0/TrendRadar |
| Docker 镜像 | https://hub.docker.com/r/wantcat/trendradar |
| 项目文档 | https://deepwiki.com/sansan0/TrendRadar |
| MCP 服务部署 | https://www.mcpworld.com/en/detail/xxx |
