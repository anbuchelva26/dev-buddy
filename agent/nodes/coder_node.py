"""
DEV BUDDY - Coder Node
Stage 4: Suggestion Generation
- Takes root cause from Researcher Node
- Generates concrete code fix using Groq LLM
- Produces final output with fix, testing steps, prevention advice
- Auto-posts analysis result as Jira comment
"""

import os
import json
import requests
from requests.auth import HTTPBasicAuth
from groq import Groq
from dotenv import load_dotenv
from agent.state import AgentState

load_dotenv()

# client initialized inside function after dotenv loads

RESET   = "\033[0m"
BOLD    = "\033[1m"
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
MAGENTA = "\033[95m"


def post_jira_comment(ticket_id, state):
    """Post analysis result as a comment on the Jira ticket"""
    JIRA_URL       = os.getenv("JIRA_URL")
    JIRA_EMAIL     = os.getenv("JIRA_EMAIL")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

    if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
        print(f"  {YELLOW}Jira credentials missing — skipping comment{RESET}")
        return False

    auth    = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    # Build comment text
    root_cause     = state.get("root_cause", "N/A")
    fix_summary    = state.get("fix_summary", "N/A")
    severity       = state.get("severity", "N/A")
    bug_type       = state.get("bug_type", "N/A")
    affected_layer = state.get("affected_layer", "N/A")
    team           = state.get("team", "N/A")
    microservice   = state.get("microservice", "N/A")
    repo_name      = state.get("repo_name", "N/A")
    testing_steps  = state.get("testing_steps", [])
    prevention     = state.get("prevention", "N/A")
    fixes          = state.get("fixes", [])

    # Build fix details
    fix_details = ""
    for i, fix in enumerate(fixes, 1):
        fix_details += f"\n*Fix #{i} — {fix.get('file_path', '')}*\n"
        fix_details += f"{fix.get('explanation', '')}\n"

    # Build testing steps
    steps_text = ""
    for i, step in enumerate(testing_steps, 1):
        steps_text += f"{i}. {step}\n"

    comment_body = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": f"[Dev Buddy AI Analysis] - {ticket_id}",
                            "marks": [{"type": "strong"}]
                        }
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "🔍 Analysis Results", "marks": [{"type": "strong"}]}
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": f"Team: {team} | Microservice: {microservice} | Repo: {repo_name}"}
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": f"Severity: {severity} | Bug Type: {bug_type} | Layer: {affected_layer}"}
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "⚠ Root Cause", "marks": [{"type": "strong"}]}
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": root_cause}]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "⚡ Fix Summary", "marks": [{"type": "strong"}]}
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": fix_summary}]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "📁 Files to Fix", "marks": [{"type": "strong"}]}
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": fix_details or "N/A"}]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "🧪 Testing Steps", "marks": [{"type": "strong"}]}
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": steps_text or "N/A"}]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "🛡 Prevention", "marks": [{"type": "strong"}]}
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": prevention}]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "— Posted automatically by Dev Buddy AI", "marks": [{"type": "em"}]}
                    ]
                }
            ]
        }
    }

    url      = f"{JIRA_URL}/rest/api/3/issue/{ticket_id}/comment"
    response = requests.post(url, headers=headers, auth=auth, json=comment_body)

    if response.status_code in (200, 201):
        print(f"  {GREEN}✅ Jira comment posted on {ticket_id}{RESET}")
        return True
    else:
        print(f"  {YELLOW}Jira comment failed: {response.status_code}{RESET}")
        return False


def build_fix_prompt(state):
    ticket_id      = state["ticket_id"]
    title          = state.get("title", "")
    team           = state.get("team", "")
    microservice   = state.get("microservice", "")
    description    = state.get("description", "")
    root_cause     = state.get("root_cause", "")
    affected_files = state.get("affected_files", [])
    affected_layer = state.get("affected_layer", "")
    bug_type       = state.get("bug_type", "")
    severity       = state.get("severity", "")
    files          = state.get("files", [])

    file_contents = ""
    for f in files:
        if f["path"] in affected_files or not affected_files:
            content = f.get("content", "")
            if content:
                file_contents += f"\n--- FILE: {f['path']} ---\n{content}\n--- END ---\n"

    return f"""You are Dev Buddy, an expert software engineer generating a production-ready fix.

TICKET:
- ID          : {ticket_id}
- Title       : {title}
- Team        : {team}
- Microservice: {microservice}
- Description : {description}

BUG ANALYSIS:
- Root Cause    : {root_cause}
- Bug Type      : {bug_type}
- Severity      : {severity}
- Affected Layer: {affected_layer}
- Affected Files: {affected_files}

BUGGY CODE:
{file_contents if file_contents else "No code available."}

Respond ONLY in this exact JSON format (no markdown, no extra text):
{{
    "fix_summary": "One sentence describing what the fix does",
    "fixes": [
        {{
            "file_path": "path/to/file.go",
            "explanation": "What was wrong and what was changed",
            "fixed_code": "Complete fixed version of the function or file"
        }}
    ],
    "testing_steps": [
        "Step 1 to verify the fix works",
        "Step 2 to verify the fix works"
    ],
    "prevention": "How to prevent this type of bug in the future"
}}"""


