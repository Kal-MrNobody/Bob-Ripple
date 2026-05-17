// API Configuration
const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://bob-ripple.onrender.com';

// State
let currentRepoUrl = '';
let riskDonutChart = null;
let fileBarChart = null;
let prRiskDonutChart = null;

// DOM Elements
const heroSection = document.getElementById('heroSection');
const heroRepoInput = document.getElementById('heroRepoInput');
const repoUrlInput = document.getElementById('repoUrlInput');
const prNumberInput = document.getElementById('prNumberInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const repoNamePill = document.getElementById('repoNamePill');
const healthBar = document.getElementById('healthBar');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingMessage = document.getElementById('loadingMessage');
const dashboard = document.getElementById('dashboard');

// Metric elements
const healthGrade = document.getElementById('healthGrade');
const sourceFiles = document.getElementById('sourceFiles');
const testFiles = document.getElementById('testFiles');
const testCoverage = document.getElementById('testCoverage');

// Chart elements
const riskDonutCanvas = document.getElementById('riskDonutChart');
const riskCenterText = document.getElementById('riskCenterText');
const fileBarCanvas = document.getElementById('fileBarChart');

// Data elements
const fragileFilesContainer = document.getElementById('fragileFilesContainer');
const untestedModulesContainer = document.getElementById('untestedModulesContainer');
const topRisksList = document.getElementById('topRisksList');
const recommendationsList = document.getElementById('recommendationsList');

// PR elements
const prResultsPanel = document.getElementById('prResultsPanel');
const prPlaceholder = document.getElementById('prPlaceholder');
const prResults = document.getElementById('prResults');
const prRiskBadge = document.getElementById('prRiskBadge');
const prTitle = document.getElementById('prTitle');
const prSummary = document.getElementById('prSummary');
const affectedFilesContainer = document.getElementById('affectedFilesContainer');
const prRiskDonutCanvas = document.getElementById('prRiskDonutChart');
const prRiskCenterText = document.getElementById('prRiskCenterText');
const staleTestsList = document.getElementById('staleTestsList');
const staleDocsList = document.getElementById('staleDocsList');

/**
 * Initialize event listeners
 */
analyzeBtn.addEventListener('click', handleAnalyze);

repoUrlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleAnalyze();
    }
});

prNumberInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleAnalyze();
    }
});

// Example repo pill buttons
document.querySelectorAll('.example-pill').forEach(btn => {
    btn.addEventListener('click', () => {
        const repoUrl = btn.dataset.repo;
        repoUrlInput.value = repoUrl;
        heroRepoInput.value = repoUrl;
        handleAnalyze();
    });
});

// Hero input sync with navbar input
heroRepoInput.addEventListener('input', (e) => {
    repoUrlInput.value = e.target.value;
});

heroRepoInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleAnalyze();
    }
});

// Sync navbar input back to hero input
repoUrlInput.addEventListener('input', (e) => {
    heroRepoInput.value = e.target.value;
});

/**
 * Handle unified analysis - runs both scan and PR analysis if PR number provided
 */
async function handleAnalyze() {
    const repoUrl = repoUrlInput.value.trim();
    const prNumber = parseInt(prNumberInput.value);
    
    if (!repoUrl) {
        alert('Please enter a repository URL');
        return;
    }
    
    // Hide hero section on first analysis
    heroSection.classList.add('hidden');
    
    currentRepoUrl = repoUrl;
    
    // Determine loading message
    const hasPR = prNumber && prNumber > 0;
    const message = hasPR
        ? `Analyzing repository + PR #${prNumber}...`
        : 'Analyzing repository...';
    
    showLoading(message);
    
    try {
        if (hasPR) {
            // Run both API calls in parallel
            const [scanData, prData] = await Promise.all([
                fetchScan(repoUrl),
                fetchPRAnalysis(repoUrl, prNumber)
            ]);
            
            // Populate both sections
            populateDashboard(scanData);
            displayPRResults(prData);
        } else {
            // Only run scan
            const scanData = await fetchScan(repoUrl);
            populateDashboard(scanData);
            
            // Show PR placeholder
            prResultsPanel.classList.add('active');
            prPlaceholder.classList.remove('hidden');
            prResults.classList.remove('active');
        }
        
    } catch (error) {
        console.error('Analysis error:', error);
        hideLoading();
        alert(`Error: ${error.message}`);
    }
}

/**
 * Fetch repository scan data
 */
