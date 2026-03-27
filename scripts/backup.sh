#!/bin/bash
# OpenClaw Workspace 每日自动备份脚本
# 功能：git add → commit → push

cd /Users/a1/.openclaw/workspace || exit 1

# 检查是否有 remote
if ! git remote get-url origin &>/dev/null; then
    echo "⚠️  未配置 git remote，跳过备份"
    exit 0
fi

# 检查是否有变更
if git diff --quiet && git diff --cached --quiet; then
    echo "📝 无变更，跳过备份"
    exit 0
fi

# 添加所有变更
git add -A

# 提交（带时间戳）
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
git commit -m "💾 自动备份 - $TIMESTAMP"

# 推送到远程
git push origin main

echo "✅ 备份完成 - $TIMESTAMP"