def print_final_report(state):
    print(f"\n{'='*60}")
    print(f"{BOLD}{CYAN}  FINAL REPORT: [{state['ticket_id']}]{RESET}")
    print(f"{'='*60}")
    print(f"{BOLD}  Title        :{RESET} {state.get('title', '')}")
    print(f"{BOLD}  Team         :{RESET} {state.get('team', '')}")
    print(f"{BOLD}  Microservice :{RESET} {state.get('microservice', '')}")
    print(f"{BOLD}  Repo         :{RESET} {state.get('repo_name', '')}")
    print(f"{BOLD}  Severity     :{RESET} {RED}{state.get('severity', '')}{RESET}")
    print(f"{BOLD}  Bug Type     :{RESET} {state.get('bug_type', '')}")
    print(f"{BOLD}  Affected     :{RESET} {state.get('affected_layer', '')} layer")
    print(f"\n{BOLD}  ROOT CAUSE:{RESET}")
    print(f"  {state.get('root_cause', '')}")
    print(f"\n{BOLD}  FIX SUMMARY:{RESET}")
    print(f"  {state.get('fix_summary', '')}")

    for i, fix in enumerate(state.get("fixes", []), 1):
        print(f"\n{BOLD}{MAGENTA}  FIX #{i} — {fix.get('file_path', '')}{RESET}")
        print(f"  {BOLD}What changed:{RESET} {fix.get('explanation', '')}")
        print(f"\n  {BOLD}Fixed Code:{RESET}")
        for line in fix.get("fixed_code", "").split("\n"):
            print(f"  {GREEN}{line}{RESET}")

    steps = state.get("testing_steps", [])
    if steps:
        print(f"\n{BOLD}  TESTING STEPS:{RESET}")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")

    prevention = state.get("prevention", "")
    if prevention:
        print(f"\n{BOLD}  PREVENTION:{RESET}")
        print(f"  {YELLOW}{prevention}{RESET}")

    print(f"\n{'='*60}\n")


def coder_node(state: AgentState) -> AgentState:
    ticket_id = state["ticket_id"]
    print(f"\n{BOLD}{CYAN}[CODER NODE] Generating fix for: {ticket_id}{RESET}")

    if not state.get("root_cause") or state["root_cause"] == "No code files found for analysis":
        print(f"  {YELLOW}No root cause available — skipping fix generation{RESET}")
        return {
            **state,
            "fix_summary"  : "Fix could not be generated — no code files available",
            "fixes"        : [],
            "testing_steps": [],
            "prevention"   : "",
            "next_node"    : "end",
        }

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    client       = Groq(api_key=GROQ_API_KEY)
    print(f"  Sending to Groq ({GROQ_MODEL}) for fix generation...")

    try:
        prompt   = build_fix_prompt(state)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role"   : "system",
                    "content": "You are Dev Buddy. Generate production-ready code fixes. Always respond with valid JSON only. No markdown."
                },
                {
                    "role"   : "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=3000,
        )

        raw = response.choices[0].message.content.strip()

        # Clean markdown
        if raw.startswith("```"):
            lines = [l for l in raw.split("\n") if not l.startswith("```")]
            raw   = "\n".join(lines)

        fix = json.loads(raw)
        print(f"  {GREEN}Fix generated successfully{RESET}")
        print(f"  Files fixed: {len(fix.get('fixes', []))}")

        updated_state = {
            **state,
            "fix_summary"  : fix.get("fix_summary", ""),
            "fixes"        : fix.get("fixes", []),
            "testing_steps": fix.get("testing_steps", []),
            "prevention"   : fix.get("prevention", ""),
            "next_node"    : "end",
            "error"        : None,
        }

        # Print final report
        print_final_report(updated_state)

        # Post comment to Jira
        print(f"  Posting analysis to Jira...")
        post_jira_comment(ticket_id, updated_state)

        return updated_state

    except json.JSONDecodeError as e:
        print(f"  {YELLOW}JSON parse error: {e}{RESET}")
        return {
            **state,
            "fix_summary"  : "Fix generated but could not be parsed",
            "fixes"        : [],
            "testing_steps": [],
            "prevention"   : "",
            "next_node"    : "end",
        }
    except Exception as e:
        print(f"  {RED}Groq error: {e}{RESET}")
        return {**state, "error": str(e), "next_node": "end"}