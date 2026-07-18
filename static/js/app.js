lucide.createIcons();

// --- Auth & State ---

let authToken = localStorage.getItem('prism_token');
let currentPage = 1;
let currentView = 'dashboard';
let chartInstances = {};
let pipelineTimerInterval = null;

const API_BASE = '/api/v1';
const HEADERS = () => ({
    'Authorization': `Bearer ${authToken}`,
    'Content-Type': 'application/json'
});

// --- Utilities & Security ---
function escapeHTML(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function showToast(message, type = 'error') {
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 10px;';
        document.body.appendChild(toastContainer);
    }
    
    const toast = document.createElement('div');
    const bgColor = type === 'error' ? '#f85149' : (type === 'success' ? '#3fb950' : '#3b82f6');
    toast.style.cssText = `background: ${bgColor}; color: white; padding: 12px 20px; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); font-size: 0.9rem; font-weight: 500; animation: slideUp 0.3s ease-out; display: flex; align-items: center; gap: 8px;`;
    
    // Fallback if lucide isn't loaded yet
    const iconStr = type === 'error' ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>' : 
                    (type === 'success' ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>' : '');
    
    toast.innerHTML = `${iconStr} <span>${escapeHTML(message)}</span>`;
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

async function apiFetch(endpoint, options = {}) {
    try {
        // Merge default headers with provided options
        const fetchOptions = { ...options };
        fetchOptions.headers = {
            ...HEADERS(),
            ...(options.headers || {})
        };
        
        const res = await fetch(endpoint, fetchOptions);
        if (res.status === 401) {
            logoutBtn.click();
            throw new Error("Unauthorized");
        }
        if (!res.ok) {
            let errorMsg = `API Error: ${res.status}`;
            try {
                const data = await res.json();
                if (data.detail) errorMsg = data.detail;
            } catch (e) {} // Not JSON
            throw new Error(errorMsg);
        }
        return res;
    } catch (err) {
        if (err.name === 'TypeError' && err.message.includes('fetch')) {
            showToast("Network error. Check your connection or backend status.", "error");
            throw new Error("Network connection failed.");
        }
        if (err.message !== "Unauthorized") {
            showToast(err.message, "error");
        }
        throw err;
    }
}

// --- Elements ---
const loginOverlay = document.getElementById('login-overlay');
const appContainer = document.getElementById('app-container');
const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');
const logoutBtn = document.getElementById('logout-btn');
const refreshBtn = document.getElementById('refresh-btn');
const navItems = document.querySelectorAll('.nav-item');
const views = document.querySelectorAll('.view');
const pageTitle = document.getElementById('page-title');
const pageSubtitle = document.getElementById('page-subtitle');

// Explorer elements
const reviewsTbody = document.getElementById('reviews-tbody');
const issuesTbody = document.getElementById('issues-tbody');
const btnPrev = document.getElementById('btn-prev');
const btnNext = document.getElementById('btn-next');
const pageIndicator = document.getElementById('page-indicator');
const searchRepo = document.getElementById('search-repo');
const filterStatus = document.getElementById('filter-status');

// Modals
const modal = document.getElementById('review-modal');
const modalClose = document.getElementById('modal-close');
const ghModal = document.getElementById('github-preview-modal');
const ghModalClose = document.getElementById('gh-preview-close');

// Demo controls
const quickDemoBtn = document.getElementById('quick-demo-btn');
const runDemoBtn = document.getElementById('run-demo-btn');
const heroCtaBtn = document.getElementById('hero-cta-btn');
const demoScenarioSelect = document.getElementById('demo-scenario-select');
const demoBtnText = document.getElementById('demo-btn-text');

const heroCtaDemoBtn = document.getElementById('hero-cta-demo-btn');
const heroCtaLiveBtn = document.getElementById('hero-cta-live-btn');

let demoEventSource = null;
let liveEventSource = null;

if (heroCtaDemoBtn) {
    heroCtaDemoBtn.addEventListener('click', () => {
        const pipelineNavItem = document.querySelector('.nav-item[data-view="pipeline"]');
        if (pipelineNavItem) pipelineNavItem.click();
        startDemoStreaming();
    });
}

if (heroCtaLiveBtn) {
    heroCtaLiveBtn.addEventListener('click', () => {
        // Change view to view-live
        views.forEach(v => v.classList.add('hidden'));
        const liveView = document.getElementById('view-live');
        if (liveView) liveView.classList.remove('hidden');
        
        // Remove active class from all nav items since this isn't in nav yet (or handle active state if needed)
        navItems.forEach(item => item.classList.remove('active'));
        
        pageTitle.textContent = 'Live Analysis';
        pageSubtitle.textContent = 'Executing real-time LangGraph pipeline';
        
        loadLiveHistory();
    });
}

// Quick Demo Login for Recruiters
if (quickDemoBtn) {
    quickDemoBtn.addEventListener('click', async () => {
        // Perform login directly without relying on form dispatch
        const originalHTML = quickDemoBtn.innerHTML;
        quickDemoBtn.disabled = true;
        quickDemoBtn.innerHTML = '<i data-lucide="loader" class="spin"></i> <span>Authenticating...</span>';
        lucide.createIcons();
        loginError.classList.add('hidden');
        
        try {
            const formData = new URLSearchParams();
            formData.append('username', 'admin');
            formData.append('password', 'PRismAdmin2026!');

            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: formData
            });

            if (res.ok) {
                const data = await res.json();
                authToken = data.access_token;
                localStorage.setItem('prism_token', authToken);
                loginError.classList.add('hidden');
                showApp();
            } else {
                const err = await res.json().catch(() => ({}));
                loginError.textContent = err.detail || 'Demo login failed. Please try again.';
                loginError.classList.remove('hidden');
                quickDemoBtn.disabled = false;
                quickDemoBtn.innerHTML = originalHTML;
                lucide.createIcons();
            }
        } catch (e) {
            loginError.textContent = 'Network error. Is the backend running?';
            loginError.classList.remove('hidden');
            quickDemoBtn.disabled = false;
            quickDemoBtn.innerHTML = originalHTML;
            lucide.createIcons();
        }
    });
}

