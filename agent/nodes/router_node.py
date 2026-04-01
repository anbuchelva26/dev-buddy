"""
DEV BUDDY - Router Node
Stage 1: Ingestion & Categorization
- Connects to Jira API
- Fetches ticket details
- Categorizes into team
- Extracts microservice name
"""

import os
import re
import requests
from requests.auth import HTTPBasicAuth
from agent.state import AgentState

# credentials loaded inside function after dotenv

TEAM_MAP = {
    "backend"       : "Backend",
    "be"            : "Backend",
    "aol"           : "AOL (Mobile)",
    "mobilefrontend": "AOL (Mobile)",
    "mobile"        : "AOL (Mobile)",
    "devops"        : "DevOps",
    "platform"      : "Platform",
    "portal"        : "Portal",
}

RESET = "\033[0m"
BOLD  = "\033[1m"
CYAN  = "\033[96m"
GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW= "\033[93m"


def extract_text_from_adf(node):
    if not node:
        return ""
    text      = ""
    node_type = node.get("type", "")
    if node_type == "text":
        text += node.get("text", "")
    for child in node.get("content", []):
        child_text = extract_text_from_adf(child)
        if node_type in ("paragraph", "listItem", "bulletList", "orderedList"):
            text += child_text + "\n"
        else:
            text += child_text
    return text.strip()


def detect_team(fields, description):
    # Try custom field first
    team_field = fields.get("customfield_10100")
    if team_field:
        raw = ""
        if isinstance(team_field, dict):
            raw = team_field.get("value", "") or team_field.get("name", "")
        elif isinstance(team_field, str):
            raw = team_field
        normalized = raw.lower().replace(" ", "").replace("-", "")
        for key, val in TEAM_MAP.items():
            if key in normalized:
                return val

    # Fallback: scan title + module
    title     = fields.get("summary", "").lower()
    mod_field = fields.get("customfield_10200")
    module    = ""
    if isinstance(mod_field, dict):
        module = mod_field.get("value", "").lower()
    elif isinstance(mod_field, str):
        module = mod_field.lower()

    combined = title + " " + module
    if "backend" in combined or "be -" in combined:
        return "Backend"
    if "mobile" in combined or "aol" in combined or "flutter" in combined:
        return "AOL (Mobile)"
    if "devops" in combined or "helm" in combined:
        return "DevOps"
    if "platform" in combined or "k8s" in combined:
        return "Platform"
    if "portal" in combined:
        return "Portal"

    # Fallback: scan description text
    if description:
        dl = description.lower()
        if "team: backend" in dl or "team:backend" in dl:
            return "Backend"
        if "team: aol" in dl or "team: mobile" in dl:
            return "AOL (Mobile)"
        if "team: devops" in dl:
            return "DevOps"
        if "team: platform" in dl:
            return "Platform"
        if "team: portal" in dl:
            return "Portal"

    # Check labels
    labels = fields.get("labels", [])
    for lbl in labels:
        if lbl.lower() == "backend":
            return "Backend"
        if lbl.lower() in ("mobile", "aol"):
            return "AOL (Mobile)"
        if lbl.lower() == "devops":
            return "DevOps"

    return "Unknown"


def extract_microservice(fields, description):
    # Try custom field
    mod_field = fields.get("customfield_10200")
    if isinstance(mod_field, dict):
        val = mod_field.get("value", "") or mod_field.get("name", "")
        if val:
            return val
    elif isinstance(mod_field, str) and mod_field:
        return mod_field

    # Fallback: regex from description
    if description:
        match = re.search(r"microservice\s*:\s*([a-zA-Z0-9_-]+)", description, re.IGNORECASE)
        if match:
            ms = match.group(1).strip()
            # Cut off at uppercase letter
            cut = re.search(r"[A-Z]", ms)
            if cut and cut.start() > 0:
                ms = ms[:cut.start()].rstrip("-")
            return ms
    return ""


def router_node(state: AgentState) -> AgentState:
    ticket_id = state["ticket_id"]
    print(f"\n{BOLD}{CYAN}[ROUTER NODE] Processing ticket: {ticket_id}{RESET}")
    JIRA_URL       = os.getenv("JIRA_URL")
    JIRA_EMAIL     = os.getenv("JIRA_EMAIL")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
    AUTH           = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    HEADERS        = {"Accept": "application/json"}

    try:
        url      = f"{JIRA_URL}/rest/api/3/issue/{ticket_id}"
        response = requests.get(url, headers=HEADERS, auth=AUTH)

        if response.status_code != 200:
            print(f"  {RED}Jira API Error {response.status_code}{RESET}")
            return {**state, "error": f"Jira API Error {response.status_code}", "next_node": "end"}

        issue  = response.json()
        fields = issue.get("fields", {})

        # Extract description
        desc_raw    = fields.get("description")
        description = extract_text_from_adf(desc_raw) if isinstance(desc_raw, dict) else (desc_raw or "")

        # Extract team
        team = detect_team(fields, description)

        # Extract microservice
        microservice = extract_microservice(fields, description)

        # Extract other fields
        title       = fields.get("summary", "")
        status      = fields.get("status", {}).get("name", "")
        priority    = fields.get("priority", {}).get("name", "")
        reporter    = (fields.get("reporter") or {}).get("displayName", "Unknown")
        assignee    = (fields.get("assignee") or {}).get("displayName", "Unassigned")
        environment = ""
        env_field   = fields.get("customfield_10600")
        if isinstance(env_field, dict):
            environment = extract_text_from_adf(env_field)
        elif isinstance(env_field, str):
            environment = env_field

        sev_field = fields.get("customfield_10400")
        severity  = sev_field.get("value", "") if isinstance(sev_field, dict) else (sev_field or "")

        exp_raw  = fields.get("customfield_10700")
        act_raw  = fields.get("customfield_10800")
        expected = extract_text_from_adf(exp_raw) if isinstance(exp_raw, dict) else (exp_raw or "")
        actual   = extract_text_from_adf(act_raw) if isinstance(act_raw, dict) else (act_raw or "")

        print(f"  {GREEN}Title       : {title}{RESET}")
        print(f"  {GREEN}Team        : {team}{RESET}")
        print(f"  {GREEN}Microservice: {microservice}{RESET}")
        print(f"  {GREEN}Status      : {status}{RESET}")

        return {
            **state,
            "title"         : title,
            "status"        : status,
            "priority"      : priority,
            "severity"      : severity,
            "reporter"      : reporter,
            "assignee"      : assignee,
            "description"   : description,
            "environment"   : environment,
            "expected"      : expected,
            "actual"        : actual,
            "team"          : team,
            "microservice"  : microservice,
            "error"         : None,
            "next_node"     : "searcher",
        }

    except Exception as e:
        print(f"  {RED}Router error: {e}{RESET}")
        return {**state, "error": str(e), "next_node": "end"}