async function fetchScan(repoUrl) {
    const response = await fetch(`${API_BASE}/scan`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ repo_url: repoUrl })
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Scan failed: ${response.status}`);
    }
    
    return await response.json();
}

/**
 * Fetch PR analysis data
 */
async function fetchPRAnalysis(repoUrl, prNumber) {
    const response = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            repo_url: repoUrl,
            pr_number: prNumber
        })
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `PR analysis failed: ${response.status}`);
    }
    
    return await response.json();
}

/**
 * Populate dashboard with scan results
 */
function populateDashboard(data) {
    // Update repo name pill
    if (data.repo_name) {
        repoNamePill.textContent = data.repo_name;
        repoNamePill.classList.add('active');
    }
    
    // Update health bar
    const grade = (data.health_score || 'unknown').toLowerCase();
    healthBar.className = `health-bar grade-${grade} active`;
    
    // Metrics
    healthGrade.textContent = grade.toUpperCase();
    healthGrade.className = `metric-value health-grade grade-${grade}`;
    
    const sourceCount = data.source_files_count || 0;
    const testCount = data.test_files_count || 0;
    const coverage = sourceCount > 0 ? Math.round((testCount / sourceCount) * 100) : 0;
    
    sourceFiles.textContent = sourceCount;
    testFiles.textContent = testCount;
    testCoverage.textContent = `${coverage}%`;
    
    // Risk Distribution Chart
    createRiskDonutChart(data.fragile_files || []);
    
    // File Breakdown Chart
    createFileBarChart(
        sourceCount,
        testCount,
        data.doc_files_count || 0
    );
    
    // Fragile Files
    displayFragileFiles(data.fragile_files || []);
    
    // Untested Modules
    displayUntestedModules(data.untested_modules || []);
    
    // Top Risks
    displayList(topRisksList, data.top_risks || [], 'No risks identified');
    
    // Recommendations
    displayList(recommendationsList, data.recommendations || [], 'No recommendations');
    
    // Show dashboard
    hideLoading();
    dashboard.classList.add('active');
    
    // Scroll to dashboard
    dashboard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Create risk distribution donut chart
 */
function createRiskDonutChart(fragileFiles) {
    // Count by risk level
    const riskCounts = {
        high: 0,
        medium: 0,
        low: 0
    };
    
    fragileFiles.forEach(file => {
        const risk = (file.risk || 'medium').toLowerCase();
        if (riskCounts.hasOwnProperty(risk)) {
            riskCounts[risk]++;
        }
    });
    
    const total = riskCounts.high + riskCounts.medium + riskCounts.low;
    riskCenterText.textContent = total;
    
    // Destroy existing chart
    if (riskDonutChart) {
        riskDonutChart.destroy();
    }
    
    // Create new chart
    riskDonutChart = new Chart(riskDonutCanvas, {
        type: 'doughnut',
        data: {
            labels: ['High Risk', 'Medium Risk', 'Low Risk'],
            datasets: [{
                data: [riskCounts.high, riskCounts.medium, riskCounts.low],
                backgroundColor: ['#da1e28', '#f1c21b', '#42be65'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#3d2618',
                    titleColor: '#f9f3eb',
                    bodyColor: '#d4b89a',
                    borderColor: '#d4965f',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.parsed}`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create file breakdown bar chart
 */
