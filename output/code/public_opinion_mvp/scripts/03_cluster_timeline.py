#!/usr/bin/env python3
import argparse
from collections import Counter
from statistics import mean
from common import load_json, write_json, parse_ts, token_set, jaccard


def rule_topic(text):
    if '泄露' in text or '异常登录' in text:
        return '数据安全疑虑'
    if '宕机' in text or '崩溃' in text or '无法' in text:
        return '服务可用性故障'
    if '涨价' in text:
        return '价格争议'
    if '维权' in text or '投诉' in text:
        return '用户维权'
    return '其他'


def to_metrics(events):
    counts = [len(e['items']) for e in events]
    return {
        'event_count': len(events),
        'avg_mentions_per_event': round(mean(counts), 2) if counts else 0
    }


def baseline_cluster(mentions, sim_threshold=0.25):
    events = []
    for m in mentions:
        topic = rule_topic(m['text'])
        toks = token_set(m['text'])
        assigned = None
        for e in events:
            if e['topic'] != topic:
                continue
            if jaccard(toks, e['token_union']) >= sim_threshold:
                assigned = e
                break
        if assigned is None:
            assigned = {
                'event_id': f"B{len(events)+1:03d}",
                'topic': topic,
                'items': [],
                'token_union': set()
            }
            events.append(assigned)
        assigned['items'].append(m)
        assigned['token_union'] |= toks
    return events


def optimized_cluster(mentions, assign_threshold=0.2, merge_threshold=0.45, time_merge_minutes=90):
    # step1: relaxed assignment to reduce early fragmentation
    events = []
    for m in mentions:
        topic = rule_topic(m['text'])
        toks = token_set(m['text'])
        best_sim = -1
        best_event = None
        for e in events:
            if e['topic'] != topic:
                continue
            sim = jaccard(toks, e['token_union'])
            if sim > best_sim:
                best_sim = sim
                best_event = e
        if best_event is not None and best_sim >= assign_threshold:
            assigned = best_event
        else:
            assigned = {
                'event_id': f"E{len(events)+1:03d}",
                'topic': topic,
                'items': [],
                'token_union': set()
            }
            events.append(assigned)
        assigned['items'].append(m)
        assigned['token_union'] |= toks

    # step2: merge similar clusters in same topic
    merged = True
    while merged:
        merged = False
        i = 0
        while i < len(events):
            j = i + 1
            while j < len(events):
                a, b = events[i], events[j]
                if a['topic'] == b['topic'] and jaccard(a['token_union'], b['token_union']) >= merge_threshold:
                    a['items'].extend(b['items'])
                    a['token_union'] |= b['token_union']
                    events.pop(j)
                    merged = True
                else:
                    j += 1
            i += 1

    # step3: time-proximity merge for tiny clusters (same topic)
    changed = True
    while changed:
        changed = False
        for i, e in enumerate(list(events)):
            if len(e['items']) > 1:
                continue
            ts_e = parse_ts(e['items'][0]['timestamp'])
            best_j = None
            best_gap = None
            for j, t in enumerate(events):
                if i == j or t['topic'] != e['topic']:
                    continue
                ts_t = parse_ts(t['items'][0]['timestamp'])
                gap = abs((ts_e - ts_t).total_seconds()) / 60
                if gap <= time_merge_minutes and (best_gap is None or gap < best_gap):
                    best_gap = gap
                    best_j = j
            if best_j is not None:
                target = events[best_j]
                target['items'].extend(e['items'])
                target['token_union'] |= e['token_union']
                events.remove(e)
                changed = True
                break

    # normalize event ids after merge
    for idx, e in enumerate(events, 1):
        e['event_id'] = f"E{idx:03d}"
    return events


