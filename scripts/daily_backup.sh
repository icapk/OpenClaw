#!/bin/bash
# OpenClaw Workspace 每日备份脚本
# 检查是否今日已备份，未备份则执行

BACKUP_FLAG="/Users/a1/.openclaw/workspace/.last_backup_date"
TODAY=$(date "+%Y-%m-%d")

cd /Users/a1/.openclaw/workspace || exit 1

# 检查是否今日已备份
if [ -f "$BACKUP_FLAG" ] && [ "$(cat "$BACKUP_FLAG")" = "$TODAY" ]; then
    echo "📝 今日($TODAY)已备份，跳过"
    exit 0
fi

# 检查是否有 remote
if ! git remote get-url origin &>/dev/null; then
    echo "⚠️  未配置 git remote，跳过备份"
    exit 0
fi

# 检查是否有变更
if git diff --quiet && git diff --cached --quiet && [ -z "$(git status --porcelain)" ]; then
    echo "📝 无变更，跳过备份"
    echo -n "$TODAY" > "$BACKUP_FLAG"
    exit 0
fi

# 执行备份
git add -A
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
git commit -m "💾 自动备份 - $TIMESTAMP"
git push origin main

# 记录备份日期
echo -n "$TODAY" > "$BACKUP_FLAG"
echo "✅ 备份完成 - $TODAY $TIMESTAMP"
