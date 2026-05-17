// API Configuration
const API_URL_ANALYZE = 'http://localhost:8000/analyze';
const API_URL_SCAN = 'http://localhost:8000/scan';

// Current mode
let currentMode = 'pr'; // 'pr' or 'scan'

// DOM Elements
const analyzeForm = document.getElementById('analyzeForm');
const analyzeBtn = document.getElementById('analyzeBtn');
const btnText = document.getElementById('btnText');
const btnLoader = document.getElementById('btnLoader');

const loadingSection = document.getElementById('loadingSection');
const loadingText = document.getElementById('loadingText');
const errorSection = document.getElementById('errorSection');
const prResultsSection = document.getElementById('prResultsSection');
const scanResultsSection = document.getElementById('scanResultsSection');

const errorMessage = document.getElementById('errorMessage');

// Tab buttons
const tabBtns = document.querySelectorAll('.tab-btn');
const prInputs = document.getElementById('prInputs');
const scanInputs = document.getElementById('scanInputs');

/**
 * Initialize tab switching
 */
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        switchTab(tab);
    });
});

/**
 * Switch between PR and Scan tabs
 */
function switchTab(tab) {
    currentMode = tab;
    
    // Update tab buttons
    tabBtns.forEach(btn => {
        if (btn.dataset.tab === tab) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Update tab content
    if (tab === 'pr') {
        prInputs.classList.add('active');
        scanInputs.classList.remove('active');
        btnText.textContent = 'Analyze Impact';
    } else {
        prInputs.classList.remove('active');
        scanInputs.classList.add('active');
        btnText.textContent = 'Scan Repository';
    }
    
    // Hide results
    hideAllResults();
}

/**
 * Handle form submission
 */
analyzeForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (currentMode === 'pr') {
        const repoUrl = document.getElementById('prRepoUrl').value.trim();
        const prNum = parseInt(document.getElementById('prNumber').value);
        
        if (!repoUrl || !prNum) {
            showError('Please provide both repository URL and PR number');
            return;
        }
        
        await analyzePR(repoUrl, prNum);
    } else {
        const repoUrl = document.getElementById('scanRepoUrl').value.trim();
        
        if (!repoUrl) {
            showError('Please provide a repository URL');
            return;
        }
        
        await scanRepo(repoUrl);
    }
});

/**
 * Analyze PR by calling the backend API
 */
async function analyzePR(repoUrl, prNum) {
    try {
        showLoading('Analyzing PR impact...');
        
        const response = await fetch(API_URL_ANALYZE, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                repo_url: repoUrl,
                pr_number: prNum
            })
        });
        
        if (!response.ok) {
            let errorMsg = `HTTP error! status: ${response.status}`;
            try {
                const errorData = await response.json();
                errorMsg = errorData.detail || errorMsg;
            } catch (e) {
                errorMsg = response.statusText || errorMsg;
            }
            throw new Error(errorMsg);
        }
        
        const data = await response.json();
        displayPRResults(data);
        
    } catch (error) {
        console.error('Analysis error:', error);
        
        let errorMsg = error.message;
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMsg = 'Cannot connect to the API server. Please ensure the backend is running on http://localhost:8000';
        }
        
        showError(errorMsg);
    }
}

/**
 * Scan repository by calling the backend API
 */
async function scanRepo(repoUrl) {
    try {
        showLoading('Bob is scanning your repository structure...');
        
        const response = await fetch(API_URL_SCAN, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                repo_url: repoUrl
            })
        });
        
        if (!response.ok) {
            let errorMsg = `HTTP error! status: ${response.status}`;
            try {
                const errorData = await response.json();
                errorMsg = errorData.detail || errorMsg;
            } catch (e) {
                errorMsg = response.statusText || errorMsg;
            }
            throw new Error(errorMsg);
        }
        
        const data = await response.json();
        displayScanResults(data);
        
    } catch (error) {
        console.error('Scan error:', error);
        
        let errorMsg = error.message;
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMsg = 'Cannot connect to the API server. Please ensure the backend is running on http://localhost:8000';
        }
        
        showError(errorMsg);
    }
}

/**
 * Display PR analysis results
 */
