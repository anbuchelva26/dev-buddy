"""
DEV BUDDY - Researcher Node
Stage 3: Code Analysis
- Applies architecture-specific analysis strategy
- Sends ticket context + code to Groq LLM
- Identifies root cause, affected files, bug type
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv
from agent.state import AgentState

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# client initialized inside function after dotenv loads

RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"

TEAM_ARCHITECTURE = {
    "Backend": """
Clean Architecture (Go):
- handler/    : HTTP entry point, request/response handling
- usecase/    : Business logic layer
- repository/ : Data access layer (DB queries)
- entity/     : Domain models and structs
- presenter/  : Response formatting
- ops/db/     : Database connections

Analysis Strategy:
1. handler   → check request validation and error handling
2. usecase   → check business logic and error propagation
3. repository→ check DB queries
4. entity    → check domain model fields
""",
    "AOL (Mobile)": """
Flutter/Kotlin Mobile Architecture:
- lib/blocs/   : State management (BLoC pattern)
- lib/screens/ : UI screens
- lib/repos/   : API and data repositories
- lib/models/  : Data models

Analysis Strategy:
1. Check BLoC state transitions
2. Check API calls for missing error handling or timeouts
3. Check UI for incorrect widget rebuilds
""",
    "DevOps": """
Infrastructure Architecture:
- helm/       : Kubernetes Helm charts
- terraform/  : Infrastructure as code
- scripts/    : Automation scripts

Analysis Strategy:
1. Check Helm values for resource limits and configs
2. Check Terraform for misconfigurations
3. Check automation scripts for logic errors
""",
    "Platform": """
Platform Architecture:
- manifests/  : Kubernetes YAML manifests
- config/     : Configuration files

Analysis Strategy:
1. Check K8s manifests for misconfigurations
2. Check Go services for logic errors
""",
    "Portal": """
Portal Frontend Architecture:
- src/components/ : React/JS components
- src/pages/      : Page components
- src/api/        : API integration

Analysis Strategy:
1. Check API calls for incorrect handling
2. Check component state management
3. Check rendering logic
""",
}


def build_analysis_prompt(state):
    ticket_id    = state["ticket_id"]
    title        = state.get("title", "")
    team         = state.get("team", "")
    microservice = state.get("microservice", "")
    description  = state.get("description", "")
    expected     = state.get("expected", "")
    actual       = state.get("actual", "")
    files        = state.get("files", [])
    arch_context = TEAM_ARCHITECTURE.get(team, "")

    file_contents = ""
    for f in files:
        content = f.get("content", "")
        if content:
            file_contents += f"\n--- FILE: {f['path']} ---\n{content}\n--- END ---\n"

    return f"""You are Dev Buddy, an expert software engineer analyzing a bug.

TICKET:
- ID          : {ticket_id}
- Title       : {title}
- Team        : {team}
- Microservice: {microservice}
- Description : {description}
- Expected    : {expected}
- Actual      : {actual}

ARCHITECTURE:
{arch_context}

CODE FILES:
{file_contents if file_contents else "No code files available."}

Respond ONLY in this exact JSON format (no markdown, no extra text):
{{
    "root_cause": "Clear explanation referencing specific file names and functions",
    "affected_files": ["list of affected file paths"],
    "affected_layer": "which architecture layer has the bug",
    "severity": "Critical/High/Medium/Low",
    "bug_type": "type of bug (e.g. unhandled exception, missing validation)",
    "analysis_summary": "2-3 sentence technical summary"
}}"""


def researcher_node(state: AgentState) -> AgentState:
    ticket_id = state["ticket_id"]
    print(f"\n{BOLD}{CYAN}[RESEARCHER NODE] Analyzing: {ticket_id}{RESET}")
    print(f"  Files to analyze: {len(state.get('files', []))}")

    if not state.get("files"):
        print(f"  {YELLOW}No files available — skipping LLM analysis{RESET}")
        return {
            **state,
            "root_cause"      : "No code files found for analysis",
            "affected_files"  : [],
            "affected_layer"  : "unknown",
            "severity"        : "Unknown",
            "bug_type"        : "Unknown",
            "analysis_summary": "No files were fetched from GitHub.",
            "next_node"       : "coder",
        }

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    client = Groq(api_key=GROQ_API_KEY)
    print(f"  Sending to Groq ({GROQ_MODEL})...")

    try:
        prompt   = build_analysis_prompt(state)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role"   : "system",
                    "content": "You are Dev Buddy. Always respond with valid JSON only. No markdown, no extra text."
                },
                {
                    "role"   : "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=1500,
        )

        raw = response.choices[0].message.content.strip()

        # Clean markdown
        if raw.startswith("```"):
            lines = [l for l in raw.split("\n") if not l.startswith("```")]
            raw   = "\n".join(lines)

        analysis = json.loads(raw)
        print(f"  {GREEN}Analysis complete{RESET}")
        print(f"  Bug Type      : {analysis.get('bug_type', 'N/A')}")
        print(f"  Severity      : {analysis.get('severity', 'N/A')}")
        print(f"  Affected Layer: {analysis.get('affected_layer', 'N/A')}")

        return {
            **state,
            "root_cause"      : analysis.get("root_cause", ""),
            "affected_files"  : analysis.get("affected_files", []),
            "affected_layer"  : analysis.get("affected_layer", ""),
            "severity"        : analysis.get("severity", ""),
            "bug_type"        : analysis.get("bug_type", ""),
            "analysis_summary": analysis.get("analysis_summary", ""),
            "next_node"       : "coder",
            "error"           : None,
        }

    except json.JSONDecodeError as e:
        print(f"  {YELLOW}JSON parse error: {e}{RESET}")
        return {
            **state,
            "root_cause"      : raw[:500] if "raw" in dir() else "Parse error",
            "affected_files"  : [],
            "affected_layer"  : "unknown",
            "severity"        : "Unknown",
            "bug_type"        : "Unknown",
            "analysis_summary": "Analysis parse failed",
            "next_node"       : "coder",
        }
    except Exception as e:
        print(f"  {RED}Groq error: {e}{RESET}")
        return {**state, "error": str(e), "next_node": "coder"}
