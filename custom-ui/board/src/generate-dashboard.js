#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '../../..');
const TASK_DIR = path.join(ROOT, 'tasks', 'in_progress');
const OUT_PATH = path.join(ROOT, 'custom-ui', 'board', 'data', 'dashboard.json');

const AGENT_ROSTER = [
  { id: 'main', name: '小麦', department: '尚书省' },
  { id: 'product', name: '产品经理', department: '产品' },
  { id: 'reviewer', name: '门下省', department: '审核' },
  { id: 'developer', name: '开发工程师', department: '研发' },
  { id: 'tester', name: '测试工程师', department: '测试' },
  { id: 'devops', name: '运维工程师', department: '运维' },
  { id: 'copywriter', name: '文案', department: '运营' },
  { id: 'video', name: '视频', department: '运营' },
  { id: 'operator', name: '运营', department: '运营' },
  { id: 'analyst', name: '数据分析师', department: '职能' },
  { id: 'assistant', name: '助手', department: '职能' },
];

function parseOwner(filename, text) {
  const fn = path.basename(filename);
  const m1 = fn.match(/^任务_\d{4}-\d{2}-\d{2}_([^_]+)_/);
  if (m1) return m1[1];
  const m2 = text.match(/(?:负责人|接收人|指派对象)[:：]\s*([^\n]+)/);
  if (m2) return m2[1].trim();
  return '未分配';
}

function normalizeOwner(owner = '') {
  const s = String(owner).trim();
  if (!s) return '未分配';
  if (s.includes('产品经理')) return '产品经理';
  if (s.includes('测试工程师')) return '测试工程师';
  if (s.includes('开发工程师')) return '开发工程师';
  if (s.includes('数据分析师')) return '数据分析师';
  if (s.includes('运维工程师')) return '运维工程师';
  if (s.includes('文案')) return '文案';
  if (s.includes('视频')) return '视频';
  if (s.includes('运营')) return '运营';
  if (s.includes('门下省') || s.includes('审核')) return '门下省';
  if (s.includes('小麦') || s.includes('尚书')) return '小麦';
  if (s.includes('助手')) return '助手';
  return s;
}

function parseTitle(filename, text) {
  const fn = path.basename(filename, '.md');
  const m1 = fn.match(/^任务_\d{4}-\d{2}-\d{2}_[^_]+_(.+)$/);
  if (m1) return m1[1];
  const m2 = text.match(/(?:任务|标题)[:：]\s*([^\n]+)/);
  return (m2?.[1] || fn).trim();
}

function parseDateKey(filename, statMs) {
  const fn = path.basename(filename);
  const m = fn.match(/任务_(\d{4}-\d{2}-\d{2})_/);
  if (m) return `${m[1]}-${String(statMs).padStart(13, '0')}`;
  return `0000-00-00-${String(statMs).padStart(13, '0')}`;
}

function readTasks() {
  if (!fs.existsSync(TASK_DIR)) return [];
  const files = fs.readdirSync(TASK_DIR).filter((f) => f.endsWith('.md') && f.startsWith('任务_'));
  const tasks = [];
  for (const f of files) {
    const full = path.join(TASK_DIR, f);
    const st = fs.statSync(full);
    const text = fs.readFileSync(full, 'utf8');
    const ownerRaw = parseOwner(f, text);
    tasks.push({
      file: f,
      ownerRaw,
      owner: normalizeOwner(ownerRaw),
      title: parseTitle(f, text),
      key: parseDateKey(f, st.mtimeMs),
      mtimeMs: st.mtimeMs,
    });
  }
  return tasks;
}

function ownerMatch(owner, agent) {
  const normalized = normalizeOwner(owner);
  return normalized === agent.name;
}

function buildPayload() {
  const tasks = readTasks();

  // 主链路：实时读取 tasks/in_progress，并按 owner 选最新任务作为“当前任务”
  const latestByOwner = new Map();
  for (const t of tasks) {
    const prev = latestByOwner.get(t.owner);
    if (!prev || t.key > prev.key) latestByOwner.set(t.owner, t);
  }

  const activeTasks = Array.from(latestByOwner.values());

  const agents = AGENT_ROSTER.map((a) => {
    const matched = activeTasks.filter((t) => ownerMatch(t.owner, a));
    const latest = matched.sort((x, y) => (x.key < y.key ? 1 : -1))[0];
    const currentTasks = latest ? [latest] : [];
    return {
      id: a.id,
      name: a.name,
      department: a.department,
      status: currentTasks.length ? 'active' : 'done',
      currentTask: latest ? latest.title : '（空闲）',
      todoCount: currentTasks.length,
      recentDone: '-',
      durationSec: 0,
      tokenUsed: 0,
      tasks: currentTasks.map((t) => ({ title: t.title, status: 'doing', durationSec: 0, tokens: 0 })),
    };
  });

  const payload = {
    generatedAt: new Date().toISOString(),
    source: 'tasks/in_progress realtime aggregation',
    summary: {
      totalAgents: agents.length,
      activeAgents: agents.filter((a) => a.status === 'active').length,
      doneAgents: agents.filter((a) => a.status === 'done').length,
      todoItems: agents.reduce((s, a) => s + a.todoCount, 0),
      totalDurationSec: 0,
      totalTokens: 0,
    },
    agents,
    taskBoard: {
      todo: [],
      doing: activeTasks.map((t) => ({ title: t.title, owner: t.owner, priority: 'P0', status: 'doing' })),
      done: [],
    },
  };

  fs.mkdirSync(path.dirname(OUT_PATH), { recursive: true });
  fs.writeFileSync(OUT_PATH, JSON.stringify(payload, null, 2));
  return payload;
}

const payload = buildPayload();
console.log(`[board-data] written: ${OUT_PATH}`);
console.log(`[board-data] PM todoCount=${payload.agents.find((a) => a.id === 'product')?.todoCount || 0}`);
console.log(`[board-data] Tester todoCount=${payload.agents.find((a) => a.id === 'tester')?.todoCount || 0}`);