function displayPRResults(data) {
    const prTitle = document.getElementById('prTitle');
    const riskBadge = document.getElementById('riskBadge');
    const repoName = document.getElementById('repoName');
    const prNumberDisplay = document.getElementById('prNumberDisplay');
    const summaryText = document.getElementById('summaryText');
    const affectedFiles = document.getElementById('affectedFiles');
    const staleTests = document.getElementById('staleTests');
    const staleDocs = document.getElementById('staleDocs');
    
    prTitle.textContent = data.pr_title || 'Pull Request Analysis';
    repoName.textContent = data.repo_name || 'N/A';
    prNumberDisplay.textContent = `#${data.pr_number}`;
    
    const riskLevel = data.risk_score || 'medium';
    riskBadge.textContent = `${capitalizeFirst(riskLevel)} Risk`;
    riskBadge.className = `risk-badge ${riskLevel}`;
    
    summaryText.textContent = data.summary || 'No summary available.';
    
    displayAffectedFiles(data.affected_files || [], affectedFiles);
    displayList(data.stale_tests || [], staleTests, 'No tests need updates');
    displayList(data.stale_docs || [], staleDocs, 'No documentation needs updates');
    
    hideLoading();
    hideError();
    prResultsSection.style.display = 'block';
    prResultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Display repository scan results
 */
function displayScanResults(data) {
    // Health grade
    const healthGrade = document.getElementById('healthGrade');
    const grade = data.health_score || 'unknown';
    healthGrade.textContent = grade.toUpperCase();
    healthGrade.className = `health-grade grade-${grade.toLowerCase()}`;
    
    // Repo info
    document.getElementById('scanRepoName').textContent = data.repo_name || 'N/A';
    document.getElementById('scanLanguage').textContent = data.language || 'Unknown';
    document.getElementById('scanStars').textContent = data.stars || 0;
    document.getElementById('scanTotalFiles').textContent = data.total_files || 0;
    
    // Stats
    document.getElementById('sourceCount').textContent = data.source_files_count || 0;
    document.getElementById('testCount').textContent = data.test_files_count || 0;
    document.getElementById('docCount').textContent = data.doc_files_count || 0;
    
    // Health summary
    document.getElementById('healthSummary').textContent = data.health_summary || 'No summary available.';
    
    // Top risks
    displayNumberedList(data.top_risks || [], document.getElementById('topRisks'), 'No risks identified');
    
    // Untested modules
    displayList(data.untested_modules || [], document.getElementById('untestedModules'), 'None detected');
    
    // Fragile files
    displayFragileFiles(data.fragile_files || []);
    
    // Stale docs
    displayList(data.stale_docs || [], document.getElementById('scanStaleDocs'), 'None detected');
    
    // Recommendations
    displayNumberedList(data.recommendations || [], document.getElementById('recommendations'), 'No recommendations');
    
    hideLoading();
    hideError();
    scanResultsSection.style.display = 'block';
    scanResultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Display affected files
 */
function displayAffectedFiles(files, container) {
    if (!files || files.length === 0) {
        container.innerHTML = '<div class="empty-state">No affected files detected</div>';
        return;
    }
    
    container.innerHTML = files.map(file => `
        <div class="file-card">
            <div class="file-header">
                <span class="file-path">${escapeHtml(file.path)}</span>
                <span class="file-impact ${file.impact}">${file.impact}</span>
            </div>
            <div class="file-reason">${escapeHtml(file.reason)}</div>
        </div>
    `).join('');
}

/**
 * Display fragile files
 */
function displayFragileFiles(files) {
    const container = document.getElementById('fragileFiles');
    
    if (!files || files.length === 0) {
        container.innerHTML = '<div class="empty-state">No fragile files detected</div>';
        return;
    }
    
    container.innerHTML = files.map(file => `
        <div class="file-card">
            <div class="file-header">
                <span class="file-path">${escapeHtml(file.path)}</span>
                <span class="file-impact ${file.risk}">${file.risk}</span>
            </div>
            <div class="file-reason">${escapeHtml(file.reason)}</div>
        </div>
    `).join('');
}

/**
 * Display a list of items
 */
function displayList(items, container, emptyMessage) {
    if (!items || items.length === 0) {
        container.innerHTML = `<div class="empty-state">${emptyMessage}</div>`;
        return;
    }
    
    container.innerHTML = items.map(item => `
        <div class="list-item">${escapeHtml(item)}</div>
    `).join('');
}

/**
 * Display a numbered list
 */
function displayNumberedList(items, container, emptyMessage) {
    if (!items || items.length === 0) {
        container.innerHTML = `<li class="empty-state" style="list-style: none; border: none;">${emptyMessage}</li>`;
        return;
    }
    
    container.innerHTML = items.map(item => `
        <li>${escapeHtml(item)}</li>
    `).join('');
}

/**
 * Show loading state
 */
function showLoading(message) {
    analyzeBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-block';
    
    loadingText.textContent = message;
    loadingSection.style.display = 'block';
    
    hideError();
    hideAllResults();
}

/**
 * Hide loading state
 */
function hideLoading() {
    analyzeBtn.disabled = false;
    btnText.style.display = 'inline';
    btnLoader.style.display = 'none';
    
    loadingSection.style.display = 'none';
}

/**
 * Show error message
 */
function showError(message) {
    hideLoading();
    hideAllResults();
    
    errorMessage.textContent = message;
    errorSection.style.display = 'block';
    
    errorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Hide error section
 */
function hideError() {
    errorSection.style.display = 'none';
}

/**
 * Hide all result sections
 */
function hideAllResults() {
    prResultsSection.style.display = 'none';
    scanResultsSection.style.display = 'none';
}

/**
 * Capitalize first letter of a string
 */
function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
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
        const response = await fetch('http://localhost:8000/health', {
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
