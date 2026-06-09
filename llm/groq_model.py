from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY, MODEL_NAME

def load_model():

    llm = ChatGroq(
        model=MODEL_NAME,
        temperature=0,
        api_key=GROQ_API_KEY
    )

    return llm
