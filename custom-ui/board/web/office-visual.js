// 办公室场景看板 - JavaScript功能

// 获取部门颜色
function getDepartmentColor(department) {
    const colors = {
        '中枢': '#9f7aea',
        '研发部': '#4299e1',
        '运营部': '#ed8936',
        '职能部': '#48bb78',
        '产品': '#f56565'
    };
    return colors[department] || '#718096';
}

// 获取部门图标
function getDepartmentIcon(department) {
    const icons = {
        '中枢': '👑',
        '研发部': '💻',
        '运营部': '📈',
        '职能部': '📊',
        '产品': '🎯'
    };
    return icons[department] || '🤖';
}

// 格式化时间
function formatTime(seconds) {
    const totalSeconds = Math.floor(Number(seconds || 0));
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

// 渲染统计数据
function renderStats(data) {
    const summary = data.summary || {};
    
    document.getElementById('totalAgents').textContent = summary.totalAgents || 0;
    document.getElementById('activeAgents').textContent = summary.activeAgents || 0;
    document.getElementById('doneAgents').textContent = summary.doneAgents || 0;
    document.getElementById('todoTasks').textContent = summary.todoItems || 0;
    document.getElementById('totalTokens').textContent = summary.totalTokens || 0;
    document.getElementById('totalTime').textContent = formatTime(summary.totalDurationSec);
    
    // 老板办公室数据
    document.getElementById('bossTotalAgents').textContent = summary.totalAgents || 0;
    document.getElementById('bossActiveAgents').textContent = summary.activeAgents || 0;
    document.getElementById('bossDoneAgents').textContent = summary.doneAgents || 0;
}

// 渲染工位
function renderWorkstations(data) {
    const agents = data.agents || [];
    const workstationsContainer = document.getElementById('workstations');
    
    if (agents.length === 0) {
        workstationsContainer.innerHTML = '<div class="loading">暂无员工信息</div>';
        return;
    }
    
    workstationsContainer.innerHTML = agents.map(agent => {
        const departmentColor = getDepartmentColor(agent.department);
        const departmentIcon = getDepartmentIcon(agent.department);
        const avatarColor = departmentColor;
        
        return `
            <div class="workstation" onclick="showAgentDetail('${agent.id}')">
                <div class="workstation-header">
                    <div class="agent-avatar" style="background: ${avatarColor}">
                        ${departmentIcon}
                    </div>
                    <div class="agent-info">
                        <h4>${agent.name}</h4>
                        <span class="agent-status ${agent.status === 'active' ? 'status-active' : 'status-done'}">
                            ${agent.status === 'active' ? '工作中' : '已完成'}
                        </span>
                    </div>
                </div>
                <div class="workstation-content">
                    <p><strong>部门：</strong>${agent.department || '未分配'}</p>
                    <p><strong>当前任务：</strong>${agent.currentTask || '无'}</p>
                    <p><strong>待办数量：</strong>${agent.todoCount || 0}</p>
                    <p><strong>最近完成：</strong>${agent.recentDone || '无'}</p>
                    <p><strong>工作时长：</strong>${formatTime(agent.durationSec)}</p>
                    <p><strong>Token消耗：</strong>${agent.tokenUsed || 0}</p>
                </div>
            </div>
        `;
    }).join('');
}

// 渲染任务看板
function renderKanban(data) {
    const todoList = document.getElementById('todoList');
    const doingList = document.getElementById('doingList');
    const doneList = document.getElementById('doneList');
    
    // 清空现有内容
    todoList.innerHTML = '';
    doingList.innerHTML = '';
    doneList.innerHTML = '';
    
    // 收集所有任务
    const allTasks = [];
    data.agents?.forEach(agent => {
        if (agent.tasks && agent.tasks.length > 0) {
            agent.tasks.forEach(task => {
                allTasks.push({
                    ...task,
                    owner: agent.name,
                    department: agent.department
                });
            });
        }
    });
    
    // 按状态分类任务
    allTasks.forEach(task => {
        const taskElement = document.createElement('div');
        taskElement.className = 'kanban-task';
        taskElement.innerHTML = `
            <strong>${task.title}</strong>
            <br>
            <small>@${task.owner} (${task.department})</small>
            <br>
            <small>优先级: ${task.priority || '未设置'}</small>
        `;
        
        if (task.status === 'todo') {
            todoList.appendChild(taskElement);
        } else if (task.status === 'doing') {
            doingList.appendChild(taskElement);
        } else if (task.status === 'done') {
            doneList.appendChild(taskElement);
        }
    });
}

// 显示Agent详情
function showAgentDetail(agentId) {
    // 这里可以实现一个弹窗显示更详细的Agent信息
    alert(`查看Agent ${agentId} 的详细信息`);
}

// 刷新数据 - 对接OpenClaw实时数据源
async function refreshData() {
    // 显示加载状态
    const workstations = document.getElementById('workstations');
    const originalContent = workstations.innerHTML;
    workstations.innerHTML = '<div class="loading">正在刷新数据...</div>';
    
    try {
        // 优先尝试从OpenClaw本地数据获取
        const response = await fetch('/data/dashboard.json?t=' + Date.now());
        if (!response.ok) {
            throw new Error('数据文件不存在');
        }
        const data = await response.json();
        
        // 渲染真实数据
        renderStats(data);
        renderWorkstations(data);
        renderKanban(data);
        
        // 显示成功消息
        showSuccessMessage('数据刷新成功！');
        
    } catch (error) {
        console.log('本地数据获取失败，尝试从OpenClaw API获取:', error);
        
        try {
            // 尝试从OpenClaw CLI获取实时数据
            const cliData = await fetchFromOpenClawCLI();
            if (cliData) {
                renderStats(cliData);
                renderWorkstations(cliData);
                renderKanban(cliData);
                showSuccessMessage('从OpenClaw实时数据获取成功！');
                return;
            }
        } catch (cliError) {
            console.log('OpenClaw CLI获取失败，使用示例数据:', cliError);
        }
        
        // 如果都失败，使用示例数据
        const sampleData = getSampleData();
        renderStats(sampleData);
        renderWorkstations(sampleData);
        renderKanban(sampleData);
        showSuccessMessage('使用示例数据展示');
    } finally {
        // 恢复原始内容
        setTimeout(() => {
            workstations.innerHTML = originalContent;
        }, 1000);
    }
}

// 从OpenClaw CLI获取实时数据
async function fetchFromOpenClawCLI() {
    try {
        // 尝试多种OpenClaw命令获取数据
        const commands = [
            'openclaw subagents list --json',
            'openclaw subagents list',
            'openclaw sessions list --json',
            'openclaw sessions list'
        ];
        
        for (const cmd of commands) {
            try {
                const response = await fetch(`/api/openclaw-exec?cmd=${encodeURIComponent(cmd)}`);
                if (response.ok) {
                    const result = await response.json();
                    return parseOpenClawOutput(result);
                }
            } catch (e) {
                console.log(`命令 ${cmd} 执行失败:`, e);
                continue;
            }
        }
        return null;
    } catch (error) {
        console.log('OpenClaw CLI获取失败:', error);
        return null;
    }
}

// 解析OpenClaw输出
function parseOpenClawOutput(output) {
    // 这里需要根据实际的OpenClaw输出格式进行解析
    // 目前返回一个示例结构
    return {
        generatedAt: new Date().toISOString(),
        source: "OpenClaw实时数据",
        summary: {
            totalAgents: output.length || 0,
            activeAgents: output.filter(a => a.status === 'active').length || 0,
            doneAgents: output.filter(a => a.status === 'done').length || 0,
            todoItems: output.reduce((sum, a) => sum + (a.todoCount || 0), 0),
            totalTokens: output.reduce((sum, a) => sum + (a.tokenUsed || 0), 0),
            totalDurationSec: output.reduce((sum, a) => sum + (a.durationSec || 0), 0)
        },
        agents: output.map(agent => ({
            id: agent.id || agent.name,
            name: agent.name,
            department: agent.department || mapDepartment(agent.name),
            status: agent.status || 'done',
            currentTask: agent.currentTask || '（空闲）',
            todoCount: agent.todoCount || 0,
            recentDone: agent.recentDone || '-',
            durationSec: agent.durationSec || 0,
            tokenUsed: agent.tokenUsed || 0,
            tasks: agent.tasks || []
        }))
    };
}

// 根据名称映射部门
function mapDepartment(name) {
    if (name.includes('研发') || name.includes('测试') || name.includes('运维')) return '研发部';
    if (name.includes('运营')) return '运营部';
    if (name.includes('产品') || name.includes('审核') || name.includes('尚书')) return '中枢';
    return '职能部';
}

// 获取示例数据
function getSampleData() {
    return {
        generatedAt: new Date().toISOString(),
        source: "示例数据",
        summary: {
            totalAgents: 5,
            activeAgents: 3,
            doneAgents: 2,
            todoItems: 4,
            doingItems: 2,
            doneItems: 6,
            totalTokens: 15230,
            totalDurationSec: 2450
        },
        agents: [
            {
                id: "main",
                name: "小麦",
                department: "中枢",
                status: "active",
                currentTask: "统筹全局工作",
                todoCount: 1,
                recentDone: "完成项目规划",
                durationSec: 1200,
                tokenUsed: 8500,
                tasks: [
                    { title: "统筹全局工作", status: "doing", priority: "P0" },
                    { title: "团队会议", status: "todo", priority: "P1" }
                ]
            },
            {
                id: "developer",
                name: "开发工程师",
                department: "研发部",
                status: "active",
                currentTask: "实现办公室看板",
                todoCount: 2,
                recentDone: "修复前端bug",
                durationSec: 800,
                tokenUsed: 4500,
                tasks: [
                    { title: "实现办公室看板", status: "doing", priority: "P0" },
                    { title: "优化性能", status: "todo", priority: "P2" },
                    { title: "代码审查", status: "done", priority: "P1" }
                ]
            },
            {
                id: "tester",
                name: "测试工程师",
                department: "研发部",
                status: "active",
                currentTask: "测试看板功能",
                todoCount: 1,
                recentDone: "编写测试用例",
                durationSec: 450,
                tokenUsed: 2230,
                tasks: [
                    { title: "测试看板功能", status: "doing", priority: "P0" },
                    { title: "回归测试", status: "todo", priority: "P1" }
                ]
            }
        ]
    };
}

// 显示成功消息
function showSuccessMessage(message) {
    const successMsg = document.createElement('div');
    successMsg.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #48bb78;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        z-index: 1000;
        font-size: 14px;
    `;
    successMsg.textContent = message;
    document.body.appendChild(successMsg);
    setTimeout(() => {
        if (document.body.contains(successMsg)) {
            document.body.removeChild(successMsg);
        }
    }, 2000);
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 自动加载数据
    refreshData();
    
    // 每30秒自动刷新一次
    setInterval(refreshData, 30000);
});