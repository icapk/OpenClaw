#!/usr/bin/env python3
"""
日报生成脚本
读取各 agent 工作日志，生成每日汇总
"""
import os
from datetime import datetime

WORKSPACE = "/Users/a1/.openclaw/workspace"
TODAY = datetime.now().strftime("%Y-%m-%d")
REPORT_DIR = f"{WORKSPACE}/日报"
AGENTS_DIR = f"{WORKSPACE}/agents"

AGENT_NAMES = {
    "product": "产品",
    "developer": "开发",
    "tester": "测试",
    "operations": "运营",
    "小麦": "小麦",
}

def read_work_log(agent_path):
    """读取工作日志内容"""
    log_file = f"{agent_path}/工作日志.md"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            return f.read()
    return None

def generate_report():
    """生成日报"""
    report = f"""# 日报 · {TODAY}

---

## 核心讨论

"""
    agents_content = {}
    for agent_id, agent_name in AGENT_NAMES.items():
        agent_path = f"{AGENTS_DIR}/{agent_id}"
        if os.path.exists(agent_path):
            content = read_work_log(agent_path)
            if content:
                agents_content[agent_name] = content

    if not agents_content:
        report += "_今日各 agent 暂无工作日志记录_"
    else:
        for name, content in agents_content.items():
            report += f"### {name}\n{content}\n---\n"

    # 写入日报
    os.makedirs(REPORT_DIR, exist_ok=True)
    report_file = f"{REPORT_DIR}/日报_{TODAY}.md"
    with open(report_file, "w") as f:
        f.write(report)

    print(f"✅ 日报已生成: {report_file}")
    return report_file

if __name__ == "__main__":
    generate_report()
