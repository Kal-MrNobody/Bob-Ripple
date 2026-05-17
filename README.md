# Bob Ripple

**Know your codebase. Predict what breaks before it does.**

Bob Ripple analyzes GitHub repositories using AI to identify fragile code, predict PR risks, and surface problems before they hit production. The entire project was built using IBM Bob IDE with Google Gemini 2.5 Pro handling the analysis.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)

---

## What It Does

### Repository Health Scanning
Point it at any GitHub repo and get an instant health grade (A through D). The system reads your entire codebase, identifies fragile files that could break your app, calculates test coverage, and generates specific recommendations for improvement.

### Pull Request Impact Analysis
Before merging a PR, Bob Ripple predicts its risk level and shows exactly which files will be affected. It flags tests that need updates and documentation that's about to go stale.

### Live Dashboard
Everything runs through a single-page dashboard with real-time charts. The interface uses a warm cafe aesthetic with espresso browns and amber accents. Charts update instantly using Chart.js, and you can analyze both repos and PRs from one unified command bar.

---

## Getting Started

You'll need Python 3.11 or higher, a GitHub personal access token, and a Google Gemini API key.

### Installation

Clone the repo and set up the backend:

```bash
git clone https://github.com/yourusername/bob-ripple.git
cd bob-ripple/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your API keys:

```env
GITHUB_TOKEN=ghp_your_github_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

Start the backend:

```bash
python main.py
```

The API runs on `http://localhost:8000`. Open `frontend/index.html` in your browser, or serve it with:

```bash
cd ../frontend
python -m http.server 3000
```

---

## How to Use It

Open the dashboard and paste any GitHub repository URL. Click Analyze and you'll see health metrics, risk distribution charts, and a list of fragile files. Add a PR number in the optional field to analyze a specific pull request at the same time.

Try the quick-start examples on the landing page: `pallets/flask` or `fastapi/fastapi`. Both trigger instant analysis.

---

## Project Structure

```
bob-ripple/
├── backend/
│   ├── main.py              # FastAPI routes and CORS setup
│   ├── github_service.py    # GitHub API integration
│   ├── analyzer.py          # Gemini AI calls
│   ├── models.py            # Pydantic schemas
│   └── requirements.txt
├── frontend/
│   ├── index.html           # Single-page dashboard
│   ├── style.css            # Cafe-themed styling
│   └── app.js               # Chart.js and API logic
└── .env.example
```

The backend uses FastAPI with httpx for async HTTP calls. The frontend is vanilla JavaScript with Chart.js 4.4.1 for visualizations. No frameworks, no build step.

---

## The Prompts That Built This

Most projects claim they used AI but don't show how. Here are the actual prompts from the development session, in order.

### Prompt 1: Initial Scaffold

"Create a complete project structure for Bob Ripple — a web app that analyzes GitHub PR impact using Gemini AI. Create these files with full working content: /backend with main.py (FastAPI app with CORS, routes POST /analyze and GET /health), github_service.py (fetches PR diff and changed files via GitHub REST API), analyzer.py (calls Gemini API with repo context + diff, returns structured impact JSON), models.py (Pydantic models: AnalyzeRequest, AffectedFile, ImpactReport), requirements.txt (fastapi, uvicorn, httpx, python-dotenv, pydantic). /frontend with index.html, style.css, app.js. Use httpx for all HTTP calls. Use python-dotenv for env vars."

Bob generated 14 files, fully wired and ready to run.

### Prompt 2: GitHub Integration

"Implement github_service.py completely with two functions: get_pr_data() — parse owner/repo from URL, call GitHub REST API, return PR metadata. get_pr_diff() — fetch all changed files, concatenate patches into diff string, truncate to 12000 chars if longer, return (diff_string, changed_files_list). Both use httpx.AsyncClient with follow_redirects=True. Raise HTTPException with clear messages on 404 and 401."

This produced a complete async GitHub service with proper redirect handling and URL parsing.

### Prompt 3: Gemini Integration

"Implement analyzer.py using Google Gemini API. URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent. Add header x-goog-api-key: GEMINI_API_KEY. Add thinkingConfig: {thinkingBudget: 1024} to generationConfig. Set responseMimeType: application/json to force clean JSON output. Prompt instructs Gemini to act as senior software architect and return affected_files, stale_tests, stale_docs, risk_score, and summary. On any exception return a valid empty response shape — never let the frontend break."

Bob integrated Gemini with thinking mode enabled and clean JSON parsing.

### Prompt 4: Repository Scanner

"Add a new Repo Health Scan feature. In github_service.py add get_repo_structure() that fetches the full file tree via GitHub tree API, classifies files into source/test/doc categories using extension matching, caps each category independently (150 source, 50 test, 100 doc), sorts source files by importance — root-level files and files named main/app/core/api/router first. In analyzer.py add analyze_repo_health() that sends file structure to Gemini and returns health_score A-D, fragile_files, untested_modules, top_risks, and recommendations. Add POST /scan route to main.py."

