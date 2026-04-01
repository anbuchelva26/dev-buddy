"""
DEV BUDDY - Main Entry Point
Runs the full LangGraph pipeline for all Open/In-Progress Jira tickets.

Usage:
    python main.py                        # process all open tickets
    python main.py --ticket KAN-1         # process specific ticket
"""

import os
import json
import argparse
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from agent.graph import build_graph

load_dotenv()

JIRA_URL       = os.getenv("JIRA_URL")
JIRA_EMAIL     = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
PROJECT_KEY    = os.getenv("JIRA_PROJECT_KEY", "KAN")

AUTH    = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
HEADERS = {"Accept": "application/json"}

RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"


def fetch_ticket_ids(project_key):
    """Fetch all Open/In-Progress ticket IDs from Jira"""
    url    = f"{JIRA_URL}/rest/api/3/search/jql"
    jql    = f'project = "{project_key}" AND status IN ("Open", "In Progress") ORDER BY created DESC'
    params = {
        "jql"       : jql,
        "maxResults": 50,
        "fields"    : ["summary", "status"],
        "startAt"   : 0,
    }

    print(f"{BOLD}Fetching tickets from Jira project: {project_key}{RESET}")
    response = requests.get(url, headers=HEADERS, auth=AUTH, params=params)

    if response.status_code != 200:
        print(f"{RED}Jira API Error {response.status_code}: {response.text}{RESET}")
        return []

    issues = response.json().get("issues", [])
    ticket_ids = [issue["key"] for issue in issues]
    print(f"{GREEN}Found {len(ticket_ids)} ticket(s): {ticket_ids}{RESET}")
    return ticket_ids


def build_initial_state(ticket_id):
    """Build the initial AgentState with just the ticket ID"""
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


def save_results(results, output_file="output/final_output.json"):
    os.makedirs("output", exist_ok=True)

    # Clean state for saving (remove internal fields)
    clean_results = []
    for r in results:
        clean = {k: v for k, v in r.items() if k not in ("next_node", "files")}
        # Save file paths but not full content
        clean["files_scanned"] = [f["path"] for f in r.get("files", [])]
        clean_results.append(clean)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(clean_results, f, indent=2, ensure_ascii=False)

    print(f"\n{GREEN}Saved final output to {output_file}{RESET}")


def main():
    parser = argparse.ArgumentParser(description="Dev Buddy - AI Engineering Assistant")
    parser.add_argument("--ticket", type=str, help="Specific ticket ID to process (e.g. KAN-1)")
    args = parser.parse_args()

    print("=" * 60)
    print("   DEV BUDDY - AI Engineering Assistant")
    print("   Powered by LangGraph + Groq")
    print("=" * 60)

    # Build the LangGraph
    app = build_graph()

    # Get ticket IDs to process
    if args.ticket:
        ticket_ids = [args.ticket]
        print(f"\n{BOLD}Processing specific ticket: {args.ticket}{RESET}\n")
    else:
        ticket_ids = fetch_ticket_ids(PROJECT_KEY)

    if not ticket_ids:
        print(f"{YELLOW}No tickets found to process.{RESET}")
        return

    results = []

    for i, ticket_id in enumerate(ticket_ids, 1):
        print(f"\n{'─'*60}")
        print(f"{BOLD}{CYAN}Processing ticket {i}/{len(ticket_ids)}: {ticket_id}{RESET}")
        print(f"{'─'*60}")

        # Build initial state
        initial_state = build_initial_state(ticket_id)

        # Run the LangGraph pipeline
        try:
            final_state = app.invoke(initial_state)
            results.append(final_state)

            if final_state.get("error"):
                print(f"{YELLOW}Completed with warning: {final_state['error']}{RESET}")
            else:
                print(f"{GREEN}Successfully processed: {ticket_id}{RESET}")

        except Exception as e:
            print(f"{RED}Pipeline error for {ticket_id}: {e}{RESET}")

    # Save all results
    save_results(results)

    # Final summary
    print(f"\n{'='*60}")
    print(f"{BOLD}{GREEN}  DEV BUDDY PIPELINE COMPLETE!{RESET}")
    print(f"{'='*60}")
    print(f"  Tickets processed : {len(results)}")
    print(f"  Fixes generated   : {sum(1 for r in results if r.get('fixes'))}")
    print(f"  Output saved to   : output/final_output.json")
    print(f"\n  Pipeline flow:")
    print(f"  START → Router → Searcher → Researcher → Coder → END")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
