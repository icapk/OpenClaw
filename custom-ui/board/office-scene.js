// 3D办公场景看板 - JavaScript完整实现

class OfficeScene {
    constructor() {
        this.canvas = document.getElementById('officeCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.tooltip = document.getElementById('agentTooltip');
        
        this.agents = [];
        this.furniture = [];
        this.animationRunning = true;
        this.currentView = 'top';
        this.time = 0;
        
        this.setupCanvas();
        this.generateOfficeLayout();
        this.loadAgentData();
        this.animate();
        
        // 鼠标交互
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('click', (e) => this.handleClick(e));
        this.canvas.addEventListener('mouseleave', () => {
            this.tooltip.style.opacity = '0';
        });
    }

    setupCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        window.addEventListener('resize', () => {
            this.canvas.width = window.innerWidth;
            this.canvas.height = window.innerHeight;
            this.generateOfficeLayout();
        });
    }

    generateOfficeLayout() {
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        // 办公室家具布局
        this.furniture = [
            // 工作区域 - 4个工位
            { type: 'desk', x: width * 0.2, y: height * 0.3, width: 120, height: 80, color: '#8B4513' },
            { type: 'desk', x: width * 0.4, y: height * 0.3, width: 120, height: 80, color: '#8B4513' },
            { type: 'desk', x: width * 0.6, y: height * 0.3, width: 120, height: 80, color: '#8B4513' },
            { type: 'desk', x: width * 0.8, y: height * 0.3, width: 120, height: 80, color: '#8B4513' },
            
            // 休息区沙发
            { type: 'sofa', x: width * 0.1, y: height * 0.7, width: 200, height: 60, color: '#4169E1' },
            { type: 'sofa', x: width * 0.7, y: height * 0.7, width: 200, height: 60, color: '#4169E1' },
            
            // 会议桌
            { type: 'meeting', x: width * 0.5, y: height * 0.5, width: 150, height: 100, color: '#654321' },
            
            // 健身设备
            { type: 'fitness', x: width * 0.85, y: height * 0.1, width: 80, height: 80, color: '#FF6347' },
            
            // 老板办公室
            { type: 'boss', x: width * 0.05, y: height * 0.05, width: 150, height: 120, color: '#FFD700' },
            
            // 植物装饰
            { type: 'plant', x: width * 0.35, y: height * 0.15, width: 30, height: 30, color: '#228B22' },
            { type: 'plant', x: width * 0.75, y: height * 0.15, width: 30, height: 30, color: '#228B22' },
            
            // 饮水机
            { type: 'water', x: width * 0.5, y: height * 0.85, width: 40, height: 60, color: '#87CEEB' }
        ];
    }

    loadAgentData() {
        // 模拟真实Agent数据
        this.agents = [
            {
                id: 'main',
                name: '小麦',
                department: '中枢',
                status: 'working',
                task: '统筹全局工作',
                priority: 'high',
                x: this.canvas.width * 0.25,
                y: this.canvas.height * 0.35,
                targetX: this.canvas.width * 0.25,
                targetY: this.canvas.height * 0.35,
                color: '#e74c3c',
                avatar: '👑'
            },
            {
                id: 'developer',
                name: '开发工程师',
                department: '研发部',
                status: 'working',
                task: '实现办公室看板',
                priority: 'high',
                x: this.canvas.width * 0.45,
                y: this.canvas.height * 0.35,
                targetX: this.canvas.width * 0.45,
                targetY: this.canvas.height * 0.35,
                color: '#3498db',
                avatar: '💻'
            },
            {
                id: 'tester',
                name: '测试工程师',
                department: '研发部',
                status: 'working',
                task: '测试看板功能',
                priority: 'medium',
                x: this.canvas.width * 0.65,
                y: this.canvas.height * 0.35,
                targetX: this.canvas.width * 0.65,
                targetY: this.canvas.height * 0.35,
                color: '#f39c12',
                avatar: '🧪'
            },
            {
                id: 'product',
                name: '产品经理',
                department: '中枢',
                status: 'idle',
                task: '需求分析',
                priority: 'medium',
                x: this.canvas.width * 0.85,
                y: this.canvas.height * 0.35,
                targetX: this.canvas.width * 0.2,
                targetY: this.canvas.height * 0.75,
                color: '#9b59b6',
                avatar: '🧠'
            },
            {
                id: 'ops',
                name: '运营专员',
                department: '运营部',
                status: 'break',
                task: '内容策划',
                priority: 'low',
                x: this.canvas.width * 0.15,
                y: this.canvas.height * 0.75,
                targetX: this.canvas.width * 0.15,
                targetY: this.canvas.height * 0.75,
                color: '#1abc9c',
                avatar: '📈'
            },
            {
                id: 'data',
                name: '数据分析师',
                department: '职能部',
                status: 'working',
                task: '看板字段映射与对账规则',
                priority: 'medium',
                x: this.canvas.width * 0.85,
                y: this.canvas.height * 0.5,
                targetX: this.canvas.width * 0.85,
                targetY: this.canvas.height * 0.5,
                color: '#e67e22',
                avatar: '📊'
            }
        ];
        
        this.updateStats();
    }