def build_event_outputs(events):
    out_events = []
    timeline_nodes = []
    timeline_links = []

    for e in events:
        items = sorted(e['items'], key=lambda x: parse_ts(x['timestamp']))
        bucket = Counter()
        channel_c = Counter(x['channel'] for x in items)
        senti_c = Counter(x.get('sentiment', 'neutral') for x in items)
        topic_c = Counter(rule_topic(x['text']) for x in items)

        for x in items:
            b = parse_ts(x['timestamp']).strftime('%Y-%m-%d %H:%M')[:-1] + '0'
            bucket[b] += 1

        peak_bucket, peak_count = ('', 0)
        if bucket:
            peak_bucket, peak_count = max(bucket.items(), key=lambda kv: kv[1])

        points = sorted(bucket.items(), key=lambda kv: kv[0])
        turnings = []
        for i in range(1, len(points)-1):
            prev_v, cur_v, next_v = points[i-1][1], points[i][1], points[i+1][1]
            if (cur_v > prev_v and cur_v > next_v) or (cur_v < prev_v and cur_v < next_v):
                turnings.append({'bucket': points[i][0], 'value': cur_v})

        eid = e['event_id']
        out_events.append({
            'event_id': eid,
            'topic': e['topic'],
            'mention_count': len(items),
            'start_time': items[0]['timestamp'],
            'end_time': items[-1]['timestamp'],
            'channels': sorted(channel_c.keys()),
            'sample_texts': [x['text'] for x in items[:3]],
            'attribution': {
                'channel': dict(channel_c),
                'topic': dict(topic_c),
                'sentiment': dict(senti_c)
            },
            'timeline_stats': {
                'peak_bucket': peak_bucket,
                'peak_count': peak_count,
                'turning_points': turnings,
                'bucket_series': [{'bucket': k, 'count': v} for k, v in sorted(bucket.items())]
            }
        })

        for idx, x in enumerate(items):
            nid = f"{eid}_N{idx+1:03d}"
            timeline_nodes.append({
                'node_id': nid,
                'event_id': eid,
                'time': x['timestamp'],
                'channel': x['channel'],
                'sentiment': x.get('sentiment', 'neutral'),
                'text': x['text']
            })
            if idx > 0:
                timeline_links.append({'source': f"{eid}_N{idx:03d}", 'target': nid, 'event_id': eid})

    out_events.sort(key=lambda x: x['mention_count'], reverse=True)
    return out_events, timeline_nodes, timeline_links


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--assign-threshold', type=float, default=0.2)
    p.add_argument('--merge-threshold', type=float, default=0.45)
    p.add_argument('--baseline-threshold', type=float, default=0.25)
    p.add_argument('--time-merge-minutes', type=int, default=90)
    args = p.parse_args()

    detected = load_json(args.input)
    mentions = detected.get('mentions', [])
    mentions.sort(key=lambda x: parse_ts(x['timestamp']))

    baseline_events = baseline_cluster(mentions, sim_threshold=args.baseline_threshold)
    optimized_events = optimized_cluster(
        mentions,
        assign_threshold=args.assign_threshold,
        merge_threshold=args.merge_threshold,
        time_merge_minutes=args.time_merge_minutes,
    )

    out_events, timeline_nodes, timeline_links = build_event_outputs(optimized_events)

    before = to_metrics(baseline_events)
    after = to_metrics(optimized_events)

    write_json(args.output, {
        'events': out_events,
        'timeline_graph': {
            'nodes': timeline_nodes,
            'links': timeline_links
        },
        'timeline': [
            {
                'time': n['time'],
                'event_id': n['event_id'],
                'channel': n['channel'],
                'text': n['text']
            } for n in sorted(timeline_nodes, key=lambda x: parse_ts(x['time']))
        ],
        'summary': after,
        'fragmentation_optimization': {
            'before': before,
            'after': after,
            'strategy': {
                'baseline_threshold': args.baseline_threshold,
                'optimized_assign_threshold': args.assign_threshold,
                'optimized_merge_threshold': args.merge_threshold,
                'optimized_time_merge_minutes': args.time_merge_minutes,
                'method': 'best-match assignment + same-topic iterative merge + time-proximity merge for tiny clusters'
            }
        }
    })

    print(f"[cluster] before_events={before['event_count']} after_events={after['event_count']} -> {args.output}")


if __name__ == '__main__':
    main()
