// API Configuration
const API_URL = 'http://localhost:8000/analyze';

// DOM Elements
const analyzeForm = document.getElementById('analyzeForm');
const analyzeBtn = document.getElementById('analyzeBtn');
const btnText = document.getElementById('btnText');
const btnLoader = document.getElementById('btnLoader');

const loadingSection = document.getElementById('loadingSection');
const errorSection = document.getElementById('errorSection');
const resultsSection = document.getElementById('resultsSection');

const errorMessage = document.getElementById('errorMessage');

const prTitle = document.getElementById('prTitle');
const riskBadge = document.getElementById('riskBadge');
const repoName = document.getElementById('repoName');
const prNumber = document.getElementById('prNumber');
const summaryText = document.getElementById('summaryText');
const affectedFiles = document.getElementById('affectedFiles');
const staleTests = document.getElementById('staleTests');
const staleDocs = document.getElementById('staleDocs');

/**
 * Handle form submission
 */
analyzeForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const repoUrl = document.getElementById('repoUrl').value.trim();
    const prNum = parseInt(document.getElementById('prNumber').value);
    
    if (!repoUrl || !prNum) {
        showError('Please provide both repository URL and PR number');
        return;
    }
    
    await analyzePR(repoUrl, prNum);
});

/**
 * Analyze PR by calling the backend API
 */
async function analyzePR(repoUrl, prNum) {
    try {
        // Show loading state
        showLoading();
        
        // Call API
        const response = await fetch(API_URL, {
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
                // If response is not JSON, use status text
                errorMsg = response.statusText || errorMsg;
            }
            throw new Error(errorMsg);
        }
        
        const data = await response.json();
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        console.error('Analysis error:', error);
        
        // Handle network errors gracefully
        let errorMsg = error.message;
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMsg = 'Cannot connect to the API server. Please ensure the backend is running on http://localhost:8000';
        }
        
        showError(errorMsg);
    }
}

/**
 * Display analysis results
 */
function displayResults(data) {
    // Set PR title and metadata
    prTitle.textContent = data.pr_title || 'Pull Request Analysis';
    repoName.textContent = data.repo_name || 'N/A';
    prNumber.textContent = `#${data.pr_number}`;
    
    // Set risk badge
    const riskLevel = data.risk_score || 'medium';
    riskBadge.textContent = `${capitalizeFirst(riskLevel)} Risk`;
    riskBadge.className = `risk-badge ${riskLevel}`;
    
    // Set summary
    summaryText.textContent = data.summary || 'No summary available.';
    
    // Display affected files
    displayAffectedFiles(data.affected_files || []);
    
    // Display stale tests
    displayList(data.stale_tests || [], staleTests, 'No tests need updates');
    
    // Display stale docs
    displayList(data.stale_docs || [], staleDocs, 'No documentation needs updates');
    
    // Show results section
    hideLoading();
    hideError();
    resultsSection.style.display = 'block';
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Display affected files
 */
function displayAffectedFiles(files) {
    if (!files || files.length === 0) {
        affectedFiles.innerHTML = '<div class="empty-state">No affected files detected</div>';
        return;
    }
    
    affectedFiles.innerHTML = files.map(file => `
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
 * Display a list of items (tests or docs)
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
 * Show loading state
 */
function showLoading() {
    // Disable form
    analyzeBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-block';
    
    // Show loading section
    loadingSection.style.display = 'block';
    
    // Hide other sections
    errorSection.style.display = 'none';
    resultsSection.style.display = 'none';
}

/**
 * Hide loading state
 */
function hideLoading() {
    // Enable form
    analyzeBtn.disabled = false;
    btnText.style.display = 'inline';
    btnLoader.style.display = 'none';
    
    // Hide loading section
    loadingSection.style.display = 'none';
}

/**
 * Show error message
 */
function showError(message) {
    hideLoading();
    resultsSection.style.display = 'none';
    
    errorMessage.textContent = message;
    errorSection.style.display = 'block';
    
    // Scroll to error
    errorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Hide error section
 */
function hideError() {
    errorSection.style.display = 'none';
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