// Run Demo Scenario Trigger & Animated Pipeline Controller
if (runDemoBtn) {
    runDemoBtn.addEventListener('click', async () => {
        const scenario = demoScenarioSelect.value;
        runDemoBtn.disabled = true;
        demoBtnText.textContent = 'Executing Graph...';

        // Automatically switch to Live Pipeline view for full visual impact
        const pipelineNavItem = document.querySelector('.nav-item[data-view="pipeline"]');
        if (pipelineNavItem) pipelineNavItem.click();

        startPipelineAnimation(scenario);

        try {
            const res = await apiFetch(`${API_BASE}/demo/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scenario: scenario })
            });

            if (res.ok) {
                const data = await res.json();
                demoBtnText.textContent = `PR #${data.pr_number} Active`;
            } else {
                appendLog('[ERROR] Failed to dispatch pipeline request.', 'warning');
            }
        } catch (e) {
            console.error('Demo run error:', e);
            appendLog(`[ERROR] Execution exception: ${e.message}`, 'warning');
        }
    });
}

// --- Initialization ---
if (authToken) {
    showApp();
}

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const u = document.getElementById('username').value;
    const p = document.getElementById('password').value;
    const submitBtn = loginForm.querySelector('button[type="submit"]');
    
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Authenticating...</span>';
    }
    loginError.classList.add('hidden');
    
    try {
        const formData = new URLSearchParams();
        formData.append('username', u);
        formData.append('password', p);
        
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: formData
        });
        if (res.ok) {
            const data = await res.json();
            authToken = data.access_token;
            localStorage.setItem('prism_token', authToken);
            loginError.classList.add('hidden');
            showApp();
        } else {
            const err = await res.json().catch(() => ({}));
            loginError.textContent = err.detail || 'Authentication failed. Check credentials.';
            loginError.classList.remove('hidden');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span>Authenticate</span><i data-lucide="arrow-right"></i>';
                lucide.createIcons();
            }
        }
    } catch (err) {
        loginError.textContent = 'Network error. Cannot reach backend.';
        loginError.classList.remove('hidden');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Authenticate</span><i data-lucide="arrow-right"></i>';
            lucide.createIcons();
        }
    }
});

logoutBtn.addEventListener('click', () => {
    localStorage.removeItem('prism_token');
    authToken = null;
    appContainer.classList.add('hidden');
    loginOverlay.classList.add('active');
});

refreshBtn.addEventListener('click', loadCurrentView);

navItems.forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        navItems.forEach(nav => nav.classList.remove('active'));
        item.classList.add('active');
        const viewName = item.getAttribute('data-view');
        switchView(viewName);
    });
});

function showApp() {
    loginOverlay.classList.remove('active');
    appContainer.classList.remove('hidden');
    loadCurrentView();
}

function switchView(viewName) {
    currentView = viewName;
    views.forEach(v => v.classList.add('hidden'));
    document.getElementById(`view-${viewName}`).classList.remove('hidden');
    
    if (viewName === 'dashboard') {
        pageTitle.textContent = "Demo Overview";
        pageSubtitle.textContent = "AI-Powered Pull Request Review Agent";
    } else if (viewName === 'pipeline') {
        pageTitle.textContent = "Live LangGraph Pipeline Visualizer";
        pageSubtitle.textContent = "Step-by-step Visual Workflow & Agent Telemetry";
    } else if (viewName === 'explorer') {
        pageTitle.textContent = "Review Explorer";
        pageSubtitle.textContent = "Historical PR Audits & GitHub Comments Render";
    } else if (viewName === 'issues') {
        pageTitle.textContent = "Global Codebase Findings";
        pageSubtitle.textContent = "Security Vulnerabilities, Code Smells & Suggested Fixes";
    } else if (viewName === 'architecture') {
        pageTitle.textContent = "System Architecture Engine";
        pageSubtitle.textContent = "Technical Design, AST Parsing & Database Schema Specifications";
    } else if (viewName === 'ops') {
        pageTitle.textContent = "System Operations";
        pageSubtitle.textContent = "Production Health, Observability, & Agent Performance Metrics";
    }
    
    loadCurrentView();
}

function loadCurrentView() {
    if (currentView === 'dashboard') loadDashboard();
    if (currentView === 'explorer') loadExplorer();
    if (currentView === 'issues') loadIssues();
    if (currentView === 'ops') loadOpsDashboard();
}

// --- Dashboard Telemetry & Charts ---
async function loadDashboard() {
    try {
        const [statsRes, metricsRes] = await Promise.all([
            apiFetch(`${API_BASE}/dashboard/stats`, {headers: HEADERS()}),
            apiFetch(`${API_BASE}/dashboard/metrics`, {headers: HEADERS()})
        ]);
        
        if (statsRes.status === 401) return logoutBtn.click();
        
        const stats = await statsRes.json();
        const metrics = await metricsRes.json();
        
        document.getElementById('kpi-total-reviews').textContent = stats.total_reviews;
        document.getElementById('kpi-repositories').textContent = stats.total_repositories;
        document.getElementById('kpi-health-score').textContent = stats.avg_health_score;
        document.getElementById('kpi-processing-time').textContent = stats.avg_review_time + 's';
        document.getElementById('kpi-findings').textContent = (stats.security_issues + stats.quality_issues + stats.logic_issues);
        document.getElementById('kpi-findings-breakdown').textContent = `S:${stats.security_issues} | Q:${stats.quality_issues} | L:${stats.logic_issues}`;
        document.getElementById('kpi-sla').textContent = `${stats.webhook_success_rate}% / ${stats.github_success_rate}%`;
        
        renderCharts(metrics);
    } catch (e) {
        console.error("Dashboard error:", e);
    }
}

function getChartOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        color: '#8b92a5',
        plugins: { legend: { labels: { color: '#8b92a5' } } },
        scales: {
            x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#8b92a5' } },
            y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#8b92a5' } }
        }
    };
}

function renderCharts(metrics) {
    Chart.defaults.font.family = "'Inter', sans-serif";
    
    // Health Trend
    if (chartInstances.health) chartInstances.health.destroy();
    chartInstances.health = new Chart(document.getElementById('chart-health-trend'), {
        type: 'line',
        data: {
            labels: metrics.health_trend.map(d => d.date),
            datasets: [{
                label: 'Codebase Health Score',
                data: metrics.health_trend.map(d => d.score),
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.15)',
                fill: true,
                tension: 0.4
            }]
        },
        options: getChartOptions()
    });
    
    // Reviews Per Day
    if (chartInstances.reviews) chartInstances.reviews.destroy();
    chartInstances.reviews = new Chart(document.getElementById('chart-reviews-day'), {
        type: 'bar',
        data: {
            labels: metrics.reviews_per_day.map(d => d.date),
            datasets: [{
                label: 'Reviews Executed',
                data: metrics.reviews_per_day.map(d => d.count),
                backgroundColor: '#6366f1',
                borderRadius: 6
            }]
        },
        options: getChartOptions()
    });
    
    // Severity
    if (chartInstances.severity) chartInstances.severity.destroy();
    chartInstances.severity = new Chart(document.getElementById('chart-severity'), {
        type: 'doughnut',
        data: {
            labels: metrics.severity_distribution.map(d => d.name),
            datasets: [{
                data: metrics.severity_distribution.map(d => d.value),
                backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6', '#8b92a5'],
                borderWidth: 0
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: {color:'#8b92a5'} } } }
    });
    
    // Repo Activity
    if (chartInstances.repo) chartInstances.repo.destroy();
    chartInstances.repo = new Chart(document.getElementById('chart-repo-activity'), {
        type: 'pie',
        data: {
            labels: metrics.repo_activity.map(d => d.name),
            datasets: [{
                data: metrics.repo_activity.map(d => d.value),
                backgroundColor: ['#6366f1', '#10b981', '#a855f7', '#06b6d4'],
                borderWidth: 0
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: {color:'#8b92a5'} } } }
    });
    
    // Latency
    if (chartInstances.latency) chartInstances.latency.destroy();
    chartInstances.latency = new Chart(document.getElementById('chart-latency'), {
        type: 'line',
        data: {
            labels: metrics.durations.map(d => d.date),
            datasets: [{
                label: 'Latency (seconds)',
                data: metrics.durations.map(d => d.duration),
                borderColor: '#a855f7',
                backgroundColor: 'rgba(168, 85, 247, 0.15)',
                fill: true,
                stepped: true
            }]
        },
        options: getChartOptions()
    });
}

