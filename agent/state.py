"""
DEV BUDDY - AgentState
The shared state object passed between all nodes in the LangGraph pipeline.
"""

from typing import TypedDict, List, Optional


class FileData(TypedDict):
    name        : str
    path        : str
    download_url: str
    content     : str
    source      : str


class FixData(TypedDict):
    file_path   : str
    explanation : str
    fixed_code  : str


class AgentState(TypedDict):
    # ── Input ──────────────────────────────────────────────
    ticket_id   : str
    title       : str
    status      : str
    priority    : str
    severity    : str
    reporter    : str
    assignee    : str
    description : str
    environment : str
    expected    : str
    actual      : str
    pr_link     : str

    # ── Router Node output ─────────────────────────────────
    team        : str
    microservice: str

    # ── Searcher Node output ───────────────────────────────
    repo_name   : str
    branch      : str
    files       : List[FileData]
    search_attempts: int          # tracks retry count

    # ── Researcher Node output ─────────────────────────────
    root_cause      : str
    bug_type        : str
    affected_layer  : str
    affected_files  : List[str]
    analysis_summary: str

    # ── Coder Node output ──────────────────────────────────
    fix_summary   : str
    fixes         : List[FixData]
    testing_steps : List[str]
    prevention    : str

    # ── Control flags ──────────────────────────────────────
    error         : Optional[str]   # set if something goes wrong
    next_node     : Optional[str]   # used for conditional routing