This added the full repository scanner with smart file prioritization.

### Prompt 5: Dashboard Redesign

"Completely rewrite the frontend as a real analytics dashboard. Unified navbar: repo URL input + PR number input + Analyze button in one bar. Hero landing state with headline, feature pills, and two quick-start example buttons (pallets/flask and fastapi/fastapi) that trigger analysis on click. Dashboard grid: 4 metric cards, risk distribution donut chart, file type bar chart, fragile files table, untested modules list, top risks panel, recommendations panel, PR impact results section. Warm cafe aesthetic: espresso browns, amber accent, Playfair Display headings, JetBrains Mono for file paths. Chart.js for all charts. Both API calls run in parallel with Promise.all() when PR number is provided."

Bob delivered a complete single-page dashboard with zero frameworks and live charts.

### The Debugging Prompts

These are the ones that actually mattered:

"In github_service.py, configure httpx.AsyncClient with follow_redirects=True in both functions."

This fixed the issue where `tiangolo/fastapi` redirected to `fastapi/fastapi` and broke the entire call.

"In github_service.py, fix get_repo_structure(). Classify ALL files first, then cap each list independently. Sort source files by importance before capping — root-level files and files named main/app/core/api/router float to the top."

The first version returned 300 documentation files for fastapi/fastapi, so Gemini concluded the repo had no source code.

"In github_service.py, add import os at the very top of the file."

The backend crashed with `NameError: name 'os' is not defined`.

---

## Real Output Example

Here's actual output from analyzing `pallets/flask`:

```json
{
  "repo_name": "flask",
  "language": "Python",
  "stars": 71549,
  "health_score": "A",
  "health_summary": "This is an exceptionally well-structured and mature repository. It demonstrates excellent separation of concerns, a high test-to-source file ratio, and comprehensive documentation covering all major aspects of the framework.",
  "fragile_files": [
    {
      "path": "src/flask/app.py",
      "reason": "Core application class, central to the entire framework. Any bug introduced here has a high probability of causing widespread issues across all Flask applications.",
      "risk": "high"
    },
    {
      "path": "src/flask/ctx.py", 
      "reason": "Manages application and request contexts. Issues in context management are subtle and can lead to hard-to-debug state-related bugs.",
      "risk": "high"
    }
  ],
  "top_risks": [
    "The complexity of app.py and ctx.py makes them susceptible to regressions with widespread impact",
    "Outdated deployment docs for older technologies like Gevent could mislead users",
    "Any undiscovered security vulnerability in sessions or wrappers could expose a large number of applications"
  ],
  "recommendations": [
    "Review and update deployment documentation, prioritizing modern ASGI/WSGI servers",
    "Add architectural decision records to document reasoning behind major design choices",
    "Continue investing in type hint coverage and static analysis"
  ]
}
```

This isn't a template. Run it on `fastapi/fastapi` and you get a B. Run it on this repo and you get a C. The analysis changes based on what's actually in the codebase.

---

## API Keys

### GitHub Token

Go to GitHub Settings, then Developer settings, then Personal access tokens. Generate a new classic token with `repo` scope for private repos or `public_repo` for public only. Copy the token into your `.env` file.

### Gemini API Key

Visit Google AI Studio at `aistudio.google.com/app/apikey` and create an API key. Add it to your `.env` file.

---

## Technical Stack

**Backend:**
- FastAPI for the web framework
- httpx for async HTTP requests
- Pydantic for data validation
- python-dotenv for environment variables

**Frontend:**
- Vanilla JavaScript (no frameworks)
- Chart.js 4.4.1 for charts
- Google Fonts: Playfair Display, Inter, JetBrains Mono

**AI:**
- Google Gemini 2.5 Pro with thinking mode
- GitHub REST API v3

---

## Design Notes

The interface uses a warm cafe aesthetic inspired by understanding your codebase over coffee. Deep espresso browns (#2a1810, #3d2618, #4a3020) for backgrounds, caramel and amber (#d4965f, #f0b878) for accents. Playfair Display for headings, Inter for body text, JetBrains Mono for code. The health bar under the navbar has an animated wave effect that flows across when you run an analysis.

---

## Contributing

Fork the repo, create a feature branch, make your changes, and open a pull request. Standard GitHub workflow.

---

## License

MIT License. See LICENSE file for details.

---

## Credits

Built with IBM Bob IDE. Analysis powered by Google Gemini 2.5 Pro. Repository data from GitHub REST API. Charts by Chart.js. Backend framework by FastAPI.

---

**Try it:** Paste any GitHub URL and see what Bob finds.

<sub>Built entirely with IBM Bob IDE • Powered by Gemini 2.5 Pro • Real GitHub API — no hardcoded data</sub>