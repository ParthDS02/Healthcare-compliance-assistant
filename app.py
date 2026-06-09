import streamlit as st
import tempfile
import os
from ingestion.pdf_loader import load_pdf
from ingestion.classifier import is_medical_document
from ingestion.text_splitter import split_documents
from ingestion.embeddings import get_embeddings
from vectorstore.chroma_db import create_vector_store
from graph.rag_graph import build_graph
from utils.citation_formatter import format_sources
from config.settings import CHROMA_PATH

st.set_page_config(
    page_title="Healthcare Compliance & Intelligence Assistant",
    page_icon="🏥",
    layout="wide"
)

# Custom premium styling injection supporting both Light and Dark modes
st.markdown("""
    <style>
        /* Import Outfit & Inter fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;800&display=swap');

        /* Modern block padding */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 1200px;
        }

        /* Heading styling */
        h1 {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 700 !important;
            padding-bottom: 0.5rem !important;
        }
        
        h2, h3, h4 {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 600 !important;
        }
        
        body, p, span, div, li {
            font-family: 'Inter', sans-serif !important;
        }

        /* Style blockquotes (used for source snippets) */
        blockquote {
            background-color: rgba(128, 128, 128, 0.08) !important;
            border-left: 3px solid #0f766e !important;
            padding: 10px 14px !important;
            margin: 8px 0px !important;
            border-radius: 0px 8px 8px 0px !important;
            font-size: 0.88rem !important;
            font-style: italic !important;
            color: inherit !important;
        }

        /* Customize sidebar selectbox styling */
        div[data-baseweb="select"] {
            border-radius: 8px !important;
        }

        /* Theme-agnostic scrollbars */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(128, 128, 128, 0.3);
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(128, 128, 128, 0.5);
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for DB status and chat history
if "db_ready" not in st.session_state:
    st.session_state["db_ready"] = os.path.exists(CHROMA_PATH) and os.path.isdir(CHROMA_PATH) and len(os.listdir(CHROMA_PATH)) > 0

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# ── Cached graph (rebuilt after every new ingestion) ──────────────────────────
@st.cache_resource(show_spinner=False)
def get_graph():
    return build_graph()

# ── Page header ───────────────────────────────────────────────────────────────
st.title("🏥 Healthcare Compliance & Intelligence Assistant")
st.caption("RAG Based, AI-Driven Compliance & Regulatory Intelligence for Healthcare Standards")

# ── Sidebar: PDF upload, Ingestion & Sources ──────────────────────────────────
with st.sidebar:
    st.header("📄 Upload Documents")
    st.write("Upload one or more PDF files to build (or update) the knowledge base.")

    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if uploaded_files:
        if st.button("🔄 Ingest PDFs", type="primary", use_container_width=True):
            all_chunks = []
            progress_bar = st.progress(0, text="Starting…")

            for i, uploaded_file in enumerate(uploaded_files):
                progress_bar.progress(
                    (i) / len(uploaded_files),
                    text=f"Processing {uploaded_file.name}…"
                )

                # Write to a temp file so PyPDFLoader can open it by path
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name

                try:
                    docs = load_pdf(tmp_path)

                    # AI Guardrail: Verify document is medical/healthcare-related
                    sample_text = docs[0].page_content if docs else ""
                    if not is_medical_document(sample_text):
                        st.error(f"❌ Rejected **{uploaded_file.name}**: This document does not appear to be medical or healthcare-related.")
                        continue

                    # Replace temp path with the real filename
                    for doc in docs:
                        doc.metadata["source"] = uploaded_file.name

                    chunks = split_documents(docs)
                    all_chunks.extend(chunks)
                except Exception as e:
                    st.error(f"Failed to process {uploaded_file.name}: {e}")
                finally:
                    os.unlink(tmp_path)

            progress_bar.progress(1.0, text="Storing in ChromaDB…")

            try:
                embeddings = get_embeddings()
                create_vector_store(all_chunks, embeddings)

                # Clear cached graph so next query uses the fresh DB
                get_graph.clear()
                st.session_state["db_ready"] = True

                progress_bar.empty()
                st.success(
                    f"✅ Done! {len(all_chunks)} chunks ingested "
                    f"from {len(uploaded_files)} file(s)."
                )
            except Exception as e:
                st.error(f"Failed to store embeddings: {e}")

    st.markdown("---")

    if st.session_state.get("db_ready"):
        st.info("📚 Knowledge base is ready. Ask questions →")
        if st.session_state.get("chat_history"):
            if st.button("🗑️ Clear Chat History", use_container_width=True):
                st.session_state["chat_history"] = []
                st.rerun()
    else:
        st.warning("⚠️ No knowledge base yet. Upload PDFs above first.")

    # ── Sidebar Question-wise Source Inspector ──────────────────────────────────
    st.markdown("---")
    st.header("🔍 Question-wise Sources")
    
    # Filter only assistant messages with sources
    assistant_msgs = [
        msg for msg in st.session_state["chat_history"]
        if msg["role"] == "assistant" and msg.get("sources")
    ]
    
    if assistant_msgs:
        q_options = [msg.get("user_question", f"Question {idx+1}") for idx, msg in enumerate(assistant_msgs)]
        
        # Selectbox to inspect sources question-wise
        selected_q_text = st.selectbox(
            "Select question to view sources:",
            options=q_options,
            index=len(q_options) - 1,
            key="selected_question_sources"
        )
        
        # Find matching message
        selected_msg = next((msg for msg in assistant_msgs if msg.get("user_question") == selected_q_text), None)
        if selected_msg and selected_msg.get("sources"):
            for idx, citation in enumerate(selected_msg["sources"]):
                st.markdown(citation)
                if idx < len(selected_msg["sources"]) - 1:
                    st.markdown("---")
    else:
        st.info("Citations and source documents will appear here once you ask a question.")

    st.markdown("---")
    st.markdown("<p style='text-align: center; font-size: 0.8rem; opacity: 0.7;'>Created by Parth B. Mistry</p>", unsafe_allow_html=True)

# ── Main panel: Chat Interface ────────────────────────────────────────────────
st.markdown("---")

# Display previous chat messages from history (without sources cluttering the main screen)
for message in st.session_state["chat_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ask a follow-up or new question
if not st.session_state.get("db_ready"):
    st.info("📤 Upload and ingest PDFs using the sidebar to start asking questions.")
else:
    if prompt := st.chat_input("Ask a follow-up or new question..."):
        # Display user message in chat container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare history for LangGraph (only pass role and content)
        langgraph_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in st.session_state["chat_history"]
        ]

        # Add user question to history immediately
        st.session_state["chat_history"].append({"role": "user", "content": prompt})

        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base…"):
                try:
                    rag = get_graph()
                    result = rag.invoke({
                        "question": prompt,
                        "chat_history": langgraph_history
                    })

                    answer = result.get("answer", "No answer found.")
                    st.markdown(answer)

                    context = result.get("context", [])
                    sources = []
                    if context and "The requested information is not mentioned in the provided PDF." not in answer:
                        sources = format_sources(context)

                    # Add assistant response to history with the user question linked
                    st.session_state["chat_history"].append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "user_question": prompt
                    })
                    
                    # Rerun immediately to update the sidebar Question-wise Sources
                    st.rerun()

                except Exception as e:
                    err = str(e).lower()
                    st.error(f"Error: {e}")
                    if any(k in err for k in ["no such table", "does not exist", "empty", "no documents"]):
                        st.info("📤 Upload and ingest PDFs using the sidebar first.")
                    # Remove the last user message from history if generation failed
                    if st.session_state["chat_history"]:
                        st.session_state["chat_history"].pop()