    updateStats() {
        const total = this.agents.length;
        const active = this.agents.filter(a => a.status === 'working').length;
                const idle = this.agents.filter(a => a.status === 'idle' || a.status === 'break').length;
                const tasks = this.agents.filter(a => a.status === 'working').length;
                
                document.getElementById('totalAgents').textContent = total;
                document.getElementById('activeAgents').textContent = active;
                document.getElementById('idleAgents').textContent = idle;
                document.getElementById('totalTasks').textContent = tasks;
            }

            drawBackground() {
                // 渐变背景
                const gradient = this.ctx.createLinearGradient(0, 0, 0, this.canvas.height);
                gradient.addColorStop(0, '#87CEEB');
                gradient.addColorStop(1, '#E0F6FF');
                this.ctx.fillStyle = gradient;
                this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
                
                // 添加云朵效果
                this.ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                for (let i = 0; i < 5; i++) {
                    const x = (this.time * 0.5 + i * 200) % (this.canvas.width + 100) - 50;
                    const y = 50 + i * 30;
                    this.drawCloud(x, y);
                }
            }

            drawCloud(x, y) {
                this.ctx.beginPath();
                this.ctx.arc(x, y, 20, 0, Math.PI * 2);
                this.ctx.arc(x + 25, y, 30, 0, Math.PI * 2);
                this.ctx.arc(x + 50, y, 20, 0, Math.PI * 2);
                this.ctx.arc(x + 25, y - 15, 25, 0, Math.PI * 2);
                this.ctx.fill();
            }

            drawFloor() {
                // 绘制地板格子
                this.ctx.strokeStyle = 'rgba(255,255,255,0.3)';
                this.ctx.lineWidth = 1;
                
                const gridSize = 60;
                for (let x = 0; x < this.canvas.width; x += gridSize) {
                    this.ctx.beginPath();
                    this.ctx.moveTo(x, 0);
                    this.ctx.lineTo(x, this.canvas.height);
                    this.ctx.stroke();
                }
                
                for (let y = 0; y < this.canvas.height; y += gridSize) {
                    this.ctx.beginPath();
                    this.ctx.moveTo(0, y);
                    this.ctx.lineTo(this.canvas.width, y);
                    this.ctx.stroke();
                }
                
                // 地板阴影效果
                this.ctx.fillStyle = 'rgba(0,0,0,0.1)';
                for (let i = 0; i < 10; i++) {
                    const x = Math.random() * this.canvas.width;
                    const y = Math.random() * this.canvas.height;
                    this.ctx.fillRect(x, y, 40, 40);
                }
            }

