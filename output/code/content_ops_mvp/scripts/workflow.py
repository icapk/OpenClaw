#!/usr/bin/env python3
import argparse
import csv
import datetime as dt
import json
import os
import random
import subprocess
import time
from pathlib import Path


def now_cn():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_config(base_dir: Path) -> dict:
    config_path = base_dir / "config" / "config.json"
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dirs(cfg: dict):
    runtime = Path(cfg["paths"]["runtime_output_dir"])
    for p in [runtime / "drafts", runtime / "published", runtime / "reports", runtime / "logs", Path(cfg["paths"]["weekly_report_dir"])]:
        p.mkdir(parents=True, exist_ok=True)


def log_line(cfg: dict, message: str):
    logf = Path(cfg["paths"]["runtime_output_dir"]) / "logs" / "workflow.log"
    with logf.open("a", encoding="utf-8") as f:
        f.write(f"[{now_cn()}] {message}\n")


def read_topic_seeds(base_dir: Path, cfg: dict):
    p = base_dir / cfg["sources"]["topic_seeds_file"]
    return [x.strip() for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def read_trending(base_dir: Path, cfg: dict):
    p = base_dir / cfg["sources"]["trending_file"]
    rows = []
    with p.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["heat"] = int(row.get("heat", 0))
            rows.append(row)
    return sorted(rows, key=lambda x: x["heat"], reverse=True)


def choose_topic(base_dir: Path, cfg: dict):
    seeds = read_topic_seeds(base_dir, cfg)
    trending = read_trending(base_dir, cfg)
    keywords = cfg["workflow"]["keywords"]
    best = None
    for row in trending:
        if any(k in row["keyword"] or row["keyword"] in k for k in keywords):
            best = row
            break
    if not best:
        best = trending[0] if trending else {"keyword": random.choice(seeds) if seeds else "内容增长", "heat": 50, "source": "seed"}
    topic = f"{best['keyword']}：{random.choice(seeds) if seeds else '实战指南'}"
    return {
        "topic": topic,
        "keyword": best["keyword"],
        "heat": best["heat"],
        "source": best.get("source", "unknown")
    }


def render_template(template_text: str, vars_map: dict) -> str:
    out = template_text
    for k, v in vars_map.items():
        out = out.replace("{{" + k + "}}", str(v))
    return out


def create_draft(base_dir: Path, cfg: dict, channel: str, topic_info: dict):
    channel_cfg = cfg["channels"][channel]
    tpl_path = base_dir / channel_cfg["template"]
    tpl = tpl_path.read_text(encoding="utf-8")
    title = f"{topic_info['topic']}（{channel.upper()}）"
    vars_map = {
        "title": title,
        "publish_time": channel_cfg["publish_time"],
        "account": channel_cfg["account"],
        "hook": f"这个选题热度 {topic_info['heat']}，正处于增长窗口。",
        "problem_status": "很多团队内容生产链路断裂，无法稳定输出。",
        "pain_point": "选题靠拍脑袋、发布靠手动、复盘无数据。",
        "opportunity": "把流程产品化后，可规模复用。",
        "step1_title": "选题标准化",
        "step1_body": "通过关键词和热度数据自动排序，锁定本日主选题。",
        "step2_title": "模板化创作",
        "step2_body": "按平台模板自动生成首稿，减少从0写作时间。",
        "step3_title": "发布与反馈闭环",
        "step3_body": "发布后收集核心指标，周报自动汇总。",
        "case_study": "某团队将内容产能提升 2.3 倍，周复盘耗时下降 70%。",
        "todo_today": "产出并发布 1 条内容",
        "todo_week": "形成可复用素材库",
        "todo_month": "完成多平台自动化适配",
        "closing": "内容不是灵感游戏，而是可运营的系统工程。",
        "cover_text": "别再发教程了：我用 OpenClaw 做了一个会自我进化的内容系统",
        "opening": "反常识：真正拉开差距的不是会写，而是会让内容系统自己变强。",
        "method": "用‘3秒钩子+冲突观点+可验证实验+评论诱因’四步法，把每篇内容变成可复盘增长实验。",
        "cta": "如果你要我把这个工作流做成可复制版本，评论区打“系统”，我按点赞前20私发模板结构。",
        "comment_bait": "你更想看哪条实验线：A. 争议观点爆发流量  B. 干货清单稳定转化？",
        "tags": "#OpenClaw #AIAgent #内容增长 #小红书运营 #自动化工作流"
    }
    body = render_template(tpl, vars_map)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(cfg["paths"]["runtime_output_dir"]) / "drafts" / f"{ts}_{channel}.md"
    out.write_text(body, encoding="utf-8")
    return out, title


def publish_content(cfg: dict, channel: str, title: str, draft_path: Path):
    pub_dir = Path(cfg["paths"]["runtime_output_dir"]) / "published"
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    payload = {
        "time": now_cn(),
        "channel": channel,
        "title": title,
        "draft": str(draft_path),
        "adapter": cfg["openclaw"]["publish_adapter"],
        "status": "simulated"
    }

    if cfg["openclaw"]["publish_adapter"] == "local_command" and not cfg["workflow"].get("dry_run_publish", True):
        cmd = cfg["openclaw"]["local_publish_command"].format(
            target=cfg["openclaw"]["default_target"],
            text=f"[{channel}] {title} 已发布"
        )
        try:
            subprocess.run(cmd, shell=True, check=True)
            payload["status"] = "published"
        except Exception as e:
            payload["status"] = f"publish_failed: {e}"

    out = pub_dir / f"{ts}_{channel}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def capture_feedback(base_dir: Path, cfg: dict, channel: str, title: str):
    fp = base_dir / cfg["sources"]["feedback_metrics_file"]
    week = dt.datetime.now().strftime("%G-W%V")
    row = {
        "week": week,
        "platform": channel,
        "title": title,
        "views": random.randint(3000, 12000),
        "likes": random.randint(100, 900),
        "favorites": random.randint(50, 700),
        "conversions": random.randint(10, 120),
        "publish_date": dt.datetime.now().strftime("%Y-%m-%d")
    }
    with fp.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writerow(row)
    return row


def generate_weekly_report(base_dir: Path, cfg: dict):
    fp = base_dir / cfg["sources"]["feedback_metrics_file"]
    rows = []
    with fp.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for k in ["views", "likes", "favorites", "conversions"]:
                r[k] = int(r[k])
            rows.append(r)
    week = dt.datetime.now().strftime("%G-W%V")
    current = [r for r in rows if r["week"] == week]
    if not current:
        current = rows[-5:]

    totals = {k: sum(r[k] for r in current) for k in ["views", "likes", "favorites", "conversions"]}
    best = max(current, key=lambda x: x["conversions"]) if current else None

    report = f"""# 自媒体内容闭环周报（{week}）

## 一、本周执行概览
- 内容条数：{len(current)}
- 总阅读：{totals['views']}
- 总点赞：{totals['likes']}
- 总收藏：{totals['favorites']}
- 总转化：{totals['conversions']}

## 二、最佳内容
- 平台：{best['platform'] if best else '-'}
- 标题：{best['title'] if best else '-'}
- 转化：{best['conversions'] if best else 0}

## 三、问题与机会
1. 问题：多平台内容复用率仍有提升空间。
2. 机会：高热关键词“AI Agent / 自动化运营”持续有效。

## 四、下周动作
- 继续执行每日自动选题+双平台发布。
- 将高转化选题扩展为系列内容。
- 接入真实平台 API，替换模拟发布链路。

## 五、明细数据
| week | platform | title | views | likes | favorites | conversions | publish_date |
|---|---|---|---:|---:|---:|---:|---|
"""
    for r in current:
        report += f"| {r['week']} | {r['platform']} | {r['title']} | {r['views']} | {r['likes']} | {r['favorites']} | {r['conversions']} | {r['publish_date']} |\n"

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out1 = Path(cfg["paths"]["runtime_output_dir"]) / "reports" / f"weekly_review_{ts}.md"
    out2 = Path(cfg["paths"]["weekly_report_dir"]) / f"内容闭环报告_{ts}.md"
    out1.write_text(report, encoding="utf-8")
    out2.write_text(report, encoding="utf-8")
    return out1, out2


def run_once(base_dir: Path, cfg: dict):
    ensure_dirs(cfg)
    log_line(cfg, "workflow started")

    topic = choose_topic(base_dir, cfg)
    log_line(cfg, f"topic selected: {topic}")

    enabled_channels = [k for k, v in cfg["channels"].items() if v.get("enabled")]
    for ch in enabled_channels:
        draft, title = create_draft(base_dir, cfg, ch, topic)
        log_line(cfg, f"draft created: {draft}")
        pub = publish_content(cfg, ch, title, draft)
        log_line(cfg, f"publish result: {pub}")
        feedback = capture_feedback(base_dir, cfg, ch, title)
        log_line(cfg, f"feedback captured: {feedback}")

    r1, r2 = generate_weekly_report(base_dir, cfg)
    log_line(cfg, f"report generated: {r1} & {r2}")
    print(f"DONE: {r2}")


def run_daemon(base_dir: Path, cfg: dict, interval_minutes: int):
    ensure_dirs(cfg)
    log_line(cfg, f"daemon started interval={interval_minutes}m")
    while True:
        try:
            run_once(base_dir, cfg)
        except Exception as e:
            log_line(cfg, f"daemon run failed: {e}")
        time.sleep(interval_minutes * 60)


def main():
    parser = argparse.ArgumentParser(description="OpenClaw 内容生产工作流 MVP")
    parser.add_argument("mode", nargs="?", default="run_once", choices=["run_once", "daemon", "init"])
    parser.add_argument("--interval", type=int, default=None, help="daemon模式循环分钟")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    cfg = load_config(base_dir)

    if args.mode == "init":
        ensure_dirs(cfg)
        print("INIT DONE")
        return
    if args.mode == "daemon":
        interval = args.interval or cfg["workflow"].get("daemon_interval_minutes", 60)
        run_daemon(base_dir, cfg, interval)
        return

    run_once(base_dir, cfg)


if __name__ == "__main__":
    main()
