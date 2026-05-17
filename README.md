# 🌊 Bob Ripple

**Analyze GitHub Pull Request Impact using Google Gemini AI**

Bob Ripple is a web application that leverages Google Gemini 2.0 Flash model to provide intelligent impact analysis of GitHub Pull Requests. It identifies affected files, assesses risk levels, and highlights potentially stale tests and documentation.

## Features

- 🔍 **Deep PR Analysis**: Fetches PR diffs, metadata, and changed files from GitHub
- 🤖 **AI-Powered Insights**: Uses Google Gemini 2.0 Flash model for intelligent impact assessment
- 📊 **Risk Scoring**: Categorizes PRs as high, medium, or low risk
- 🧪 **Test Detection**: Identifies test files that may need updates
- 📚 **Documentation Tracking**: Flags documentation that might be outdated
- 🎨 **Clean UI**: Dark developer-friendly interface with card-based layout

## Project Structure

```
bob-ripple/
├── backend/
│   ├── main.py              # FastAPI application with CORS and routes
│   ├── github_service.py    # GitHub API integration
│   ├── analyzer.py          # Google Gemini API integration and analysis logic
│   ├── models.py            # Pydantic data models
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Single-page application
│   ├── style.css            # Dark theme styling
│   └── app.js               # Frontend logic and API calls
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Prerequisites

- Python 3.9 or higher
- GitHub Personal Access Token
- Google Gemini API Key

## Setup Instructions

### 1. Clone or Download the Project

```bash
cd bob-ripple
```

### 2. Set Up Backend

#### Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### Configure Environment Variables

Copy the `.env.example` file to `.env` in the project root:

```bash
cd ..
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
GITHUB_TOKEN=your_github_personal_access_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

**Getting Your Credentials:**

- **GitHub Token**: Visit [GitHub Settings > Tokens](https://github.com/settings/tokens) and create a new token with `repo` scope
- **Gemini API Key**: Visit [Google AI Studio](https://aistudio.google.com/app/apikey) and create a new API key

### 3. Run the Backend

```bash
cd backend
python main.py
```

The API will start on `http://localhost:8000`

**Available Endpoints:**
- `GET /health` - Health check
- `POST /analyze` - Analyze a PR (requires JSON body with `repo_url` and `pr_number`)
- `GET /` - API information

### 4. Run the Frontend

Open `frontend/index.html` in your web browser, or serve it with a simple HTTP server:

```bash
cd frontend

# Using Python
python -m http.server 3000

# Using Node.js (if you have http-server installed)
npx http-server -p 3000
```

Then open `http://localhost:3000` in your browser.

## Usage

1. **Enter Repository URL**: Provide the full GitHub repository URL (e.g., `https://github.com/owner/repo`)
2. **Enter PR Number**: Specify the pull request number (e.g., `123`)
3. **Click "Analyze Impact"**: The app will fetch the PR data and analyze it using watsonx.ai
4. **Review Results**: See the impact report with:
   - Overall risk score (high/medium/low)
   - Affected files with individual impact levels
   - Potentially stale test files
   - Potentially stale documentation files
   - Executive summary

## API Reference

### POST /analyze

Analyze a GitHub Pull Request.

**Request Body:**
```json
{
  "repo_url": "https://github.com/owner/repo",
  "pr_number": 123
}
```

**Response:**
```json
{
  "pr_number": 123,
  "repo_name": "owner/repo",
  "pr_title": "Add new feature",
  "affected_files": [
    {
      "path": "src/main.py",
      "changes": 45,
      "impact": "high",
      "reason": "Core application logic modified"
    }
  ],
  "risk_score": "medium",
  "stale_tests": ["tests/test_main.py"],
  "stale_docs": ["README.md"],
  "summary": "This PR modifies core application logic with moderate risk..."
}
```

### GET /health

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "Bob Ripple API"
}
```

## Architecture

### Backend Flow

1. **FastAPI** receives analyze request with repo URL and PR number
2. **GitHubService** fetches PR metadata, diff, and changed files via GitHub REST API
3. **GeminiAnalyzer** constructs a structured prompt with PR context
4. **Google Gemini 2.0 Flash model** analyzes the PR and returns structured JSON
5. **Pydantic models** validate and structure the response
6. **FastAPI** returns the impact report to the frontend

### Frontend Flow

1. User submits repository URL and PR number
2. JavaScript fetches POST request to `/analyze` endpoint
3. Loading state displayed during analysis
4. Results rendered as cards with color-coded risk levels
5. Error handling for failed requests

## Technologies Used

### Backend
- **FastAPI**: Modern Python web framework
- **httpx**: Async HTTP client for API calls
- **Pydantic**: Data validation and settings management
- **python-dotenv**: Environment variable management
- **uvicorn**: ASGI server

### Frontend
- **Vanilla JavaScript**: No framework dependencies
- **Fetch API**: For HTTP requests
- **CSS Grid/Flexbox**: Responsive layout
- **CSS Variables**: Theming system

### AI/ML
- **Google Gemini API**: AI platform
- **Gemini 2.0 Flash**: Large language model for code analysis

## Troubleshooting

### Backend Issues

**Import Errors**: Make sure you're in the `backend` directory and have installed all dependencies:
```bash
cd backend
pip install -r requirements.txt
```

**API Connection Failed**: Verify your `.env` file is in the project root (not in backend/) and contains valid credentials.

**GitHub API Rate Limit**: Use a GitHub token to increase rate limits from 60 to 5000 requests per hour.

### Frontend Issues

**CORS Errors**: Make sure the backend is running and CORS is properly configured in `main.py`.

**API Not Found**: Check that the `API_BASE_URL` in `app.js` matches your backend URL (default: `http://localhost:8000`).

## Development

### Running Tests

```bash
cd backend
pytest
```

### Code Style

The project follows PEP 8 style guidelines for Python code.

## Security Notes

- Never commit your `.env` file with real credentials
- Use environment variables for all sensitive data
- In production, restrict CORS origins to specific domains
- Consider adding authentication for the API endpoints
- Rotate API keys regularly

## Future Enhancements

- [ ] Add authentication and user management
- [ ] Support for multiple AI models
- [ ] Historical analysis tracking
- [ ] Batch PR analysis
- [ ] Integration with CI/CD pipelines
- [ ] Webhook support for automatic analysis
- [ ] Export reports as PDF/Markdown
- [ ] Custom analysis rules and templates

## License

MIT License - feel free to use this project for your own purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on the GitHub repository.

---

**Built with ❤️ by Bob using Google Gemini AI**