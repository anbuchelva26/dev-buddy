"""
DEV BUDDY - Searcher Node (v2 - Dynamic Public GitHub Search)
Stage 2: Contextual Mapping

Search priority:
1. Configured org (Jira-Above9) — exact match
2. Configured org (Jira-Above9) — fuzzy match
3. PUBLIC GitHub search — by microservice name + language
4. PUBLIC GitHub search — by ticket keywords
"""

import os
import re
import requests
from agent.state import AgentState

BASE_URL            = "https://api.github.com"
MAX_SEARCH_ATTEMPTS = 3

TEAM_FOLDERS = {
    "Backend"     : ["handler", "usecase", "repository", "entity", "presenter", "ops", "internal", "cmd", "pkg", "service", "controller"],
    "AOL (Mobile)": ["lib", "src", "android", "ios", "app", "flutter"],
    "DevOps"      : ["helm", "terraform", "scripts", "k8s", "deploy", "infra"],
    "Platform"    : ["manifests", "config", "charts", "operator", "api"],
    "Portal"      : ["src", "components", "pages", "api", "app", "views"],
    "Unknown"     : ["src", "lib", "app", "internal", "pkg", "service"],
}

TEAM_EXTENSIONS = {
    "Backend"     : [".go", ".java", ".py", ".ts", ".js"],
    "AOL (Mobile)": [".kt", ".dart", ".swift", ".java", ".xml"],
    "DevOps"      : [".yaml", ".yml", ".tf", ".py", ".sh"],
    "Platform"    : [".yaml", ".yml", ".go"],
    "Portal"      : [".js", ".ts", ".jsx", ".tsx", ".vue"],
    "Unknown"     : [".go", ".py", ".ts", ".js", ".java"],
}

TEAM_LANGUAGES = {
    "Backend"     : ["Go", "Java", "Python", "TypeScript"],
    "AOL (Mobile)": ["Dart", "Kotlin", "Swift"],
    "DevOps"      : ["HCL", "Shell", "Python"],
    "Platform"    : ["Go", "YAML"],
    "Portal"      : ["JavaScript", "TypeScript"],
    "Unknown"     : [],
}

RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BLUE   = "\033[94m"


def get_headers():
    GITHUB_PAT = os.getenv("GITHUB_PAT", "")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_PAT:
        headers["Authorization"] = f"token {GITHUB_PAT}"
    return headers


def extract_keywords(text):
    stop_words = {"the", "a", "an", "is", "in", "on", "at", "to", "for",
                  "of", "and", "or", "but", "not", "with", "this", "that",
                  "api", "error", "bug", "issue", "fix", "returns", "return",
                  "when", "where", "how", "what", "why", "should", "does"}
    words    = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_-]{2,}\b', text)
    keywords = [w.lower() for w in words if w.lower() not in stop_words]
    return " ".join(keywords[:3])


def find_in_org(microservice, description=""):
    GITHUB_ORG = os.getenv("GITHUB_ORG", "Jira-Above9")
    HEADERS    = get_headers()

    # Exact match
    r = requests.get(f"{BASE_URL}/repos/{GITHUB_ORG}/{microservice}", headers=HEADERS)
    if r.status_code == 200:
        repo = r.json()
        print(f"  {GREEN}[Org] Exact match: {repo['full_name']}{RESET}")
        return repo["full_name"], repo["default_branch"]

    # Fuzzy match across org repos
    r = requests.get(f"{BASE_URL}/orgs/{GITHUB_ORG}/repos?per_page=100", headers=HEADERS)
    if r.status_code != 200:
        return None, None

    repos    = r.json()
    ms_lower = microservice.lower().replace("-", "").replace("_", "")
    for repo in (repos if isinstance(repos, list) else []):
        rn = repo["name"].lower().replace("-", "").replace("_", "")
        if ms_lower in rn or rn in ms_lower:
            print(f"  {GREEN}[Org] Fuzzy match: {repo['full_name']}{RESET}")
            return repo["full_name"], repo["default_branch"]

    return None, None


def search_public_github(microservice, team, title="", attempt=1):
    HEADERS   = get_headers()
    languages = TEAM_LANGUAGES.get(team, [])

    if attempt == 1:
        lang    = f" language:{languages[0]}" if languages else ""
        query   = f"{microservice}{lang}"
    elif attempt == 2:
        query   = microservice
    else:
        kw      = extract_keywords(title or microservice)
        lang    = f" language:{languages[0]}" if languages else ""
        query   = f"{kw}{lang}"

    print(f"  {BLUE}[Public GitHub] Searching: '{query}'{RESET}")

    r = requests.get(f"{BASE_URL}/search/repositories",
                     headers=HEADERS,
                     params={"q": query, "sort": "stars", "order": "desc", "per_page": 5})

    if r.status_code != 200:
        print(f"  {YELLOW}Search API error: {r.status_code}{RESET}")
        return None, None

    items    = r.json().get("items", [])
    ms_lower = microservice.lower().replace("-", "").replace("_", "")
    best     = None

    for repo in items:
        rn = repo["name"].lower().replace("-", "").replace("_", "")
        if ms_lower in rn or rn in ms_lower:
            best = repo
            break

    if not best and items:
        best = items[0]

    if best:
        print(f"  {GREEN}[Public] Found: {best['full_name']} ⭐{best['stargazers_count']}{RESET}")
        return best["full_name"], best["default_branch"]

    return None, None


