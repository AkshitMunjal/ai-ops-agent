from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    approve_order_node,
    create_draft_node,
    extract_node,
    human_approval_node,
    match_node,
    reject_node,
)
from agent.state import AgentState


def route_after_extract(state):
    if state.get("problems"):
        return END
    return "match"


def route_after_match(state):
    if state["status"] == "needs_review":
        return END
    return "create_draft"


def route_after_create_draft(state):
    if state["status"] == "needs_review":
        return END
    return "human_approval"


def route_after_human(state):
    if state["decision"] == "approve":
        return "approve_order"
    return "reject"


def build_graph(checkpointer):
    builder = StateGraph(AgentState)

    builder.add_node("extract", extract_node)
    builder.add_node("match", match_node)
    builder.add_node("create_draft", create_draft_node)
    builder.add_node("human_approval", human_approval_node)
    builder.add_node("approve_order", approve_order_node)
    builder.add_node("reject", reject_node)

    builder.add_edge(START, "extract")
    builder.add_conditional_edges("extract", route_after_extract)
    builder.add_conditional_edges("match", route_after_match)
    builder.add_conditional_edges("create_draft", route_after_create_draft)
    builder.add_conditional_edges("human_approval", route_after_human)
    builder.add_edge("approve_order", END)
    builder.add_edge("reject", END)

    return builder.compile(checkpointer=checkpointer)