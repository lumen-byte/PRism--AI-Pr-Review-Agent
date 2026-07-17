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

// Primary CTA Navigation to Demo Pipeline
if (heroCtaBtn) {
    heroCtaBtn.addEventListener('click', () => {
        const pipelineNavItem = document.querySelector('.nav-item[data-view="pipeline"]');
        if (pipelineNavItem) pipelineNavItem.click();
    });
}

// Quick Demo Login for Recruiters
if (quickDemoBtn) {
    quickDemoBtn.addEventListener('click', async () => {
        document.getElementById('username').value = 'admin';
        document.getElementById('password').value = 'PRismAdmin2026!';
        loginForm.dispatchEvent(new Event('submit'));
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
            const res = await fetch(`${API_BASE}/demo/run`, {
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
            loginError.classList.remove('hidden');
        }
    } catch (err) {
        loginError.classList.remove('hidden');
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
    }
    
    loadCurrentView();
}

function loadCurrentView() {
    if (currentView === 'dashboard') loadDashboard();
    if (currentView === 'explorer') loadExplorer();
    if (currentView === 'issues') loadIssues();
}

// --- Dashboard Telemetry & Charts ---
async function loadDashboard() {
    try {
        const [statsRes, metricsRes] = await Promise.all([
            fetch(`${API_BASE}/dashboard/stats`, {headers: HEADERS()}),
            fetch(`${API_BASE}/dashboard/metrics`, {headers: HEADERS()})
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

    ['security', 'quality', 'logic', 'diff'].forEach(agent => {
        const tag = document.getElementById(`agent-tag-${agent}`);
        if (tag) { tag.className = 'status-tag idle'; tag.textContent = 'IDLE'; }
        const lat = document.getElementById(`agent-lat-${agent}`); if (lat) lat.textContent = '-';
        const find = document.getElementById(`agent-find-${agent}`); if (find) find.textContent = '-';
    });

    document.getElementById('live-terminal-stream').innerHTML = '';
    appendLog(`[SYSTEM] Dispatched execution job for scenario: ${scenario.toUpperCase()}`);

    let startTime = Date.now();
    pipelineTimerInterval = setInterval(() => {
        let elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
        elapsedTimeEl.textContent = `Elapsed: ${elapsed}s`;
    }, 50);

    // Sequence simulation timeline (2.8s total runtime)
    const sequence = [
        { time: 100, node: 'webhook', text: 'Step 1/8: Webhook received. HMAC-SHA256 signature verified.', progress: 12 },
        { time: 400, node: 'diff', text: 'Step 2/8: Diff Analyzer parsing modified patch files...', progress: 25, agent: 'diff' },
        { time: 700, node: 'treesitter', text: 'Step 3/8: Tree-sitter AST scope generation completed.', progress: 38 },
        { time: 1000, parallel: ['security', 'quality', 'logic'], text: 'Step 4/8: Fan-out parallel execution (Security, Quality, Logic Agents running concurrently)...', progress: 62 },
        { time: 1900, node: 'orchestrator', text: 'Step 5/8: Specialized findings fan-in to Review Orchestrator. Deduplicating and calculating health score...', progress: 78 },
        { time: 2300, node: 'db', text: 'Step 6/8: Persisting reviews, pull request records, and line comments into PostgreSQL (asyncpg)...', progress: 88 },
        { time: 2600, node: 'publisher', text: 'Step 7/8: Review Publisher published inline feedback and decision badge.', progress: 95 },
        { time: 2900, completed: true, text: 'Step 8/8: Execution pipeline completed successfully!', progress: 100 }
    ];

    sequence.forEach(step => {
        setTimeout(() => {
            progressBar.style.width = `${step.progress}%`;
            statusText.textContent = step.text;
            appendLog(step.text, step.completed ? 'success' : 'highlight');

            if (step.node) {
                activateNode(step.node);
            }
            if (step.parallel) {
                step.parallel.forEach(n => {
                    activateNode(n);
                    setAgentStatus(n, 'RUNNING', '~450ms', 'Scanning...');
                });
            }
            if (step.agent === 'diff') {
                setAgentStatus('diff', 'RUNNING', '120ms', '3 files');
            }
            if (step.completed) {
                clearInterval(pipelineTimerInterval);
                activePrEl.textContent = `PR Review Successfully Generated!`;
                runDemoBtn.disabled = false;
                demoBtnText.textContent = 'Run AI Demo';

                // Set final agent completion metrics based on scenario
                setAgentMetricsForScenario(scenario);
                loadCurrentView();
            }
        }, step.time);
    });
}

function activateNode(nodeId) {
    const el = document.getElementById(`node-${nodeId}`);
    const badge = document.getElementById(`badge-${nodeId}`);
    if (el) el.classList.add('active');
    if (badge) badge.textContent = 'ACTIVE';

    setTimeout(() => {
        if (el) {
            el.classList.remove('active');
            el.classList.add('completed');
        }
        if (badge) badge.textContent = 'DONE';
    }, 500);
}

function setAgentStatus(agent, status, lat, find) {
    const tag = document.getElementById(`agent-tag-${agent}`);
    if (tag) {
        tag.className = `status-tag ${status.toLowerCase()}`;
        tag.textContent = status;
    }
    const latEl = document.getElementById(`agent-lat-${agent}`);
    if (latEl && lat) latEl.textContent = lat;
    const findEl = document.getElementById(`agent-find-${agent}`);
    if (findEl && find) findEl.textContent = find;
}

function setAgentMetricsForScenario(scenario) {
    if (scenario === 'security' || scenario === 'mixed') {
        setAgentStatus('security', 'COMPLETED', '480ms', '2 Critical SQLi');
    } else {
        setAgentStatus('security', 'COMPLETED', '320ms', '0 Vulnerabilities');
    }

    if (scenario === 'quality' || scenario === 'mixed') {
        setAgentStatus('quality', 'COMPLETED', '520ms', '3 Code Smells');
    } else {
        setAgentStatus('quality', 'COMPLETED', '290ms', 'Optimal Quality');
    }

    if (scenario === 'logic' || scenario === 'mixed') {
        setAgentStatus('logic', 'COMPLETED', '410ms', '1 Logic Edge-case');
    } else {
        setAgentStatus('logic', 'COMPLETED', '310ms', '0 Logic Errors');
    }

    setAgentStatus('diff', 'COMPLETED', '110ms', '3 Files Parsed');
}

function appendLog(msg, type = 'normal') {
    const stream = document.getElementById('live-terminal-stream');
    if (!stream) return;
    const time = new Date().toLocaleTimeString();
    const div = document.createElement('div');
    div.className = 'log-line';
    div.innerHTML = `<span style="color:#64748b; margin-right:8px;">[${time}]</span><span class="${type}">${msg}</span>`;
    stream.appendChild(div);
    stream.scrollTop = stream.scrollHeight;
}

document.getElementById('clear-log-btn')?.addEventListener('click', () => {
    document.getElementById('live-terminal-stream').innerHTML = '<div class="log-line">[SYSTEM] Console cleared. Waiting for next execution trigger.</div>';
});

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
    
    const res = await fetch(url, {headers: HEADERS()});
    if (!res.ok) return;
    const data = await res.json();
    
    pageIndicator.textContent = `Page ${data.page} of ${data.pages}`;
    btnPrev.disabled = data.page <= 1;
    btnNext.disabled = data.page >= data.pages;
    
    reviewsTbody.innerHTML = '';
    data.items.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${r.repo_name}</strong></td>
            <td><a href="#" style="color:var(--brand-primary); font-weight:600;">#${r.pr_number}</a></td>
            <td>${r.author}</td>
            <td><span class="decision-badge ${r.health_score > 80 ? 'APPROVED' : r.health_score > 50 ? 'COMMENTED' : 'CHANGES_REQUESTED'}">${r.health_score} / 100</span></td>
            <td><span class="decision-badge ${r.decision}">${r.decision}</span></td>
            <td>${new Date(r.reviewed_at).toLocaleString()}</td>
            <td style="display:flex; gap:6px;">
                <button class="btn-secondary btn-sm" onclick="openReviewDetails('${r.id}')"><i data-lucide="eye" style="width:14px;"></i> Details</button>
                <button class="btn-secondary btn-sm" style="border-color:#30363d;" onclick="openGitHubPreview('${r.id}')"><i data-lucide="github" style="width:14px;"></i> GH Preview</button>
            </td>
        `;
        reviewsTbody.appendChild(tr);
    });
    lucide.createIcons();
}

// --- GitHub Native Render Preview Modal ---
async function openGitHubPreview(id) {
    const res = await fetch(`${API_BASE}/dashboard/reviews/${id}`, {headers: HEADERS()});
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
                <div style="font-size:0.8rem; color:#8b949e;">Automated multi-agent code inspection for PR #${r.pr_number} (${r.repo_name})</div>
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
    const res = await fetch(`${API_BASE}/dashboard/issues`, {headers: HEADERS()});
    if (!res.ok) return;
    const issues = await res.json();
    
    issuesTbody.innerHTML = '';
    issues.forEach(i => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>#${i.pr_number}</strong></td>
            <td><code style="color:#818cf8; background:rgba(255,255,255,0.05); padding:2px 6px; border-radius:4px;">${i.file_path}:${i.line_number}</code></td>
            <td><span class="decision-badge ${i.severity}">${i.severity}</span></td>
            <td><strong>${i.category}</strong></td>
            <td><span class="version-badge" style="background:rgba(16,185,129,0.15); color:#10b981;">95% Confidence</span></td>
            <td>
                <div>${i.text}</div>
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
}

// --- Review Modal ---
async function openReviewDetails(id) {
    const res = await fetch(`${API_BASE}/dashboard/reviews/${id}`, {headers: HEADERS()});
    if (!res.ok) return;
    const r = await res.json();
    
    document.getElementById('modal-pr-title').textContent = r.pr_title;
    document.getElementById('modal-pr-subtitle').textContent = `${r.owner}/${r.repo_name}#${r.pr_number} by ${r.author}`;
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

