"""
api/main.py – FastAPI server entry point.

Run with:
    uvicorn api.main:app --reload
"""

import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="Healthcare Compliance & Intelligence Assistant API",
    description="RAG-powered Q&A over healthcare and medical device regulatory documents",
    version="1.0.0"
)

app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
