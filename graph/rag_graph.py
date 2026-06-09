from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.nodes import make_condense_question_node, make_retrieve_node, make_generate_node
from vectorstore.chroma_db import load_vector_store
from vectorstore.retriever import get_retriever
from ingestion.embeddings import get_embeddings
from llm.groq_model import load_model


def build_graph():
    """Build and compile a fresh RAG graph (call after ingestion to pick up new data)."""

    embeddings  = get_embeddings()
    vector_db   = load_vector_store(embeddings)
    retriever   = get_retriever(vector_db)
    llm         = load_model()

    condense_node = make_condense_question_node(llm)
    retrieve_node = make_retrieve_node(retriever)
    generate_node = make_generate_node(llm)

    workflow = StateGraph(GraphState)

    workflow.add_node("condense", condense_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)

    workflow.set_entry_point("condense")

    workflow.add_edge("condense", "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()