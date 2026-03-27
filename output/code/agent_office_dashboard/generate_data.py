#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""采集并整理子 Agent 数据，生成 data/dashboard.json"""

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TODO_PATH = DATA_DIR / "todo.json"
OUT_PATH = DATA_DIR / "dashboard.json"
SNAPSHOT_PATH = DATA_DIR / "subagents_snapshot.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def safe_read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def run_cmd(cmd: List[str]) -> str:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        out = (p.stdout or "").strip()
        return out
    except Exception:
        return ""


def find_json_blob(text: str) -> Any:
    if not text:
        return None
    # 优先完整 JSON
    try:
        return json.loads(text)
    except Exception:
        pass

    # 再尝试提取第一个 JSON 块
    m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def collect_subagents_raw() -> Any:
    candidates = [
        ["openclaw", "subagents", "list", "--json"],
        ["openclaw", "subagents", "list"],
        ["openclaw", "sessions", "list", "--json"],
        ["openclaw", "sessions", "list"],
    ]
    for cmd in candidates:
        text = run_cmd(cmd)
        data = find_json_blob(text)
        if data:
            return data

    # fallback: 本地快照
    snapshot = safe_read_json(SNAPSHOT_PATH, None)
    if snapshot:
        return snapshot

    return []


def normalize_agents(raw: Any) -> List[Dict[str, Any]]:
    # 兼容多种结构
    if isinstance(raw, dict):
        if isinstance(raw.get("items"), list):
            rows = raw["items"]
        elif isinstance(raw.get("subagents"), list):
            rows = raw["subagents"]
        elif isinstance(raw.get("sessions"), list):
            rows = raw["sessions"]
        else:
            rows = [raw]
    elif isinstance(raw, list):
        rows = raw
    else:
        rows = []

    out: List[Dict[str, Any]] = []
    for i, r in enumerate(rows, start=1):
        if not isinstance(r, dict):
            continue

        sid = str(r.get("id") or r.get("sessionId") or r.get("session_id") or f"agent-{i}")
        name = str(r.get("label") or r.get("name") or sid)
        state = str(r.get("status") or r.get("state") or "done").lower()
        online = "active" if "active" in state or state in {"running", "online"} else "done"

        current_task = (
            r.get("task")
            or r.get("currentTask")
            or r.get("current_task")
            or r.get("message")
            or "（暂无）"
        )

        todo_count = int(r.get("todoCount") or r.get("todo_count") or 0)
        recent_done = r.get("recentDone") or r.get("recent_done") or r.get("lastTask") or "（暂无）"
        duration_sec = float(r.get("durationSec") or r.get("duration_sec") or r.get("elapsed") or 0)
        token_used = int(r.get("tokens") or r.get("tokenUsed") or r.get("token_used") or 0)

        tasks = r.get("tasks") if isinstance(r.get("tasks"), list) else []
        if not tasks:
            tasks = [
                {
                    "title": str(current_task),
                    "status": "active" if online == "active" else "done",
                    "durationSec": duration_sec,
                    "tokens": token_used,
                }
            ]

        dept = r.get("department")
        if not dept:
            dept = ["HR", "研发", "运营"][i % 3]

        out.append(
            {
                "id": sid,
                "name": name,
                "department": dept,
                "status": online,
                "currentTask": str(current_task),
                "todoCount": todo_count,
                "recentDone": str(recent_done),
                "durationSec": duration_sec,
                "tokenUsed": token_used,
                "tasks": tasks,
            }
        )

    # 空数据时生成最小示例，保证页面可展示
    if not out:
        out = [
            {
                "id": "agent-dev-1",
                "name": "研发Agent-小川",
                "department": "研发",
                "status": "active",
                "currentTask": "实现看板前端交互",
                "todoCount": 2,
                "recentDone": "完成状态卡片组件",
                "durationSec": 1820,
                "tokenUsed": 12450,
                "tasks": [
                    {"title": "实现看板前端交互", "status": "active", "durationSec": 1820, "tokens": 12450},
                    {"title": "完成状态卡片组件", "status": "done", "durationSec": 960, "tokens": 5320},
                ],
            },
            {
                "id": "agent-ops-1",
                "name": "运营Agent-小舟",
                "department": "运营",
                "status": "done",
                "currentTask": "（空闲）",
                "todoCount": 1,
                "recentDone": "整理周报数据",
                "durationSec": 760,
                "tokenUsed": 4012,
                "tasks": [
                    {"title": "整理周报数据", "status": "done", "durationSec": 760, "tokens": 4012}
                ],
            },
            {
                "id": "agent-hr-1",
                "name": "HRAgent-小禾",
                "department": "HR",
                "status": "active",
                "currentTask": "筛选候选人简历",
                "todoCount": 3,
                "recentDone": "更新面试安排",
                "durationSec": 520,
                "tokenUsed": 2190,
                "tasks": [
                    {"title": "筛选候选人简历", "status": "active", "durationSec": 520, "tokens": 2190},
                    {"title": "更新面试安排", "status": "done", "durationSec": 430, "tokens": 1730},
                ],
            },
        ]

    return out


def merge_todo(agents: List[Dict[str, Any]], todo_items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    board = {"todo": [], "doing": [], "done": []}
    for t in todo_items:
        if not isinstance(t, dict):
            continue
        status = str(t.get("status", "todo")).lower()
        if status not in board:
            status = "todo"
        board[status].append(t)

    # 若 todo.json 为空，按 agent 兜底生成
    if not any(board.values()):
        for a in agents:
            board["doing" if a["status"] == "active" else "done"].append(
                {
                    "title": a["currentTask"],
                    "owner": a["name"],
                    "priority": "P2",
                    "status": "doing" if a["status"] == "active" else "done",
                }
            )
    return board


def build_summary(agents: List[Dict[str, Any]], board: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    total = len(agents)
    active = sum(1 for a in agents if a["status"] == "active")
    done = total - active
    total_tokens = sum(int(a.get("tokenUsed", 0)) for a in agents)
    total_duration = sum(float(a.get("durationSec", 0)) for a in agents)

    return {
        "totalAgents": total,
        "activeAgents": active,
        "doneAgents": done,
        "todoItems": len(board["todo"]),
        "doingItems": len(board["doing"]),
        "doneItems": len(board["done"]),
        "totalTokens": total_tokens,
        "totalDurationSec": total_duration,
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    raw = collect_subagents_raw()
    agents = normalize_agents(raw)
    todo_items = safe_read_json(TODO_PATH, [])
    board = merge_todo(agents, todo_items)
    summary = build_summary(agents, board)

    payload = {
        "generatedAt": now_iso(),
        "source": "openclaw-cli-or-local-snapshot",
        "summary": summary,
        "agents": agents,
        "taskBoard": board,
    }

    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 已生成: {OUT_PATH}")


if __name__ == "__main__":
    main()
