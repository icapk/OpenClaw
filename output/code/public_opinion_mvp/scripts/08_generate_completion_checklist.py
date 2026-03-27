#!/usr/bin/env python3
import argparse
from common import write_text


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', required=True)
    args = p.parse_args()

    md = """# 最终功能清单_v1.0

## done
- 聚类优化：采用 best-match + 同主题迭代合并，减少事件碎片化
- 聚类对比指标：输出优化前/后事件数、平均每事件条目数（写入时间线数据）
- 数据采集鲁棒性：RSS/HTTP 增加重试、超时、重试间隔配置
- 失败回退：RSS/HTTP 失败自动 fallback 到 sample，并记录失败原因与回退记录
- 通知链路联调：notifier 支持 openclaw message 实发模式（配置开关）
- 通知优雅降级：无权限/命令失败自动降级 mock，不中断主流程并写日志
- feishu_doc 适配增强：支持 mock/openclaw 可切换模式 + 真实调用异常处理
- feishu_doc 无权限兜底：失败保持 mock 并在日志输出原因
- Dashboard 增强：新增 10 分钟桶趋势图（折线+柱）
- Dashboard 对比卡片：展示事件碎片化优化前后指标
- 完整演示脚本：run_full_demo.sh 贯穿新能力
- 验收脚本：run_acceptance.sh 自动生成“验收报告.md”并逐项判定通过/失败
- 文档升级：README 更新为 v1.0 完整版

## partial
- 无

## todo
- 无（当前补救项均已落地）
"""
    write_text(args.output, md)
    print(f"[checklist] -> {args.output}")


if __name__ == '__main__':
    main()
