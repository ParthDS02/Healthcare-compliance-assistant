from typing import TypedDict, List, Dict

class GraphState(TypedDict):

    question: str

    chat_history: List[Dict[str, str]]

    condensed_question: str

    context: list

    answer: str