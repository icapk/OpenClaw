#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "[1/2] 生成看板数据..."
python3 generate_data.py

echo "[2/2] 启动本地服务..."
echo "Portal地址: http://127.0.0.1:18979"
echo "办公室看板: http://127.0.0.1:18979/office"
python3 serve.py
