import os


def format_sources(docs):
    """
    Format retrieved documents into numbered, deduplicated citations.
    Only unique (filename + page) combinations are shown.
    Multiple chunks from the same page are grouped under that page.
    """

    # Sort docs to prioritize real filenames (non-tmp) over temporary ones
    docs_sorted = sorted(
        docs,
        key=lambda d: 1 if os.path.basename(d.metadata.get("source", "Unknown")).startswith("tmp") else 0
    )

    # Group chunks by (source_name, page_num)
    grouped = {}
    global_seen_content = set()

    for doc in docs_sorted:
        source = doc.metadata.get("source", "Unknown Document")
        source_name = os.path.basename(source)

        page = doc.metadata.get("page", None)
        # PyPDF uses 0-indexed pages
        page_num = int(page) + 1 if page is not None else None

        # Clean/normalize chunk content to detect global duplicates
        content_stripped = doc.page_content.strip()

        # Global content deduplication: skip if this chunk content is already shown
        content_key = content_stripped[:150]
        if content_key in global_seen_content:
            continue
        global_seen_content.add(content_key)

        start_line = doc.metadata.get("start_line", None)
        end_line = doc.metadata.get("end_line", None)

        key = (source_name, page_num)
        if key not in grouped:
            grouped[key] = []

        grouped[key].append({
            "content": doc.page_content,
            "start_line": start_line,
            "end_line": end_line
        })

    # Build numbered citation list
    citations = []
    for i, ((source_name, page_num), chunks) in enumerate(grouped.items(), start=1):
        if not chunks:
            continue

        page_label = f"Page {page_num}" if page_num is not None else "Page N/A"
        citation_lines = [f"**[{i}] {source_name}** — {page_label}"]

        # Sort chunks by start_line to display them in page order
        chunks_sorted = sorted(
            chunks,
            key=lambda x: x["start_line"] if x["start_line"] is not None else 0
        )

        for chunk in chunks_sorted:
            start = chunk["start_line"]
            end = chunk["end_line"]

            if start is not None and end is not None:
                if start == end:
                    loc_label = f"Line {start}"
                else:
                    loc_label = f"Lines {start}-{end}"
            else:
                loc_label = "Location N/A"

            preview = chunk["content"][:150].replace("\n", " ").strip()
            if len(chunk["content"]) > 150:
                preview += "…"

            citation_lines.append(f"* **{loc_label}**:\n  > _{preview}_")

        citations.append("\n".join(citation_lines))

    return citations
