#!/bin/bash
# OpenClaw Workspace 每日备份脚本
# 检查是否今日已备份，未备份则执行

BACKUP_FLAG="/Users/a1/.openclaw/workspace/.last_backup_date"
TODAY=$(date "+%Y-%m-%d")

cd /Users/a1/.openclaw/workspace || exit 1

# 检查是否今日已备份
if [ -f "$BACKUP_FLAG" ] && [ "$(cat "$BACKUP_FLAG")" = "$TODAY" ]; then
    exit 0  # 静默跳过，不打印任何内容
fi

# 检查是否有 remote
if ! git remote get-url origin &>/dev/null; then
    exit 0
fi

# 检查是否有变更
if git diff --quiet && git diff --cached --quiet && [ -z "$(git status --porcelain)" ]; then
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
echo "✅ OpenClaw 工作区已备份 - $TIMESTAMP"
