from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from graph.rag_graph import build_graph
from utils.citation_formatter import format_sources

router = APIRouter()
_graph = None  # lazy singleton


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


class ChatMessage(BaseModel):
    role: str
    content: str


class QuestionRequest(BaseModel):
    question: str
    chat_history: List[ChatMessage] = []


@router.post("/ask")
def ask_question(request: QuestionRequest):
    history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.chat_history]

    result = get_graph().invoke({
        "question": request.question,
        "chat_history": history_dicts
    })

    citations = format_sources(result.get("context", []))

    return {
        "answer": result.get("answer", ""),
        "sources": citations
    }
