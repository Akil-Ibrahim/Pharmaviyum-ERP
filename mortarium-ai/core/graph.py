from langgraph.graph import StateGraph, END
from core.state import GraphState
from core.nodes import retrieve, enrich_from_postgres, grade_documents, transform_query, generate

def build_mortarium_graph() -> StateGraph:
    workflow = StateGraph(GraphState)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("enrich_db", enrich_from_postgres)
    workflow.add_node("grade", grade_documents)
    workflow.add_node("rewrite", transform_query)
    workflow.add_node("generate", generate)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "enrich_db")
    workflow.add_edge("enrich_db", "grade")

    def route_after_grading(state: GraphState):
        if state["retry_count"] >= 2 or state["documents"]:
            return "generate"
        return "rewrite"

    workflow.add_conditional_edges("grade", route_after_grading, {"rewrite": "rewrite", "generate": "generate"})
    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("generate", END)

    return workflow.compile()
