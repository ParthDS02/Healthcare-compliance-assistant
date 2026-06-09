import os

def make_condense_question_node(llm):

    def condense_question_node(state):
        chat_history = state.get("chat_history", [])
        question = state["question"]

        if not chat_history:
            state["condensed_question"] = question
            print(f"\n[CONDENSE] No chat history. Using original: '{question}'")
            return state

        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
        prompt = f"""You are an expert system that reformulates questions. Given the following chat history and a follow-up question, rephrase the follow-up question to be a standalone question.
The standalone question must contain all necessary context from the chat history so it can be understood on its own to search a database.

CRITICAL RULE: Respond ONLY with the rephrased standalone question. Do NOT write any introduction, explanation, quotes, or notes.

Chat History:
{history_str}

Follow-up Question: {question}

Standalone Question:"""

        response = llm.invoke(prompt)
        condensed = response.content.strip().strip('"').strip("'")
        state["condensed_question"] = condensed
        print(f"\n[CONDENSE] Original: '{question}'")
        print(f"[CONDENSE] Standalone: '{condensed}'")

        return state

    return condense_question_node


def make_retrieve_node(retriever):

    def retrieve_node(state):
        query = state.get("condensed_question", state["question"])
        docs = retriever.invoke(query)
        state["context"] = docs
        print(f"[RETRIEVE] Query: '{query}' | Retrieved {len(docs)} documents.")

        return state

    return retrieve_node


def make_generate_node(llm):

    def generate_node(state):
        chat_history = state.get("chat_history", [])
        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
        query = state.get("condensed_question", state["question"])

        # Format context as clean, readable text blocks
        formatted_context_list = []
        for doc in state.get('context', []):
            src = os.path.basename(doc.metadata.get('source', 'Unknown'))
            page = int(doc.metadata.get('page', 0)) + 1
            formatted_context_list.append(
                f"Source Document: {src} (Page {page})\n"
                f"Content:\n{doc.page_content}"
            )
        context_str = "\n\n---\n\n".join(formatted_context_list)

        prompt = f"""You are a professional medical device regulatory and compliance intelligence assistant.
Your task is to answer the user's question based strictly on the provided Context and Chat History.

FORMATTING REQUIREMENTS:
1. Be highly structured and professional. Use markdown elements (like clean headings, bold sub-headers, and bulleted/numbered lists) to break down complex procedures, clauses, and technical requirements.
2. If comparing metrics, specifications, or processes, format them in a clean markdown table.
3. Keep sentences clear, precise, and professional.
4. Bold key terms, regulations (e.g., **ISO 13485**, **21 CFR Part 820**), and metrics.
5. Be correct, accurate, direct, and concise. Avoid unnecessarily long, verbose, or redundant text. Keep the focus entirely on answering the user's question.
6. CRITICAL RULE: If the answer to the user's question cannot be found or is not available in the provided context, you MUST respond ONLY with the exact sentence: "The requested information is not mentioned in the provided PDF." Do NOT output any other text, greetings, explanations, markdown tables, headings, or lists.

Chat History:
{history_str}

Context:
{context_str}

Question: {query}

Answer:"""

        response = llm.invoke(prompt)
        state["answer"] = response.content
        print(f"[GENERATE] Answered question: '{query}'")

        return state

    return generate_node