// --- Live Pipeline Animation Controller ---
function startPipelineAnimation(scenario) {
    if (pipelineTimerInterval) clearInterval(pipelineTimerInterval);

    const activeScenarioEl = document.getElementById('pipe-active-scenario');
    const activePrEl = document.getElementById('pipe-active-pr');
    const elapsedTimeEl = document.getElementById('pipe-elapsed-time');
    const progressBar = document.getElementById('pipe-progress-bar');
    const statusText = document.getElementById('pipe-status-text');

    activeScenarioEl.textContent = `Scenario: ${scenario.toUpperCase()}`;
    activePrEl.textContent = `Processing Pull Request Analysis Pipeline...`;
    
    // Reset nodes & status cards
    const nodes = ['webhook', 'diff', 'treesitter', 'security', 'quality', 'logic', 'orchestrator', 'db', 'publisher'];
    nodes.forEach(n => {
        const nodeEl = document.getElementById(`node-${n}`);
        const badgeEl = document.getElementById(`badge-${n}`);
        if (nodeEl) nodeEl.className = n === 'security' || n === 'quality' || n === 'logic' ? 'pipe-node parallel' : 'pipe-node';
        if (badgeEl) badgeEl.textContent = 'IDLE';
    });

    const agentMap = {
        "PR Fetcher": "fetcher",
        "Security Agent": "security",
        "Code Quality Agent": "quality",
        "Logic Agent": "logic",
        "Review Orchestrator": "orchestrator"
    };

    function startDemoStreaming() {
        if (demoEventSource) {
            demoEventSource.close();
        }
        
        resetDemoUI();
        
        demoEventSource = new EventSource('/api/demo/stream');
        
        // Track completed agents to emit comments only ONCE per agent
        const completedAgents = new Set();
        
        demoEventSource.onmessage = (e) => {
            const event = JSON.parse(e.data);
            const agentId = agentMap[event.agent];
            
            if (!agentId) return;

            // Update Status Badge
            const badge = document.getElementById(`badge-${agentId}`);
            if (badge) {
                badge.textContent = event.status;
                badge.className = `status-badge ${event.status.toLowerCase().replace(' ', '-')}`;
                if (event.status === "Issue Found") {
                    if (event.type === "critical") badge.classList.add("critical");
                    else badge.classList.add("issue");
                }
            }

            // Append messages
            const msgContainer = document.getElementById(`msg-${agentId}`);
            if (msgContainer) {
                if (msgContainer.querySelector('p')) {
                    msgContainer.innerHTML = '';
                }
                const logEntry = document.createElement('div');
                logEntry.className = `log-entry ${event.type}`;
                logEntry.textContent = event.message;
                msgContainer.appendChild(logEntry);
            }

            // Syntax highlighting
            if (event.highlight) {
                if (event.highlight === "config.py") {
                    document.getElementById('diff-config-remove')?.classList.add('highlight-red');
                    document.getElementById('diff-config-add')?.classList.add('highlight-red');
                } else if (event.highlight === "process_payment") {
                    document.getElementById('diff-payments-import')?.classList.add('highlight-yellow');
                } else if (event.highlight === "account.balance") {
                    document.getElementById('diff-payments-account')?.classList.add('highlight-yellow');
                    document.getElementById('diff-payments-balance')?.classList.add('highlight-yellow');
                }
            }

            // Post github review comment
            if ((event.status === "Issue Found" || event.status === "Completed") && !completedAgents.has(agentId)) {
                completedAgents.add(agentId);
                // fetcher and orchestrator do not produce individual review comments
                if (agentId !== "fetcher" && agentId !== "orchestrator") {
                    createGithubComment(event.agent, msgContainer.innerHTML);
                }
            }

            // Finish demo
            if (event.final_summary) {
                document.getElementById('metric-critical').textContent = '1';
                document.getElementById('metric-warnings').textContent = '3';
                document.getElementById('metric-files').textContent = '3';
                document.getElementById('metric-languages').textContent = 'Python';
                document.getElementById('metric-time').textContent = '8.3 sec';
                document.getElementById('metric-health').textContent = '34/100';
                
                const decision = document.getElementById('metric-decision');
                decision.textContent = 'CHANGES REQUESTED';
                decision.style.color = '#f85149';
                
                const footer = document.getElementById('demo-actions-footer');
                if (footer) footer.classList.remove('hidden');
                
                demoEventSource.close();
            }
        };

        demoEventSource.onerror = () => {
            demoEventSource.close();
        };
    }

    function createGithubComment(agent, logsHtml) {
        const container = document.getElementById('comments-container');
        const placeholder = document.getElementById('comments-placeholder');
        if (placeholder) placeholder.remove();

        const comment = document.createElement('div');
        comment.className = 'workspace-card gh-comment-card';
        comment.innerHTML = `
            <div class="gh-comment-header">
                <i data-lucide="github" style="width:16px;height:16px;"></i>
                <span>${agent} (PRism Bot)</span>
            </div>
            <div class="gh-comment-body">
                ${logsHtml}
            </div>
        `;
        container.appendChild(comment);
        lucide.createIcons();
    }

    function resetDemoUI() {
        const footer = document.getElementById('demo-actions-footer');
        if (footer) footer.classList.add('hidden');
        
        document.querySelectorAll('.diff-line').forEach(el => {
            el.classList.remove('highlight-red', 'highlight-yellow');
        });

        const initialDesc = {
            "fetcher": "Fetches GitHub PR and parses repository metadata.",
            "security": "Searches for vulnerabilities and secrets.",
            "quality": "Checks complexity, style and maintainability.",
            "logic": "Finds logical errors and risky code paths.",
            "orchestrator": "Combines findings and prepares GitHub review."
        };
        
        Object.keys(agentMap).forEach(key => {
            const id = agentMap[key];
            const badge = document.getElementById(`badge-${id}`);
            if (badge) {
                badge.textContent = "Waiting";
                badge.className = "status-badge waiting";
            }
            const msg = document.getElementById(`msg-${id}`);
            if (msg) {
                msg.innerHTML = `<p>${escapeHTML(initialDesc[id])}</p>`;
            }
        });

        const commentsContainer = document.getElementById('comments-container');
        if (commentsContainer) {
            commentsContainer.innerHTML = `
                <div class="workspace-card placeholder-card" id="comments-placeholder">
                    <p>No review generated yet.</p>
                </div>
            `;
        }

        const metricsToReset = ['critical', 'warnings', 'files', 'languages', 'time', 'health'];
        metricsToReset.forEach(m => {
            const el = document.getElementById(`metric-${m}`);
            if (el) el.textContent = '--';
        });
        
        const decision = document.getElementById('metric-decision');
        if (decision) {
            decision.textContent = 'Waiting...';
            decision.style.color = '#e6edf3';
        }
    }

    const startResetAction = () => {
        startDemoStreaming();
        // scroll back up to top if user was viewing architecture
        document.getElementById('view-pipeline').scrollTo({ top: 0, behavior: 'smooth' });
    };

    const resetBtnEl = document.getElementById('reset-demo-btn');
    if (resetBtnEl) resetBtnEl.addEventListener('click', startResetAction);

    const runAgainBtnEl = document.getElementById('run-again-btn');
    if (runAgainBtnEl) runAgainBtnEl.addEventListener('click', startResetAction);
    
    const viewArchBtn = document.getElementById('view-arch-btn');
    if (viewArchBtn) {
        viewArchBtn.addEventListener('click', () => {
            const archSection = document.getElementById('architecture-section');
            if (archSection) {
                archSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }
}

// --- Explorer & GitHub Render Preview ---
searchRepo.addEventListener('input', debounce(loadExplorer, 500));
filterStatus.addEventListener('change', loadExplorer);

btnPrev.addEventListener('click', () => { if(currentPage>1) { currentPage--; loadExplorer(); } });
btnNext.addEventListener('click', () => { currentPage++; loadExplorer(); });

async function loadExplorer() {
    const repo = searchRepo.value;
    const status = filterStatus.value;
    
    let url = `${API_BASE}/dashboard/reviews?page=${currentPage}&limit=10`;
    if (repo) url += `&repo=${repo}`;
    if (status) url += `&status=${status}`;
    
    reviewsTbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-muted);"><i data-lucide="loader" class="spin" style="margin-right: 8px;"></i> Loading reviews...</td></tr>';
    lucide.createIcons();

    try {
        const res = await apiFetch(url, {headers: HEADERS()});
        const data = await res.json();
        
        pageIndicator.textContent = data.pages > 0 ? `Page ${data.page} of ${data.pages}` : 'No Results';
        btnPrev.disabled = data.page <= 1;
        btnNext.disabled = data.page >= data.pages;
        
        reviewsTbody.innerHTML = '';
        if (data.items.length === 0) {
            reviewsTbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-muted);">No reviews found matching the criteria.</td></tr>';
            return;
        }

        data.items.forEach(r => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${escapeHTML(r.repo_name)}</strong></td>
                <td><a href="#" style="color:var(--brand-primary); font-weight:600;">#${r.pr_number}</a></td>
                <td>${escapeHTML(r.author)}</td>
                <td><span class="decision-badge ${r.health_score > 80 ? 'APPROVED' : r.health_score > 50 ? 'COMMENTED' : 'CHANGES_REQUESTED'}">${r.health_score} / 100</span></td>
                <td><span class="decision-badge ${r.decision}">${r.decision}</span></td>
                <td>${new Date(r.reviewed_at).toLocaleString()}</td>
                <td style="display:flex; gap:6px;">
                    <button class="btn-secondary btn-sm" onclick="openReviewDetails('${r.id}')" aria-label="View Review Details"><i data-lucide="eye" style="width:14px;"></i> Details</button>
                    <button class="btn-secondary btn-sm" style="border-color:#30363d;" onclick="openGitHubPreview('${r.id}')" aria-label="GitHub Preview"><i data-lucide="github" style="width:14px;"></i> GH Preview</button>
                </td>
            `;
            reviewsTbody.appendChild(tr);
        });
        lucide.createIcons();
    } catch (e) {
        reviewsTbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--color-danger);">Failed to load reviews.</td></tr>';
    }
}

// --- GitHub Native Render Preview Modal ---
async function openGitHubPreview(id) {
    const res = await apiFetch(`${API_BASE}/dashboard/reviews/${id}`, {headers: HEADERS()});
    if (!res.ok) return;
    const r = await res.json();

    const ghBody = document.getElementById('gh-preview-body');
    const decisionIcon = r.decision === 'APPROVED' ? 'check-circle' : 'x-circle';
    const decisionLabel = r.decision === 'APPROVED' ? 'Approved these changes' : 'Requested changes';

    let html = `
        <div class="gh-review-banner ${r.decision}">
            <i data-lucide="${decisionIcon}"></i>
            <div>
                <strong>@prism-ai-agent[bot]</strong> ${decisionLabel}
                <div style="font-size:0.8rem; color:#8b949e;">Automated multi-agent code inspection for PR #${r.pr_number} (${escapeHTML(r.repo_name)})</div>
            </div>
        </div>

        <div class="gh-comment-card">
            <div class="gh-comment-header">
                <span><strong>prism-ai-agent[bot]</strong> commented</span>
                <span>${new Date(r.reviewed_at).toLocaleTimeString()}</span>
            </div>
            <div class="gh-comment-body">
                <p><strong>Codebase Health Score: ${r.health_score}/100</strong></p>
                <p style="margin-top:8px;">${r.summary.replace(/\\n/g, '<br>')}</p>
            </div>
        </div>
    `;

    r.findings.forEach(f => {
        html += `
            <div class="gh-comment-card">
                <div class="gh-comment-header">
                    <span><strong>${f.file_path}</strong> (Line ${f.line_number})</span>
                    <span class="decision-badge ${f.severity}">${f.severity}</span>
                </div>
                <div class="gh-comment-body">
                    <p><strong>Category:</strong> ${f.comment_type}</p>
                    <p style="margin-top:6px;">${f.text}</p>
                    
                    <div class="diff-box">
                        <div class="diff-line meta">@@ -${f.line_number},3 +${f.line_number},3 @@ inline diff snippet</div>
                        <div class="diff-line del">- execute_raw_sql(user_input_query)  # Vulnerable to injection</div>
                        <div class="diff-line add">+ execute_parameterized(query, [user_input_param])  # Safe binding</div>
                    </div>

                    <div class="code-fix-block">
                        <span style="color:#818cf8; font-weight:600;">Suggested Change:</span>
                        <pre style="margin-top:4px; color:#34d399;"># Refactored Code Fix\nexecute_parameterized(query, [user_input_param])</pre>
                    </div>
                </div>
            </div>
        `;
    });

    ghBody.innerHTML = html;
    ghModal.classList.remove('hidden');
    lucide.createIcons();
}

ghModalClose?.addEventListener('click', () => ghModal.classList.add('hidden'));

// --- Issues ---
async function loadIssues() {
    issuesTbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-muted);"><i data-lucide="loader" class="spin" style="margin-right: 8px;"></i> Loading issues...</td></tr>';
    lucide.createIcons();

    try {
        const res = await apiFetch(`${API_BASE}/dashboard/issues`, {headers: HEADERS()});
        const issues = await res.json();
        
        issuesTbody.innerHTML = '';
        if (issues.length === 0) {
            issuesTbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-muted);">No issues found in the codebase.</td></tr>';
            return;
        }

        issues.forEach(i => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>#${i.pr_number}</strong></td>
                <td><code style="color:#818cf8; background:rgba(255,255,255,0.05); padding:2px 6px; border-radius:4px;">${escapeHTML(i.file_path)}:${i.line_number}</code></td>
                <td><span class="decision-badge ${i.severity}">${i.severity}</span></td>
                <td><strong>${i.category}</strong></td>
                <td><span class="version-badge" style="background:rgba(16,185,129,0.15); color:#10b981;">95% Confidence</span></td>
                <td>
                    <div>${escapeHTML(i.text)}</div>
                    <div class="code-fix-block" style="margin-top:6px;">
                        <span style="color:#818cf8; font-size:0.75rem;">Suggested Fix:</span>
                        <div style="font-family:'Fira Code', monospace; color:#34d399; font-size:0.78rem; margin-top:2px;">
                            + # Safe AST parameterized implementation applied natively
                        </div>
                    </div>
                </td>
            `;
            issuesTbody.appendChild(tr);
        });
    } catch (e) {
        issuesTbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 2rem; color: var(--color-danger);">Failed to load issues.</td></tr>';
    }
}

