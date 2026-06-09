from langchain_chroma import Chroma
from config.settings import CHROMA_PATH

def create_vector_store(chunks, embeddings):
    # Clear the existing database collection if it exists to avoid accumulating duplicates
    try:
        db = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embeddings
        )
        existing = db.get()
        if existing and "ids" in existing and existing["ids"]:
            db.delete(ids=existing["ids"])
    except Exception as e:
        # If the database doesn't exist yet or is empty, ignore
        pass

    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )

    return db

def load_vector_store(embeddings):

    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )

    return db