function createFileBarChart(sourceCount, testCount, docCount) {
    // Destroy existing chart
    if (fileBarChart) {
        fileBarChart.destroy();
    }
    
    // Create new chart
    fileBarChart = new Chart(fileBarCanvas, {
        type: 'bar',
        data: {
            labels: ['Source Files', 'Test Files', 'Doc Files'],
            datasets: [{
                data: [sourceCount, testCount, docCount],
                backgroundColor: ['#0062ff', '#42be65', '#6929c4'],
                borderRadius: 4,
                borderWidth: 0
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#3d2618',
                    titleColor: '#f9f3eb',
                    bodyColor: '#d4b89a',
                    borderColor: '#d4965f',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.x} files`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        color: '#d4b89a',
                        font: {
                            family: 'Inter'
                        }
                    },
                    grid: {
                        color: 'rgba(212, 150, 95, 0.15)'
                    }
                },
                y: {
                    ticks: {
                        color: '#d4b89a',
                        font: {
                            family: 'Inter'
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Display fragile files
 */
function displayFragileFiles(files) {
    if (!files || files.length === 0) {
        fragileFilesContainer.innerHTML = '<div class="empty-state">No fragile files detected</div>';
        return;
    }
    
    const displayFiles = files.slice(0, 8);
    const hasMore = files.length > 8;
    
    let html = displayFiles.map(file => {
        const risk = (file.risk || 'medium').toLowerCase();
        return `
            <div class="fragile-file-row">
                <div class="file-info">
                    <div class="file-path">${escapeHtml(file.path)}</div>
                    <div class="file-reason">${escapeHtml(file.reason)}</div>
                </div>
                <div class="risk-badge ${risk}">${risk}</div>
            </div>
        `;
    }).join('');
    
    if (hasMore) {
        html += `<div class="show-all-link">+ ${files.length - 8} more files</div>`;
    }
    
    fragileFilesContainer.innerHTML = html;
}

/**
 * Display untested modules
 */
function displayUntestedModules(modules) {
    if (!modules || modules.length === 0) {
        untestedModulesContainer.innerHTML = '<div class="empty-state success">Full test coverage detected</div>';
        return;
    }
    
    const html = modules.map(module => 
        `<div class="module-pill">${escapeHtml(module)}</div>`
    ).join('');
    
    untestedModulesContainer.innerHTML = html;
}

/**
 * Display a numbered list
 */
function displayList(container, items, emptyMessage) {
    if (!items || items.length === 0) {
        container.innerHTML = `<li class="empty-state" style="list-style: none; border: none; padding: 2rem;">${emptyMessage}</li>`;
        return;
    }
    
    const html = items.map(item => 
        `<li>${escapeHtml(item)}</li>`
    ).join('');
    
    container.innerHTML = html;
}

/**
 * Display PR analysis results
 */
function displayPRResults(data) {
    // Hide placeholder, show results
    prPlaceholder.classList.add('hidden');
    prResults.classList.add('active');
    prResultsPanel.classList.add('active');
    
    // Risk badge
    const risk = (data.risk_score || 'medium').toLowerCase();
    prRiskBadge.textContent = `${risk.toUpperCase()} RISK`;
    prRiskBadge.className = `pr-risk-badge ${risk}`;
    
    // Title and summary
    prTitle.textContent = data.pr_title || `Pull Request #${data.pr_number}`;
    prSummary.textContent = data.summary || 'No summary available.';
    
    // Affected files
    displayAffectedFiles(data.affected_files || []);
    
    // PR risk donut chart
    createPRRiskDonutChart(data.affected_files || []);
    
    // Stale tests and docs
    displayPRList(staleTestsList, data.stale_tests || [], 'No tests need updates');
    displayPRList(staleDocsList, data.stale_docs || [], 'No docs need updates');
}

/**
 * Display affected files
 */
function displayAffectedFiles(files) {
    if (!files || files.length === 0) {
        affectedFilesContainer.innerHTML = '<div class="empty-state">No affected files detected</div>';
        return;
    }
    
    const html = files.map(file => {
        const impact = (file.impact || 'medium').toLowerCase();
        return `
            <div class="affected-file-row">
                <div class="affected-file-header">
                    <div class="affected-file-path">${escapeHtml(file.path)}</div>
                    <div class="risk-badge ${impact}">${impact}</div>
                </div>
                <div class="affected-file-reason">${escapeHtml(file.reason)}</div>
            </div>
        `;
    }).join('');
    
    affectedFilesContainer.innerHTML = html;
}

/**
 * Create PR risk donut chart
 */
function createPRRiskDonutChart(affectedFiles) {
    // Count by impact level
    const impactCounts = {
        high: 0,
        medium: 0,
        low: 0
    };
    
    affectedFiles.forEach(file => {
        const impact = (file.impact || 'medium').toLowerCase();
        if (impactCounts.hasOwnProperty(impact)) {
            impactCounts[impact]++;
        }
    });
    
    const total = impactCounts.high + impactCounts.medium + impactCounts.low;
    prRiskCenterText.textContent = total;
    
    // Destroy existing chart
    if (prRiskDonutChart) {
        prRiskDonutChart.destroy();
    }
    
    // Create new chart
    prRiskDonutChart = new Chart(prRiskDonutCanvas, {
        type: 'doughnut',
        data: {
            labels: ['High Impact', 'Medium Impact', 'Low Impact'],
            datasets: [{
                data: [impactCounts.high, impactCounts.medium, impactCounts.low],
                backgroundColor: ['#da1e28', '#f1c21b', '#42be65'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#3d2618',
                    titleColor: '#f9f3eb',
                    bodyColor: '#d4b89a',
                    borderColor: '#d4965f',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.parsed}`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Display PR list items
 */
function displayPRList(container, items, emptyMessage) {
    if (!items || items.length === 0) {
        container.innerHTML = `<div class="empty-state">${emptyMessage}</div>`;
        return;
    }
    
    const html = items.map(item => 
        `<div class="pr-list-item">${escapeHtml(item)}</div>`
    ).join('');
    
    container.innerHTML = html;
}

/**
 * Show loading overlay
 */
function showLoading(message) {
    loadingMessage.textContent = message;
    loadingOverlay.classList.add('active');
    analyzeBtn.disabled = true;
}

/**
 * Hide loading overlay
 */
function hideLoading() {
    loadingOverlay.classList.remove('active');
    analyzeBtn.disabled = false;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Check API health on page load
 */
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (response.ok) {
            console.log('✅ API is healthy and ready');
        } else {
            console.warn('⚠️ API health check returned non-OK status:', response.status);
        }
    } catch (error) {
        console.error('❌ Cannot connect to API:', error.message);
        console.log('💡 Make sure the backend is running: cd backend && python main.py');
    }
}

// Check API health when page loads
checkAPIHealth();

// Made with Bob