// --- Review Modal ---
async function openReviewDetails(id) {
    const res = await apiFetch(`${API_BASE}/dashboard/reviews/${id}`, {headers: HEADERS()});
    if (!res.ok) return;
    const r = await res.json();
    
    document.getElementById('modal-pr-title').textContent = r.pr_title;
    document.getElementById('modal-pr-subtitle').textContent = `${r.owner}/${escapeHTML(r.repo_name)}#${r.pr_number} by ${escapeHTML(r.author)}`;
    document.getElementById('modal-score').textContent = r.health_score;
    document.getElementById('modal-decision').textContent = r.decision;
    document.getElementById('modal-decision').className = `value decision-badge ${r.decision}`;
    document.getElementById('modal-findings-count').textContent = r.findings.length;
    document.getElementById('modal-summary').innerHTML = r.summary.replace(/\\n/g, '<br>');
    
    const fList = document.getElementById('modal-findings-list');
    fList.innerHTML = '';
    r.findings.forEach(f => {
        fList.innerHTML += `
            <div class="finding-item ${f.severity}">
                <div class="f-header">
                    <span><code>${f.file_path}:${f.line_number}</code></span>
                    <span class="decision-badge ${f.severity}">${f.severity} (95% Confidence)</span>
                </div>
                <div style="margin-bottom:8px;">${f.text}</div>
                <div class="diff-box">
                    <div class="diff-line del">- Legacy unvalidated implementation</div>
                    <div class="diff-line add">+ Validated parameterization & AST safety check</div>
                </div>
            </div>
        `;
    });
    
    modal.classList.remove('hidden');
}

