from langgraph.graph import END, START, StateGraph

from app.orchestration.nodes.execute_plan import execute_plan_node
from app.orchestration.nodes.plan import plan_node, route_after_plan
from app.orchestration.nodes.synthesize import synthesize_node
from app.orchestration.nodes.verify import route_after_verify, verify_node
from app.orchestration.state import GraphContext, GraphState


def build_retrieval_graph():
    builder = StateGraph(GraphState, context_schema=GraphContext)
    builder.add_node("plan", plan_node)
    builder.add_node("execute_plan", execute_plan_node)
    builder.add_edge(START, "plan")
    builder.add_conditional_edges(
        "plan",
        route_after_plan,
        {
            "execute_plan": "execute_plan",
            "synthesize": END,
        },
    )
    builder.add_edge("execute_plan", END)
    return builder.compile()


def build_full_graph():
    builder = StateGraph(GraphState, context_schema=GraphContext)
    builder.add_node("plan", plan_node)
    builder.add_node("execute_plan", execute_plan_node)
    builder.add_node("synthesize", synthesize_node)
    builder.add_node("verify", verify_node)
    builder.add_edge(START, "plan")
    builder.add_conditional_edges(
        "plan",
        route_after_plan,
        {
            "execute_plan": "execute_plan",
            "synthesize": "synthesize",
        },
    )
    builder.add_edge("execute_plan", "synthesize")
    builder.add_edge("synthesize", "verify")
    builder.add_conditional_edges(
        "verify",
        route_after_verify,
        {
            "retry": "synthesize",
            "end": END,
        },
    )
    return builder.compile()


retrieval_graph = build_retrieval_graph()
full_graph = build_full_graph()
