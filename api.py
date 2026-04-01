"""
DEV BUDDY - FastAPI Backend
Wraps the LangGraph pipeline as a REST API.
"""

import os
import json
import asyncio
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from agent.graph import build_graph

load_dotenv()

JIRA_URL       = os.getenv("JIRA_URL")
JIRA_EMAIL     = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
PROJECT_KEY    = os.getenv("JIRA_PROJECT_KEY", "KAN")

AUTH    = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
HEADERS = {"Accept": "application/json"}

app = FastAPI(title="Dev Buddy API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Build graph once on startup
graph = build_graph()

# In-memory store for results
results_store = {}
pipeline_status = {}


class TicketRequest(BaseModel):
    ticket_id: str
    force: Optional[bool] = False


def build_initial_state(ticket_id):
    return {
        "ticket_id"       : ticket_id,
        "title"           : "",
        "status"          : "",
        "priority"        : "",
        "severity"        : "",
        "reporter"        : "",
        "assignee"        : "",
        "description"     : "",
        "environment"     : "",
        "expected"        : "",
        "actual"          : "",
        "pr_link"         : "",
        "team"            : "",
        "microservice"    : "",
        "repo_name"       : "",
        "branch"          : "",
        "files"           : [],
        "search_attempts" : 0,
        "root_cause"      : "",
        "bug_type"        : "",
        "affected_layer"  : "",
        "affected_files"  : [],
        "analysis_summary": "",
        "fix_summary"     : "",
        "fixes"           : [],
        "testing_steps"   : [],
        "prevention"      : "",
        "error"           : None,
        "next_node"       : None,
    }


@app.get("/")
def root():
    return {"message": "Dev Buddy API is running!", "version": "1.0.0"}


@app.get("/tickets")
def get_tickets():
    """Fetch all Open/In-Progress tickets from Jira"""
    url    = f"{JIRA_URL}/rest/api/3/search/jql"
    jql    = f'project = "{PROJECT_KEY}" AND status NOT IN ("Done", "Closed", "Resolved") ORDER BY created DESC'
    params = {
        "jql"       : jql,
        "maxResults": 50,
        "fields"    : ["summary", "status", "priority", "assignee", "reporter", "labels"],
        "startAt"   : 0,
    }

    response = requests.get(url, headers=HEADERS, auth=AUTH, params=params)
    if response.status_code != 200:
        return {"error": f"Jira API Error {response.status_code}", "tickets": []}

    issues  = response.json().get("issues", [])
    tickets = []
    for issue in issues:
        fields = issue.get("fields", {})
        tickets.append({
            "ticket_id": issue["key"],
            "title"    : fields.get("summary", ""),
            "status"   : fields.get("status", {}).get("name", ""),
            "priority" : fields.get("priority", {}).get("name", ""),
            "assignee" : (fields.get("assignee") or {}).get("displayName", "Unassigned"),
            "reporter" : (fields.get("reporter") or {}).get("displayName", "Unknown"),
        })
    return {"tickets": tickets, "total": len(tickets)}


@app.post("/analyze")
async def analyze_ticket(req: TicketRequest, background_tasks: BackgroundTasks):
    """Start pipeline analysis for a ticket"""
    ticket_id = req.ticket_id
    pipeline_status[ticket_id] = {
        "status"      : "running",
        "current_node": "router",
        "nodes_done"  : [],
        "error"       : None,
    }
    background_tasks.add_task(run_pipeline, ticket_id)
    return {"message": f"Analysis started for {ticket_id}", "ticket_id": ticket_id}


async def run_pipeline(ticket_id: str):
    """Run the LangGraph pipeline in background"""
    try:
        pipeline_status[ticket_id]["current_node"] = "router"
        initial_state = build_initial_state(ticket_id)

        # Run pipeline
        loop        = asyncio.get_event_loop()
        final_state = await loop.run_in_executor(None, graph.invoke, initial_state)

        # Store result
        clean = {k: v for k, v in final_state.items() if k not in ("next_node", "files")}
        clean["files_scanned"] = [f["path"] for f in final_state.get("files", [])]
        results_store[ticket_id] = clean

        pipeline_status[ticket_id] = {
            "status"      : "completed",
            "current_node": "done",
            "nodes_done"  : ["router", "searcher", "researcher", "coder"],
            "error"       : final_state.get("error"),
        }

    except Exception as e:
        pipeline_status[ticket_id] = {
            "status"      : "error",
            "current_node": "error",
            "nodes_done"  : [],
            "error"       : str(e),
        }


@app.get("/status/{ticket_id}")
def get_status(ticket_id: str):
    """Get pipeline status for a ticket"""
    return pipeline_status.get(ticket_id, {"status": "not_started"})


@app.get("/result/{ticket_id}")
def get_result(ticket_id: str):
    """Get analysis result for a ticket"""
    result = results_store.get(ticket_id)
    if not result:
        return {"error": "No result found. Run /analyze first."}
    return result


@app.get("/results")
def get_all_results():
    """Get all analysis results"""
    return {"results": list(results_store.values()), "total": len(results_store)}


@app.get("/health")
def health():
    return {"status": "ok", "graph": "compiled"}
