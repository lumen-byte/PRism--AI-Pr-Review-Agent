import time

from langgraph.graph import END, START, StateGraph

from app.agents.nodes.diff_analyzer import diff_analyzer
from app.agents.nodes.github_publisher import github_publisher
from app.agents.nodes.logic_agent import logic_agent
from app.agents.nodes.orchestrator import orchestrator
from app.agents.nodes.quality_agent import quality_agent
from app.agents.nodes.security_agent import security_agent
from app.agents.state import ReviewState
from app.core.logger import logger
from app.core.metrics import prism_review_duration_seconds, prism_reviews_total


def build_review_graph() -> StateGraph:
    logger.info("Compiling ReviewState Graph...")
    workflow = StateGraph(ReviewState)

    # Add Nodes
    workflow.add_node("diff_analyzer", diff_analyzer)
    workflow.add_node("security_agent", security_agent)
    workflow.add_node("quality_agent", quality_agent)
    workflow.add_node("logic_agent", logic_agent)
    workflow.add_node("orchestrator", orchestrator)
    workflow.add_node("github_publisher", github_publisher)

    # Add Edges
    workflow.add_edge(START, "diff_analyzer")

    # Diff analyzer fans out to specialized agents in parallel
    workflow.add_edge("diff_analyzer", "security_agent")
    workflow.add_edge("diff_analyzer", "quality_agent")
    workflow.add_edge("diff_analyzer", "logic_agent")

    # Specialized agents fan in to the orchestrator
    workflow.add_edge("security_agent", "orchestrator")
    workflow.add_edge("quality_agent", "orchestrator")
    workflow.add_edge("logic_agent", "orchestrator")

    # Finally, publish and end
    workflow.add_edge("orchestrator", "github_publisher")
    workflow.add_edge("github_publisher", END)

    return workflow.compile()


# Singleton graph initialization
review_graph = build_review_graph()


async def run_review_graph(initial_state: ReviewState) -> ReviewState:
    logger.info(f"Invoking review graph for PR {initial_state.get('pr_number')}")
    start_time = time.time()

    # langgraph invoke processes the state through the graph
    final_state = await review_graph.ainvoke(initial_state)

    duration = time.time() - start_time
    logger.info(
        f"Graph execution complete for PR {initial_state.get('pr_number')} in {duration:.2f} seconds"
    )

    # Track Metrics
    repo = initial_state.get("repo", "unknown")
    decision = final_state.get("review_decision", "COMMENTED")
    prism_reviews_total.labels(repo=repo, decision=decision).inc()
    prism_review_duration_seconds.observe(duration)

    return final_state