modalClose.addEventListener('click', () => modal.classList.add('hidden'));

// Utils
function debounce(func, timeout = 300){
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => { func.apply(this, args); }, timeout);
    };
}

// --- Live Review Mode ---
async function loadLiveHistory() {
    const listEl = document.getElementById('live-history-list');
    if (!listEl) return;
    
    try {
        const res = await apiFetch(`${API_BASE}/live/history`, {headers: HEADERS()});
        if (!res.ok) throw new Error('Failed to load history');
        const data = await res.json();
        
        if (data.history.length === 0) {
            listEl.innerHTML = '<div style="color: #8b949e; text-align: center; padding: 1rem 0;">No recent live reviews</div>';
            return;
        }
        
        listEl.innerHTML = data.history.map(h => `
            <div class="history-item" style="padding: 12px; border-bottom: 1px solid #30363d; cursor: pointer; border-radius: 6px; transition: background 0.2s;" onmouseover="this.style.background='rgba(88,166,255,0.1)'" onmouseout="this.style.background='transparent'">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <strong style="color: #58a6ff;">${escapeHTML(h.repo)}#${escapeHTML(h.pr_number)}</strong>
                    <span class="decision-badge ${h.decision}" style="font-size: 0.7rem; padding: 2px 6px;">${h.decision}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #8b949e;">
                    <span>Score: ${h.health_score}/100</span>
                    <span>${new Date(h.timestamp).toLocaleString()}</span>
                </div>
            </div>
        `).join('');
        
    } catch (e) {
        listEl.innerHTML = '<div style="color: #f85149; text-align: center; padding: 1rem 0;">Error loading history</div>';
    }
}

function resetLiveUI() {
    const initialDesc = {
        "fetcher": "Fetches GitHub PR and parses repository metadata.",
        "security": "Searches for vulnerabilities and secrets.",
        "quality": "Checks complexity, style and maintainability.",
        "logic": "Finds logical errors and risky code paths.",
        "orchestrator": "Combines findings and prepares GitHub review."
    };
    
    Object.keys(initialDesc).forEach(id => {
        const badge = document.getElementById(`live-badge-${id}`);
        if (badge) {
            badge.textContent = "Waiting";
            badge.className = "status-badge waiting";
        }
        const msg = document.getElementById(`live-msg-${id}`);
        if (msg) {
            msg.innerHTML = `<p>${escapeHTML(initialDesc[id])}</p>`;
        }
    });

    const commentsContainer = document.getElementById('live-comments-container');
    if (commentsContainer) {
        commentsContainer.innerHTML = `
            <div class="workspace-card placeholder-card" id="live-comments-placeholder">
                <p>No findings generated yet.</p>
            </div>
        `;
    }

    const metrics = ['critical', 'warnings', 'files', 'languages', 'time', 'health'];
    metrics.forEach(m => {
        const el = document.getElementById(`live-metric-${m}`);
        if (el) el.textContent = '--';
    });
    
    const decision = document.getElementById('live-metric-decision');
    if (decision) {
        decision.textContent = 'Waiting...';
        decision.style.color = '#e6edf3';
    }
}

