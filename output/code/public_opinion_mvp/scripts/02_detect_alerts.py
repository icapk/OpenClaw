#!/usr/bin/env python3
import argparse
from collections import Counter, defaultdict
from common import load_json, write_json, parse_ts, now_iso


def calc_sentiment(text, neg_words, pos_words):
    neg = sum(1 for w in neg_words if w in text)
    pos = sum(1 for w in pos_words if w in text)
    if neg > pos:
        return 'negative', neg, pos
    if pos > neg:
        return 'positive', neg, pos
    return 'neutral', neg, pos


def level_from_score(score):
    if score >= 80:
        return 'P1'
    if score >= 50:
        return 'P2'
    return 'P3'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--monitor', required=True, help='config/monitor.json')
    p.add_argument('--input', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()

    cfg = load_json(args.monitor)
    data = load_json(args.input).get('items', [])
    kw = cfg['keywords']
    neg_words = cfg['sentiment']['negative_words']
    pos_words = cfg['sentiment']['positive_words']
    thresholds = cfg['thresholds']

    mentions = []
    sentiment_counter = Counter()
    bucket_counter = Counter()
    keyword_counter = Counter()
    topic_counter = Counter()

    for x in data:
        hit = [k for k in kw if k in x['text']]
        if not hit:
            continue
        ts = parse_ts(x['timestamp'])
        b = ts.strftime('%Y-%m-%d %H:%M')[:-1] + '0'
        senti, neg, pos = calc_sentiment(x['text'], neg_words, pos_words)
        if '泄露' in x['text'] or '异常登录' in x['text']:
            topic = '数据安全'
        elif '宕机' in x['text'] or '崩溃' in x['text'] or '无法' in x['text']:
            topic = '服务故障'
        elif '涨价' in x['text']:
            topic = '价格争议'
        elif '投诉' in x['text'] or '维权' in x['text']:
            topic = '维权投诉'
        else:
            topic = '其他'

        sentiment_counter[senti] += 1
        bucket_counter[b] += 1
        topic_counter[topic] += 1
        for k in hit:
            keyword_counter[k] += 1
        mentions.append({**x, 'keywords_hit': hit, 'sentiment': senti, 'neg_score': neg, 'pos_score': pos, 'bucket': b, 'topic': topic})

    total = len(mentions)
    neg_ratio = sentiment_counter['negative'] / total if total else 0
    peak = max(bucket_counter.values()) if bucket_counter else 0
    avg = (sum(bucket_counter.values()) / len(bucket_counter)) if bucket_counter else 0
    surge = (peak >= max(1, avg * thresholds['surge_multiplier'])) and peak >= thresholds['min_mentions_for_alert']

    reasons = []
    if total >= thresholds['min_mentions_for_alert']:
        reasons.append('mention_count_reached')
    if neg_ratio >= thresholds['negative_ratio']:
        reasons.append('negative_ratio_exceeded')
    if surge:
        reasons.append('surge_detected')

    risk_score = 0
    risk_score += min(40, total * 2)
    risk_score += min(30, int(neg_ratio * 100 * 0.3))
    risk_score += 20 if surge else 0
    risk_score += 10 if ('数据安全' in topic_counter and topic_counter['数据安全'] >= 2) else 0

    level = level_from_score(risk_score)
    if not reasons:
        level = 'P3'

    escalation_cfg = cfg.get('escalation', {})
    esc_timeout = escalation_cfg.get('timeout_minutes', 20)
    esc_target = escalation_cfg.get('next_level', {'P3': 'P2', 'P2': 'P1', 'P1': 'P1'})
    alerts = []
    now = now_iso()

    topic_mentions = defaultdict(list)
    for m in mentions:
        topic_mentions[m['topic']].append(m)

    for topic, items in topic_mentions.items():
        items.sort(key=lambda x: x['timestamp'])
        item_total = len(items)
        item_neg = sum(1 for x in items if x['sentiment'] == 'negative')
        item_neg_ratio = item_neg / item_total if item_total else 0
        base_score = min(50, item_total * 5) + int(item_neg_ratio * 40)
        if topic == '数据安全':
            base_score += 15
        l = level_from_score(base_score)
        triggered = item_total >= max(2, thresholds['min_mentions_for_alert'] - 1)
        status = 'open' if triggered else 'observe'

        alerts.append({
            'alert_id': f"A-{abs(hash(topic)) % 10000:04d}",
            'topic': topic,
            'level': l,
            'status': status,
            'created_at': items[0]['timestamp'],
            'updated_at': items[-1]['timestamp'],
            'escalate_after_minutes': esc_timeout,
            'escalate_to': esc_target.get(l, l),
            'reasons': reasons,
            'metrics': {
                'mentions': item_total,
                'negative_ratio': round(item_neg_ratio, 3)
            }
        })

    result = {
        'generated_at': now,
        'summary': {
            'total_mentions': total,
            'sentiment_count': dict(sentiment_counter),
            'negative_ratio': round(neg_ratio, 3),
            'peak_bucket_mentions': peak,
            'avg_bucket_mentions': round(avg, 2),
            'keyword_count': dict(keyword_counter),
            'topic_count': dict(topic_counter),
            'risk_score': risk_score
        },
        'alert': {
            'triggered': len(reasons) > 0,
            'level': level,
            'reasons': reasons,
            'escalation_policy': escalation_cfg
        },
        'alerts': alerts,
        'mentions': mentions
    }

    write_json(args.output, result)
    print(f"[detect] mentions={total} level={level} topic_alerts={len(alerts)} -> {args.output}")


if __name__ == '__main__':
    main()
