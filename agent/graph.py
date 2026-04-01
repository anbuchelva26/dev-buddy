"""
DEV BUDDY - LangGraph State Machine
Defines the graph with nodes, edges, and conditional routing.

Flow:
START → router → searcher → researcher → coder → END
                    ↑           
                    └── retry if no files found (up to 3 times)
"""

from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes.router_node     import router_node
from agent.nodes.searcher_node   import searcher_node
from agent.nodes.researcher_node import researcher_node
from agent.nodes.coder_node      import coder_node

RESET = "\033[0m"
BOLD  = "\033[1m"
CYAN  = "\033[96m"


# ── Conditional routing functions ─────────────────────────────────────────────

def route_after_router(state: AgentState) -> str:
    """After router: go to searcher or end if error"""
    if state.get("error") and state.get("next_node") == "end":
        print(f"  Routing → END (router error)")
        return "end"
    print(f"  Routing → searcher")
    return "searcher"


def route_after_searcher(state: AgentState) -> str:
    """After searcher: retry if no files, else go to researcher"""
    next_node       = state.get("next_node", "researcher")
    search_attempts = state.get("search_attempts", 0)

    if next_node == "searcher" and search_attempts < 3:
        print(f"  Routing → searcher (retry {search_attempts}/3)")
        return "searcher"

    print(f"  Routing → researcher")
    return "researcher"


def route_after_researcher(state: AgentState) -> str:
    """After researcher: always go to coder"""
    print(f"  Routing → coder")
    return "coder"


def route_after_coder(state: AgentState) -> str:
    """After coder: always end"""
    print(f"  Routing → END")
    return "end"


# ── Build the LangGraph ───────────────────────────────────────────────────────

def build_graph():
    print(f"\n{BOLD}{CYAN}Building Dev Buddy LangGraph...{RESET}")

    # Initialize graph with AgentState
    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("router",     router_node)
    graph.add_node("searcher",   searcher_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("coder",      coder_node)

    # Set entry point
    graph.set_entry_point("router")

    # Add conditional edges
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "searcher": "searcher",
            "end"     : END,
        }
    )

    graph.add_conditional_edges(
        "searcher",
        route_after_searcher,
        {
            "searcher"  : "searcher",    # retry loop
            "researcher": "researcher",
        }
    )

    graph.add_conditional_edges(
        "researcher",
        route_after_researcher,
        {
            "coder": "coder",
        }
    )

    graph.add_conditional_edges(
        "coder",
        route_after_coder,
        {
            "end": END,
        }
    )

    # Compile the graph
    app = graph.compile()
    print(f"  Graph compiled successfully!\n")
    return app
