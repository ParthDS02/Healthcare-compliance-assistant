def get_retriever(vector_db):

    retriever = vector_db.as_retriever(
        search_kwargs={"k": 5}
    )

    return retriever