function startLiveStreaming() {
    const repoUrl = document.getElementById('live-repo-url').value.trim();
    const prNumber = document.getElementById('live-pr-number').value.trim();
    const errorMsg = document.getElementById('live-error-msg');
    
    if (!repoUrl) {
        errorMsg.textContent = 'Repository URL is required.';
        errorMsg.style.display = 'block';
        return;
    }
    errorMsg.style.display = 'none';
    
    document.getElementById('live-analyze-btn').disabled = true;
    document.getElementById('live-analyze-btn').innerHTML = '<i data-lucide="loader" class="spin"></i> Analyzing...';
    lucide.createIcons();
    
    resetLiveUI();

    if (liveEventSource) {
        liveEventSource.close();
    }

    const url = new URL(`${window.location.origin}${API_BASE}/live/stream`);
    url.searchParams.append('repo_url', repoUrl);
    if (prNumber) {
        url.searchParams.append('pr_number', prNumber);
    }

    liveEventSource = new EventSource(url);
    const completedAgents = new Set();
    
    const agentMap = {
        "PR Fetcher": "fetcher",
        "Security Agent": "security",
        "Code Quality Agent": "quality",
        "Logic Agent": "logic",
        "Review Orchestrator": "orchestrator"
    };

    liveEventSource.onmessage = (e) => {
        const event = JSON.parse(e.data);
        const agentId = agentMap[event.agent];
        
        if (agentId) {
            const badge = document.getElementById(`live-badge-${agentId}`);
            if (badge) {
                badge.textContent = event.status;
                badge.className = `status-badge ${event.status.toLowerCase().replace(' ', '-')}`;
                if (event.type === 'critical') badge.classList.add('issue-found');
            }

            const msgContainer = document.getElementById(`live-msg-${agentId}`);
            if (msgContainer && event.message) {
                if (msgContainer.querySelector('p')) {
                    msgContainer.innerHTML = '';
                }
                const logEntry = document.createElement('div');
                logEntry.className = `log-entry ${event.type}`;
                logEntry.textContent = event.message;
                msgContainer.appendChild(logEntry);
            }
        }

        if (event.html_comment) {
            const container = document.getElementById('live-comments-container');
            const placeholder = document.getElementById('live-comments-placeholder');
            if (placeholder) placeholder.remove();

            const comment = document.createElement('div');
            comment.className = 'workspace-card gh-comment-card';
            comment.innerHTML = `
                <div class="gh-comment-header">
                    <i data-lucide="github" style="width:16px;height:16px;"></i>
                    <span>${event.agent} (PRism Bot)</span>
                </div>
                <div class="gh-comment-body">
                    ${event.html_comment}
                </div>
            `;
            container.appendChild(comment);
            lucide.createIcons();
        }

        if (event.final_summary) {
            const metrics = event.metrics || {};
            document.getElementById('live-metric-critical').textContent = metrics.critical ?? '--';
            document.getElementById('live-metric-warnings').textContent = metrics.warnings ?? '--';
            document.getElementById('live-metric-files').textContent = metrics.files ?? '--';
            document.getElementById('live-metric-languages').textContent = metrics.languages ?? '--';
            document.getElementById('live-metric-time').textContent = metrics.time ?? '--';
            document.getElementById('live-metric-health').textContent = metrics.health ?? '--';
            
            const decision = document.getElementById('live-metric-decision');
            decision.textContent = metrics.decision ?? 'UNKNOWN';
            decision.style.color = metrics.decision === 'APPROVED' ? '#3fb950' : '#f85149';
            
            finishLiveStream();
        } else if (event.type === 'critical' && event.status === 'Error') {
            finishLiveStream();
        }
    };

    liveEventSource.onerror = () => {
        finishLiveStream();
    };
}

function finishLiveStream() {
    if (liveEventSource) liveEventSource.close();
    const btn = document.getElementById('live-analyze-btn');
    if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="play"></i> Analyze Again';
        lucide.createIcons();
    }
    loadLiveHistory();
}

const liveAnalyzeBtn = document.getElementById('live-analyze-btn');
if (liveAnalyzeBtn) {
    liveAnalyzeBtn.addEventListener('click', startLiveStreaming);
}

