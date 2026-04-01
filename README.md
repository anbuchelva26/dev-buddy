# Dev Buddy — AI Engineering Assistant

An intelligent multi-agent system that automatically analyzes Jira bug tickets, traces root causes in code, and generates production-ready fixes.

## What it does

- Reads Jira bug tickets automatically
- Finds relevant code files from GitHub
- Analyzes root cause using Groq LLM
- Generates production-ready code fixes
- Posts analysis back to Jira ticket automatically

## Pipeline Flow
```
Jira Ticket → Router → Searcher → Researcher → Coder → Jira Comment
```

## Tech Stack

- LangGraph — Multi-agent pipeline orchestration
- Groq (llama-3.3-70b) — AI model for analysis and fix generation
- Jira REST API — Ticket ingestion and comment posting
- GitHub API — Dynamic repo search and file fetching
- FastAPI — REST API backend
- React + Vite — Frontend dashboard
- Python Scheduler — Auto-runs every 10 minutes

## Supported Teams

| Team | Languages |
|---|---|
| Backend | Go, Java, Python |
| AOL Mobile | Kotlin, Dart, Swift |
| DevOps | Terraform, YAML, Shell |
| Platform | Go, Kubernetes YAML |
| Portal | JavaScript, TypeScript, React |

## Setup

1. Clone the repo
2. Create `.env` file from `.env.example`
3. Fill in your credentials
4. Install dependencies
5. Run backend and frontend

## Running the Project

**Backend:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install fastapi uvicorn
python -m uvicorn api:app --port 8000 --host 0.0.0.0
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Open browser:**
```
http://localhost:3000
```

## Environment Variables
```
JIRA_URL=your-jira-url
JIRA_EMAIL=your-email
JIRA_API_TOKEN=your-jira-token
JIRA_PROJECT_KEY=KAN
GITHUB_PAT=your-github-pat
GITHUB_ORG=your-github-org
GROQ_API_KEY=your-groq-key
GROQ_MODEL=llama-3.3-70b-versatile
```

## Built by

AboveCloud9 Internship 
