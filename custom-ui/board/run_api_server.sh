#!/bin/bash
# 启动OpenClaw API服务器

cd "$(dirname "$0")"

echo "🚀 启动OpenClaw API服务器..."
python3 api_server.py &

# 等待服务器启动
sleep 2

echo "✅ OpenClaw API服务器已启动"
echo "📊 访问办公室看板: http://127.0.0.1:18980/custom-ui/board/office-visual.html"
echo "🔗 API端点: http://127.0.0.1:18980/api/openclaw-exec"