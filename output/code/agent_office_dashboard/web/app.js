const $ = (id) => document.getElementById(id);

function fmtSec(sec = 0) {
  const s = Math.floor(Number(sec || 0));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}m ${r}s`;
}

function statItem(label, value) {
  return `<div class="stat"><span>${label}</span><strong>${value}</strong></div>`;
}

function renderSummary(data) {
  const s = data.summary || {};
  $("summaryStats").innerHTML = [
    statItem("总Agent", s.totalAgents ?? 0),
    statItem("在线(active)", s.activeAgents ?? 0),
    statItem("离线(done)", s.doneAgents ?? 0),
    statItem("待办任务", s.todoItems ?? 0),
    statItem("总耗时", fmtSec(s.totalDurationSec ?? 0)),
    statItem("总Token", s.totalTokens ?? 0),
  ].join("");
  $("generatedAt").textContent = `数据更新时间：${data.generatedAt || "-"} | 来源：${data.source || "-"}`;
}

function renderAgents(data) {
  const list = data.agents || [];
  const wrap = $("agentCards");
  wrap.innerHTML = "";

  list.forEach((a) => {
    const div = document.createElement("div");
    div.className = "agent-card";
    div.innerHTML = `
      <h4>${a.name}</h4>
      <p>部门：${a.department || "未分配"} <span class="badge ${a.status}">${a.status}</span></p>
      <p>当前任务：${a.currentTask || "-"}</p>
      <p>待办数量：${a.todoCount ?? 0}</p>
      <p>最近完成：${a.recentDone || "-"}</p>
      <p>耗时：${fmtSec(a.durationSec)} ｜ Token：${a.tokenUsed ?? 0}</p>
      <button>查看详情</button>
    `;
    div.querySelector("button").onclick = () => openDetail(a);
    wrap.appendChild(div);
  });
}

function taskLi(t) {
  const owner = t.owner ? ` @${t.owner}` : "";
  return `<li><strong>${t.title || "未命名任务"}</strong>${owner}<br/>状态:${t.status || "todo"} ｜ 优先级:${t.priority || "P2"}</li>`;
}

function renderBoard(data) {
  const b = data.taskBoard || { todo: [], doing: [], done: [] };
  $("todoList").innerHTML = (b.todo || []).map(taskLi).join("") || "<li>暂无</li>";
  $("doingList").innerHTML = (b.doing || []).map(taskLi).join("") || "<li>暂无</li>";
  $("doneList").innerHTML = (b.done || []).map(taskLi).join("") || "<li>暂无</li>";
}

function openDetail(agent) {
  $("detailTitle").textContent = `${agent.name} 详情`;
  $("detailMeta").textContent = `状态:${agent.status} ｜ 当前任务:${agent.currentTask} ｜ 待办:${agent.todoCount}`;
  const tasks = agent.tasks || [];
  $("detailTasks").innerHTML = tasks
    .map(
      (t) =>
        `<li>${t.title || "-"} ｜ 状态:${t.status || "-"} ｜ 耗时:${fmtSec(t.durationSec)} ｜ Token:${t.tokens ?? 0}</li>`
    )
    .join("") || "<li>暂无任务记录</li>";
  $("agentDetail").showModal();
}

async function loadData() {
  const res = await fetch(`/data/dashboard.json?t=${Date.now()}`);
  const data = await res.json();
  renderSummary(data);
  renderAgents(data);
  renderBoard(data);
}

async function refreshData() {
  const btn = $("refreshData");
  btn.disabled = true;
  btn.textContent = "刷新中...";
  try {
    const resp = await fetch("/api/refresh", { method: "POST" });
    if (!resp.ok) throw new Error("刷新失败");
    await loadData();
  } catch (e) {
    alert(`刷新失败：${e.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = "一键刷新数据";
  }
}

$("refreshData").onclick = refreshData;
$("closeDetail").onclick = () => $("agentDetail").close();
loadData();
