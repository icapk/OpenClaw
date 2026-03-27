  // Complete the error handling and auto-refresh
    setTimeout(() => {
      errorToast.remove();
    }, 5000);
  }

  startAutoRefresh() {
    // Auto refresh every 30 seconds
    setInterval(() => {
      this.loadData();
    }, 30000);
  }

  cleanup() {
    // Clean up event listeners and animations
    if (this.performanceMonitor) {
      this.performanceMonitor.animationEnabled = false;
    }
    
    // Remove event listeners
    $$('button').forEach(btn => {
      btn.replaceWith(btn.cloneNode(true));
    });
    
    // Clear cache
    this.cacheManager.clear();
  }

  // Utility functions
  fmtSec(sec = 0) {
    const s = Math.floor(Number(sec || 0));
    const m = Math.floor(s / 60);
    const r = s % 60;
    return `${m}m ${r}s`;
  }

  statItem(label, value) {
    return `<div class="stat"><span>${label}</span><strong>${value}</strong></div>`;
  }

  taskLi(t) {
    const owner = t.owner ? ` @${t.owner}` : "";
    return `<li><strong>${t.title || "未命名任务"}</strong>${owner}<br/>状态:${t.status || "todo"} ｜ 优先级:${t.priority || "P2"}</li>`;
  }
}

// Initialize the dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const dashboard = new OfficeDashboard();
  
  // Add CSS for error toast animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
  `;
  document.head.appendChild(style);
  
  // Make dashboard globally available for debugging
  window.dashboard = dashboard;
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = OfficeDashboard;
}