            drawFurniture() {
                this.furniture.forEach(item => {
                    // 家具主体
                    this.ctx.fillStyle = item.color;
                    this.ctx.fillRect(item.x, item.y, item.width, item.height);
                    
                    // 家具阴影
                    this.ctx.fillStyle = 'rgba(0,0,0,0.3)';
                    this.ctx.fillRect(item.x + 5, item.y + 5, item.width, item.height);
                    
                    // 家具高光
                    this.ctx.fillStyle = 'rgba(255,255,255,0.2)';
                    this.ctx.fillRect(item.x, item.y, item.width, 5);
                    
                    // 家具标签
                    this.ctx.fillStyle = 'white';
                    this.ctx.font = 'bold 12px Arial';
                    this.ctx.textAlign = 'center';
                    
                    let label = '';
                    switch(item.type) {
                        case 'desk': label = '工位'; break;
                        case 'sofa': label = '沙发'; break;
                        case 'meeting': label = '会议室'; break;
                        case 'fitness': label = '健身区'; break;
                        case 'boss': label = '老板办公室'; break;
                        case 'plant': label = '🌿'; break;
                        case 'water': label = '💧'; break;
                    }
                    this.ctx.fillText(label, item.x + item.width/2, item.y + item.height/2);
                });
            }

            drawAgents() {
                this.agents.forEach(agent => {
                    // 平滑移动动画
                    const dx = agent.targetX - agent.x;
                    const dy = agent.targetY - agent.y;
                    agent.x += dx * 0.1;
                    agent.y += dy * 0.1;
                    
                    // 绘制Agent阴影
                    this.ctx.fillStyle = 'rgba(0,0,0,0.3)';
                    this.ctx.beginPath();
                    this.ctx.ellipse(agent.x, agent.y + 25, 15, 8, 0, 0, Math.PI * 2);
                    this.ctx.fill();
                    
                    // 绘制Agent身体（圆形）
                    this.ctx.fillStyle = agent.color;
                    this.ctx.beginPath();
                    this.ctx.arc(agent.x, agent.y, 25, 0, Math.PI * 2);
                    this.ctx.fill();
                    
                    // Agent边框
                    this.ctx.strokeStyle = 'white';
                    this.ctx.lineWidth = 3;
                    this.ctx.stroke();
                    
                    // 绘制Avatar
                    this.ctx.font = '20px Arial';
                    this.ctx.textAlign = 'center';
                    this.ctx.fillStyle = 'white';
                    this.ctx.fillText(agent.avatar, agent.x, agent.y + 7);
                    
                    // Agent名字背景
                    this.ctx.fillStyle = 'rgba(0,0,0,0.8)';
                    this.ctx.fillRect(agent.x - 30, agent.y - 45, 60, 15);
                    
                    // Agent名字
                    this.ctx.fillStyle = 'white';
                    this.ctx.font = 'bold 10px Arial';
                    this.ctx.textAlign = 'center';
                    this.ctx.fillText(agent.name, agent.x, agent.y - 35);
                    
                    // 任务状态背景
                    this.ctx.fillStyle = agent.status === 'working' ? '#2ecc71' : '#95a5a6';
                    this.ctx.fillRect(agent.x - 35, agent.y + 35, 70, 20);
                    
                    // 任务状态文字
                    this.ctx.fillStyle = 'white';
                    this.ctx.font = '8px Arial';
                    this.ctx.textAlign = 'center';
                    this.ctx.fillText(agent.task, agent.x, agent.y + 48);
                    
                    // 状态指示器
                    if (agent.status === 'working') {
                        this.ctx.fillStyle = agent.priority === 'high' ? '#e74c3c' : '#f39c12';
                        this.ctx.beginPath();
                        this.ctx.arc(agent.x + 30, agent.y - 30, 4, 0, Math.PI * 2);
                        this.ctx.fill();
                        
                        // 工作动画效果
                        if (this.time % 60 < 30) {
                            this.ctx.strokeStyle = agent.priority === 'high' ? '#e74c3c' : '#f39c12';
                            this.ctx.lineWidth = 2;
                            this.ctx.beginPath();
                            this.ctx.arc(agent.x, agent.y, 30, 0, Math.PI * 2);
                            this.ctx.stroke();
                        }
                    } else {
                        // 休息动画效果
                        this.ctx.fillStyle = '#95a5a6';
                        this.ctx.beginPath();
                        this.ctx.arc(agent.x, agent.y, 28, 0, Math.PI * 2);
                        this.ctx.stroke();
                    }
                });
            }

