# Sub2Api 中转站部署包

自建 API 中转站，基于 [Sub2Api](https://github.com/muxing/sub2api) 项目。

## 架构

```
客户端 → Cloudflare Tunnel (你的域名) → Sub2Api → WARP代理 → OpenAI/Claude API
```

## 快速部署

### 前置要求

- 海外 VPS（Ubuntu 22.04/24.04 LTS）
- Cloudflare 账号 + 域名
- OpenAI/Claude 官方 API Key

### 部署步骤

```bash
# 1. 上传此目录到 VPS
scp -r ./sub2api-relay root@你的VPS-IP:/opt/sub2api

# 2. SSH 登录 VPS
ssh root@你的VPS-IP

# 3. 执行一键部署
cd /opt/sub2api
chmod +x setup.sh
./setup.sh
```

脚本将自动完成：
1. ✅ 安装 Docker & Docker Compose
2. ✅ 安装配置 Cloudflare WARP (SOCKS5 代理)
3. ✅ 生成 .env 配置文件
4. ✅ 拉取并启动 Sub2Api + Redis + Cloudflare Tunnel

### Cloudflare Tunnel 设置

1. 登录 [Cloudflare Zero Trust](https://one.dash.cloudflare.com/)
2. **Networks → Tunnels → Create**
3. 复制 Tunnel Token（脚本运行时会提示输入）
4. 添加 Public Hostname:
   - **Domain**: `api.yourdomain.com`
   - **Service**: `http://localhost:8000`

## 文件说明

| 文件 | 说明 |
|------|------|
| `docker-compose.yml` | Docker 服务编排（Sub2Api + Redis + Cloudflared） |
| `.env.example` | 环境变量模板 |
| `setup.sh` | 一键部署脚本 |

## 常用命令

```bash
docker logs -f sub2api_core    # 查看日志
docker compose restart          # 重启服务
docker compose down             # 停止服务
docker compose pull && docker compose up -d  # 更新
```
