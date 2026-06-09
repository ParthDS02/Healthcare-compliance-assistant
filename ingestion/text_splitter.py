from langchain.text_splitter import RecursiveCharacterTextSplitter
from config.settings import CHUNK_SIZE, CHUNK_OVERLAP

def find_chunk_lines(page_content, chunk_text):
    # Try exact match first
    idx = page_content.find(chunk_text)
    if idx != -1:
        start_line = page_content[:idx].count('\n') + 1
        end_line = start_line + chunk_text.count('\n')
        return start_line, end_line
    
    # Try finding with stripped whitespace
    stripped_chunk = chunk_text.strip()
    idx = page_content.find(stripped_chunk)
    if idx != -1:
        start_line = page_content[:idx].count('\n') + 1
        end_line = start_line + stripped_chunk.count('\n')
        return start_line, end_line
    
    # If still not found, try matching by first few characters
    prefix = chunk_text.strip()[:30]
    if len(prefix) >= 10:
        idx = page_content.find(prefix)
        if idx != -1:
            start_line = page_content[:idx].count('\n') + 1
            end_line = start_line + chunk_text.count('\n')
            return start_line, end_line
            
    # Fallback
    return 1, page_content.count('\n') + 1


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    chunks = []
    for doc in documents:
        # Split each page document individually to map chunk back to its source page content
        page_chunks = splitter.split_documents([doc])
        for chunk in page_chunks:
            start_line, end_line = find_chunk_lines(doc.page_content, chunk.page_content)
            chunk.metadata["start_line"] = start_line
            chunk.metadata["end_line"] = end_line
            chunks.append(chunk)

    return chunks