            drawParticles() {
                // 工作状态粒子效果
                this.agents.forEach(agent => {
                    if (agent.status === 'working') {
                        this.ctx.fillStyle = agent.priority === 'high' ? 'rgba(231, 76, 60, 0.6)' : 'rgba(243, 156, 18, 0.6)';
                        for (let i = 0; i < 3; i++) {
                            const angle = (this.time * 0.1 + i * 120) * Math.PI / 180;
                            const x = agent.x + Math.cos(angle) * 40;
                            const y = agent.y + Math.sin(angle) * 40;
                            this.ctx.beginPath();
                            this.ctx.arc(x, y, 2, 0, Math.PI * 2);
                            this.ctx.fill();
                        }
                    }
                });
            }

            handleMouseMove(e) {
                const rect = this.canvas.getBoundingClientRect();
                const mouseX = e.clientX - rect.left;
                const mouseY = e.clientY - rect.top;
                
                let hoveredAgent = null;
                this.agents.forEach(agent => {
                    const distance = Math.sqrt((mouseX - agent.x) ** 2 + (mouseY - agent.y) ** 2);
                    if (distance < 30) {
                        hoveredAgent = agent;
                    }
                });
                
                if (hoveredAgent) {
                    this.tooltip.innerHTML = `
                        <strong>${hoveredAgent.name}</strong><br>
                        部门: ${hoveredAgent.department}<br>
                        状态: ${hoveredAgent.status === 'working' ? '工作中' : '休息中'}<br>
                        任务: ${hoveredAgent.task}<br>
                        优先级: ${hoveredAgent.priority === 'high' ? '高' : hoveredAgent.priority === 'medium' ? '中' : '低'}
                    `;
                    this.tooltip.style.left = e.clientX + 10 + 'px';
                    this.tooltip.style.top = e.clientY + 10 + 'px';
                    this.tooltip.style.opacity = '1';
                    
                    // 改变鼠标样式
                    this.canvas.style.cursor = 'pointer';
                } else {
                    this.tooltip.style.opacity = '0';
                    this.canvas.style.cursor = 'default';
                }
            }

            handleClick(e) {
                const rect = this.canvas.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                const clickY = e.clientY - rect.top;
                
                this.agents.forEach(agent => {
                    const distance = Math.sqrt((clickX - agent.x) ** 2 + (clickY - agent.y) ** 2);
                    if (distance < 30) {
                        // 切换Agent状态
                        if (agent.status === 'working') {
                            agent.status = 'break';
                            agent.targetX = this.canvas.width * 0.2;
                            agent.targetY = this.canvas.height * 0.75;
                        } else {
                            agent.status = 'working';
                            agent.targetX = this.canvas.width * (0.2 + this.agents.indexOf(agent) * 0.2);
                            agent.targetY = this.canvas.height * 0.35;
                        }
                        this.updateStats();
                    }
                });
            }

            animate() {
                if (!this.animationRunning) {
                    requestAnimationFrame(() => this.animate());
                    return;
                }
                
                // 清空画布
                this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                
                // 绘制场景
                this.drawBackground();
                this.drawFloor();
                this.drawFurniture();
                this.drawAgents();
                this.drawParticles();
                
                // 更新时间
                this.time++;
                
                requestAnimationFrame(() => this.animate());
            }

            toggleAnimation() {
                this.animationRunning = !this.animationRunning;
            }

            refreshData() {
                this.loadAgentData();
            }

            changeView() {
                // 这里可以实现视角切换功能
                this.currentView = this.currentView === '