def find_repo(microservice, team="Unknown", title="", description="", attempt=1):
    # Strategy 1+2: Org search
    print(f"  Trying configured org...")
    repo, branch = find_in_org(microservice, description)
    if repo:
        return repo, branch, "org"

    # Strategy 3+4: Public GitHub
    print(f"  Trying public GitHub search...")
    repo, branch = search_public_github(microservice, team, title, attempt)
    if repo:
        return repo, branch, "public"

    return None, None, None


def fetch_files_recursive(repo_full_name, folder_path, branch, extensions, depth=0):
    if depth > 8:
        return []
    HEADERS  = get_headers()
    r = requests.get(f"{BASE_URL}/repos/{repo_full_name}/contents/{folder_path}?ref={branch}", headers=HEADERS)
    if r.status_code != 200:
        return []
    items = r.json()
    if not isinstance(items, list):
        return []
    files = []
    for item in items:
        if item["type"] == "file" and any(item["name"].endswith(e) for e in extensions):
            files.append({"name": item["name"], "path": item["path"],
                          "download_url": item.get("download_url", ""), "content": "", "source": "folder_scan"})
        elif item["type"] == "dir":
            files.extend(fetch_files_recursive(repo_full_name, item["path"], branch, extensions, depth+1))
    return files


def fetch_root_files(repo_full_name, branch, extensions):
    HEADERS  = get_headers()
    r = requests.get(f"{BASE_URL}/repos/{repo_full_name}/contents?ref={branch}", headers=HEADERS)
    if r.status_code != 200:
        return []
    items = r.json()
    if not isinstance(items, list):
        return []
    return [{"name": i["name"], "path": i["path"],
             "download_url": i.get("download_url", ""), "content": "", "source": "root_scan"}
            for i in items if i["type"] == "file" and any(i["name"].endswith(e) for e in extensions)]


def fetch_file_content(download_url):
    if not download_url:
        return ""
    r = requests.get(download_url, headers=get_headers())
    return r.text[:3000] if r.status_code == 200 else ""


def fetch_pr_files(repo_full_name, pr_link):
    if not pr_link or "/pull/" not in pr_link:
        return []
    pr_number = pr_link.split("/pull/")[-1].strip("/")
    r = requests.get(f"{BASE_URL}/repos/{repo_full_name}/pulls/{pr_number}/files", headers=get_headers())
    if r.status_code != 200:
        return []
    return [{"name": f["filename"].split("/")[-1], "path": f["filename"],
             "download_url": f.get("raw_url", ""), "content": "", "source": "pr"}
            for f in r.json()]


def searcher_node(state: AgentState) -> AgentState:
    ticket_id       = state["ticket_id"]
    team            = state.get("team", "Unknown")
    microservice    = state.get("microservice", "")
    title           = state.get("title", "")
    description     = state.get("description", "")
    pr_link         = state.get("pr_link", "")
    search_attempts = state.get("search_attempts", 0) + 1

    print(f"\n{BOLD}{CYAN}[SEARCHER NODE] Attempt {search_attempts}/{MAX_SEARCH_ATTEMPTS}{RESET}")
    print(f"  Team: {team} | Microservice: {microservice}")

    repo_full_name, branch, source = find_repo(
        microservice=microservice, team=team,
        title=title, description=description, attempt=search_attempts,
    )

    if not repo_full_name:
        print(f"  {RED}No repo found anywhere for: {microservice}{RESET}")
        if search_attempts >= MAX_SEARCH_ATTEMPTS:
            return {**state, "search_attempts": search_attempts,
                    "next_node": "researcher", "error": f"No repo found after {MAX_SEARCH_ATTEMPTS} attempts"}
        return {**state, "search_attempts": search_attempts, "next_node": "searcher"}

    print(f"  Source: [{source}] | Repo: {repo_full_name} | Branch: {branch}")

    folders    = TEAM_FOLDERS.get(team, TEAM_FOLDERS["Unknown"])
    extensions = TEAM_EXTENSIONS.get(team, TEAM_EXTENSIONS["Unknown"])
    all_files  = []

    if pr_link and "/pull/" in pr_link:
        print(f"  PR link found — fetching PR files...")
        all_files = fetch_pr_files(repo_full_name, pr_link)
        print(f"  {GREEN}Found {len(all_files)} file(s) from PR{RESET}")
    else:
        print(f"  Scanning folders: {folders[:4]}...")
        for folder in folders:
            ff = fetch_files_recursive(repo_full_name, folder, branch, extensions)
            if ff:
                print(f"  {GREEN}Found {len(ff)} file(s) in /{folder}{RESET}")
                all_files.extend(ff)
            if len(all_files) >= 10:
                break

        if not all_files:
            print(f"  {YELLOW}No files in known folders — scanning root...{RESET}")
            all_files = fetch_root_files(repo_full_name, branch, extensions)
            if all_files:
                print(f"  {GREEN}Found {len(all_files)} file(s) at root{RESET}")

    if not all_files and search_attempts < MAX_SEARCH_ATTEMPTS:
        print(f"  {YELLOW}No files found. Retrying...{RESET}")
        return {**state, "repo_name": repo_full_name, "branch": branch,
                "search_attempts": search_attempts, "next_node": "searcher"}

    print(f"  Fetching file contents (up to 10 files)...")
    for f in all_files[:10]:
        f["content"] = fetch_file_content(f["download_url"])
        if f["content"]:
            print(f"  {GREEN}Fetched: {f['path']}{RESET}")

    print(f"  Total files collected: {min(len(all_files), 10)}")

    return {
        **state,
        "repo_name"      : repo_full_name,
        "branch"         : branch,
        "files"          : all_files[:10],
        "search_attempts": search_attempts,
        "next_node"      : "researcher",
        "error"          : None,
    }