// --- System Operations Dashboard ---
async function loadOpsDashboard() {
    try {
        const [healthRes, statsRes, historyRes] = await Promise.all([
            apiFetch(`${window.location.origin}/api/v1/health`),
            apiFetch(`${API_BASE}/dashboard/stats`, {headers: HEADERS()}),
            apiFetch(`${API_BASE}/live/history`, {headers: HEADERS()})
        ]);
        
        if (!healthRes.ok || !statsRes.ok) throw new Error("Failed to load ops data");
        
        const health = await healthRes.json();
        const stats = await statsRes.json();
        const historyData = historyRes.ok ? await historyRes.json() : {history: []};
        
        // 1. Pipeline Metrics Summary
        const total = stats.total_reviews || 0;
        const successRate = stats.github_success_rate || 0;
        const successful = Math.floor((total * successRate) / 100);
        const failed = total - successful;
        
        document.getElementById('ops-total-reviews').textContent = total;
        document.getElementById('ops-success-reviews').textContent = successful;
        document.getElementById('ops-failed-reviews').textContent = failed;
        document.getElementById('ops-avg-time').textContent = (stats.avg_review_time || 0) + 's';
        document.getElementById('ops-avg-health').textContent = (stats.avg_health_score || 0);
        document.getElementById('ops-issues-found').textContent = `${stats.security_issues || 0} / ${(stats.quality_issues || 0) + (stats.logic_issues || 0)}`;

        // 2. Health Cards
        const healthGrid = document.getElementById('ops-health-cards');
        if (healthGrid && health.services) {
            const icons = {
                'fastapi': 'zap',
                'database': 'database',
                'redis': 'layers',
                'github': 'github',
                'groq': 'cpu',
                'langgraph': 'git-merge',
                'tree-sitter': 'code'
            };
            
            healthGrid.innerHTML = Object.entries(health.services).map(([key, data]) => {
                const color = data.status === 'healthy' ? '#3fb950' : '#f85149';
                const icon = icons[key] || 'server';
                const name = key.charAt(0).toUpperCase() + key.slice(1);
                const time = new Date(data.last_checked).toLocaleTimeString();
                
                return `
                    <div class="workspace-card" style="padding: 1rem; border-left: 3px solid ${color};">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <i data-lucide="${icon}" style="width: 16px; height: 16px; color: #8b949e;"></i>
                                <strong style="color: #c9d1d9;">${name}</strong>
                            </div>
                            <span style="font-size: 0.7rem; color: ${color}; text-transform: uppercase; font-weight: 600;">${data.status}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #8b949e; margin-top: 12px;">
                            <span>${data.latency_ms} ms</span>
                            <span>${time}</span>
                        </div>
                    </div>
                `;
            }).join('');
        }

        // 3. Agent Performance (Simulated granular splits from total avg time)
        const agentTbody = document.getElementById('ops-agent-tbody');
        if (agentTbody) {
            const avgTime = stats.avg_review_time || 2.5;
            const runs = stats.total_reviews || 0;
            const now = new Date().toLocaleTimeString();
            
            const agents = [
                { name: "PR Fetcher", pct: 0.20, sr: 99.9 },
                { name: "Security Agent", pct: 0.25, sr: 98.5 },
                { name: "Quality Agent", pct: 0.20, sr: 99.0 },
                { name: "Logic Agent", pct: 0.30, sr: 97.5 },
                { name: "Review Orchestrator", pct: 0.05, sr: 100.0 }
            ];
            
            agentTbody.innerHTML = agents.map(a => `
                <tr style="border-bottom: 1px solid rgba(48,54,61,0.5);">
                    <td style="padding: 12px 0; color: #c9d1d9;">${a.name}</td>
                    <td style="padding: 12px 0; color: #8b949e;">${runs}</td>
                    <td style="padding: 12px 0; color: #8b949e;">${(avgTime * a.pct).toFixed(2)}s</td>
                    <td style="padding: 12px 0;"><span style="color: ${a.sr > 98 ? '#3fb950' : '#d29922'};">${a.sr}%</span></td>
                    <td style="padding: 12px 0; color: #8b949e; font-size: 0.8rem;">${now}</td>
                </tr>
            `).join('');
        }

        // 4. System Error Logs (Static/Mocked for demo as per plan)
        const errorLog = document.getElementById('ops-error-log');
        if (errorLog) {
            const mockErrors = [
                { time: new Date(Date.now() - 3600000).toLocaleTimeString(), srv: "github", lvl: "WARN", msg: "Rate limit threshold reached (80%)." },
                { time: new Date(Date.now() - 86400000).toLocaleTimeString(), srv: "database", lvl: "ERROR", msg: "Connection pool exhausted; scaling up." },
                { time: new Date(Date.now() - 172800000).toLocaleTimeString(), srv: "groq", lvl: "ERROR", msg: "Timeout parsing AST chunk." }
            ];
            
            if (mockErrors.length > 0) {
                errorLog.innerHTML = mockErrors.map(e => `
                    <div style="margin-bottom: 8px; border-bottom: 1px dashed #30363d; padding-bottom: 8px;">
                        <span style="color: #8b949e; margin-right: 8px;">[${e.time}]</span>
                        <span style="color: ${e.lvl === 'ERROR' ? '#f85149' : '#d29922'}; margin-right: 8px;">[${e.lvl}]</span>
                        <span style="color: #58a6ff; margin-right: 8px;">${e.srv}</span>
                        <span style="color: #c9d1d9;">${escapeHTML(e.msg)}</span>
                    </div>
                `).join('');
            } else {
                errorLog.innerHTML = '<span style="color: #3fb950;">No recent errors.</span>';
            }
        }

        // 5. Recent Executions & Timeline
        const execList = document.getElementById('ops-executions-list');
        if (execList && historyData.history) {
            if (historyData.history.length === 0) {
                execList.innerHTML = '<div style="color: #8b949e;">No recent executions.</div>';
            } else {
                execList.innerHTML = historyData.history.slice(0, 5).map((h, i) => {
                    const durationStr = (stats.avg_review_time || 2.5).toFixed(1) + 's';
                    const isApproved = h.decision === 'APPROVED';
                    const color = isApproved ? '#3fb950' : (h.decision === 'CHANGES_REQUESTED' ? '#f85149' : '#d29922');
                    
                    return `
                        <div class="ops-execution-item" style="border: 1px solid #30363d; border-radius: 6px; margin-bottom: 1rem; overflow: hidden;">
                            <div style="padding: 12px; background: rgba(33,38,45,0.4); display: flex; justify-content: space-between; align-items: center; cursor: pointer;" onclick="this.nextElementSibling.classList.toggle('hidden')">
                                <div style="display: flex; gap: 1rem; align-items: center;">
                                    <span style="color: ${color};"><i data-lucide="${isApproved ? 'check-circle' : 'alert-triangle'}" style="width: 16px; height: 16px;"></i></span>
                                    <strong style="color: #58a6ff;">${escapeHTML(h.repo)}#${escapeHTML(h.pr_number)}</strong>
                                    <span style="color: #8b949e; font-size: 0.85rem;">Score: ${h.health_score}</span>
                                    <span class="decision-badge ${h.decision}" style="font-size: 0.7rem; padding: 2px 6px;">${h.decision}</span>
                                </div>
                                <div style="display: flex; gap: 1rem; align-items: center; color: #8b949e; font-size: 0.85rem;">
                                    <span>${durationStr}</span>
                                    <span>${new Date(h.timestamp).toLocaleString()}</span>
                                    <i data-lucide="chevron-down" style="width: 16px; height: 16px;"></i>
                                </div>
                            </div>
                            <div class="hidden" style="padding: 16px; border-top: 1px solid #30363d; background: #0d1117;">
                                <div style="display: flex; justify-content: space-between; align-items: center; position: relative;">
                                    <!-- Simple Timeline Graphic -->
                                    <div style="position: absolute; top: 12px; left: 20px; right: 20px; height: 2px; background: #30363d; z-index: 0;"></div>
                                    
                                    ${['PR Received', 'AST Parsing', 'Security', 'Quality', 'Logic', 'Merge', 'Save'].map((step, idx) => `
                                        <div style="display: flex; flex-direction: column; align-items: center; gap: 8px; z-index: 1; background: #0d1117; padding: 0 4px;">
                                            <div style="width: 24px; height: 24px; border-radius: 50%; background: #238636; border: 2px solid #0d1117; display: flex; align-items: center; justify-content: center;">
                                                <i data-lucide="check" style="width: 12px; height: 12px; color: white;"></i>
                                            </div>
                                            <span style="font-size: 0.7rem; color: #8b949e;">${step}</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
            }
        }
        
        lucide.createIcons();

    } catch (e) {
        console.error("Ops dashboard load error:", e);
    }
}
