#!/bin/bash
# ===========================================
# Sub2Api 中转站一键部署脚本
# 使用方法：
#   1. 将整个 sub2api-relay 目录上传到 VPS
#   2. SSH 到 VPS 后执行：
#      chmod +x setup.sh && ./setup.sh
# ===========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}   Sub2Api 中转站一键部署脚本${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# ---- 第一步：检测系统环境 ----
echo -e "${YELLOW}[1/5] 检测系统环境...${NC}"

if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}请使用 root 用户运行此脚本${NC}"
    exit 1
fi

OS=$(lsb_release -is 2>/dev/null || echo "Unknown")
VER=$(lsb_release -rs 2>/dev/null || echo "Unknown")
echo -e "  系统: ${GREEN}${OS} ${VER}${NC}"

# ---- 第二步：安装 Docker ----
echo -e "${YELLOW}[2/5] 安装 Docker...${NC}"

if command -v docker &> /dev/null; then
    echo -e "  Docker 已安装: ${GREEN}$(docker --version)${NC}"
else
    echo "  正在安装 Docker..."
    apt update -qq
    apt install -y -qq curl ca-certificates gnupg
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo -e "  Docker 安装完成: ${GREEN}$(docker --version)${NC}"
fi

# 检查 Docker Compose
if docker compose version &> /dev/null; then
    echo -e "  Docker Compose: ${GREEN}$(docker compose version --short)${NC}"
else
    echo "  正在安装 Docker Compose 插件..."
    apt install -y -qq docker-compose-plugin
    echo -e "  Docker Compose 安装完成${NC}"
fi

# ---- 第三步：安装 Cloudflare WARP ----
echo -e "${YELLOW}[3/5] 配置 Cloudflare WARP...${NC}"

if ss -tlnp | grep -q ':40000'; then
    echo -e "  WARP SOCKS5 代理已在端口 40000 运行 ${GREEN}✓${NC}"
else
    echo -e "  ${YELLOW}WARP 尚未配置，即将运行安装脚本...${NC}"
    echo -e "  ${YELLOW}请在脚本菜单中选择 【选项 2】 注册启动 WARP 代理${NC}"
    echo ""
    read -p "  按回车继续安装 WARP..." 
    wget -N https://gitlab.com/rwkgyg/cfwarp/raw/main/cfwarp.sh && bash cfwarp.sh
    echo ""
    
    # 验证 WARP 状态
    if ss -tlnp | grep -q ':40000'; then
        echo -e "  WARP SOCKS5 代理启动成功 ${GREEN}✓${NC}"
    else
        echo -e "  ${RED}WARP 代理未检测到，请手动检查${NC}"
        echo -e "  可重新运行: ${YELLOW}bash cfwarp.sh${NC}"
    fi
fi

# 测试 WARP 代理
echo -e "  测试 WARP 代理出口 IP..."
WARP_IP=$(curl -s --socks5 127.0.0.1:40000 https://ipinfo.io/ip 2>/dev/null || echo "failed")
if [ "$WARP_IP" != "failed" ]; then
    echo -e "  WARP 出口 IP: ${GREEN}${WARP_IP}${NC}"
else
    echo -e "  ${RED}WARP 代理测试失败，请检查 WARP 状态${NC}"
fi

# ---- 第四步：配置环境变量 ----
echo -e "${YELLOW}[4/5] 配置环境变量...${NC}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f .env ]; then
    echo -e "  .env 文件已存在，跳过配置"
    echo -e "  如需修改，请手动编辑: ${BLUE}nano .env${NC}"
else
    # 生成随机 Redis 密码
    REDIS_PWD=$(openssl rand -hex 16)
    
    echo ""
    echo -e "  请输入 ${BLUE}Cloudflare Tunnel Token${NC}:"
    echo -e "  (获取方式: Cloudflare Dashboard → Zero Trust → Networks → Tunnels)"
    read -p "  Token: " CF_TOKEN
    
    if [ -z "$CF_TOKEN" ]; then
        echo -e "  ${RED}Token 不能为空！${NC}"
        echo -e "  请稍后手动编辑 .env 文件填写 Token"
        CF_TOKEN="your_cloudflare_tunnel_token_here"
    fi
    
    cat > .env << EOF
REDIS_PASSWORD=${REDIS_PWD}
TUNNEL_TOKEN=${CF_TOKEN}
WARP_PROXY=socks5h://172.17.0.1:40000
EOF
    
    echo -e "  .env 配置文件已生成 ${GREEN}✓${NC}"
    echo -e "  Redis 密码: ${GREEN}${REDIS_PWD}${NC}"
fi

# ---- 第五步：启动服务 ----
echo -e "${YELLOW}[5/5] 启动 Sub2Api 服务...${NC}"

docker compose pull
docker compose up -d

echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}   部署完成！${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo -e "  服务状态:"
docker compose ps --format "table {{.Name}}\t{{.State}}\t{{.Ports}}"
echo ""
echo -e "  ${BLUE}常用命令:${NC}"
echo -e "    查看日志:  ${YELLOW}docker logs -f sub2api_core${NC}"
echo -e "    重启服务:  ${YELLOW}docker compose restart${NC}"
echo -e "    停止服务:  ${YELLOW}docker compose down${NC}"
echo -e "    更新镜像:  ${YELLOW}docker compose pull && docker compose up -d${NC}"
echo ""
echo -e "  ${BLUE}验证测试:${NC}"
echo -e "    本地测试:  ${YELLOW}curl http://localhost:8000/v1/models${NC}"
echo -e "    WARP IP:   ${YELLOW}curl --socks5 127.0.0.1:40000 https://ipinfo.io${NC}"
echo ""
echo -e "  ${GREEN}接下来请在 Sub2Api 管理面板中配置你的 API Key${NC}"
echo -e "  管理面板默认地址: ${BLUE}http://你的域名${NC}"
