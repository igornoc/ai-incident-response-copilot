from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"


def split_document(text: str, source: str) -> list[dict]:
    chunks = []

    current_heading = "General"
    current_lines = []

    def save_chunk():
        if not current_lines:
            return

        content = "\n".join(current_lines).strip()

        if len(content) < 40:
            return

        chunks.append(
            {
                "source": source,
                "section": current_heading,
                "content": content,
            }
        )

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("#"):
            save_chunk()
            current_lines.clear()

            current_heading = (
                stripped.lstrip("#").strip()
                or "General"
            )
        else:
            current_lines.append(line)

    save_chunk()

    return chunks


def load_knowledge_base() -> list[dict]:
    chunks = []

    if not DOCS_DIR.exists():
        return chunks

    for path in DOCS_DIR.rglob("*.md"):
        try:
            text = path.read_text(
                encoding="utf-8"
            )
        except UnicodeDecodeError:
            continue

        source = str(
            path.relative_to(DOCS_DIR)
        ).replace("\\", "/")

        chunks.extend(
            split_document(
                text=text,
                source=source
            )
        )

    return chunks


def retrieve_evidence(
    query: str,
    top_k: int = 3
) -> list[dict]:
    chunks = load_knowledge_base()

    if not chunks:
        return []

    documents = [
        chunk["content"]
        for chunk in chunks
    ]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2)
    )

    matrix = vectorizer.fit_transform(
        documents + [query]
    )

    document_vectors = matrix[:-1]
    query_vector = matrix[-1]

    scores = cosine_similarity(
        query_vector,
        document_vectors
    ).flatten()

    ranked_indices = scores.argsort()[::-1]

    results = []

    for index in ranked_indices:
        score = float(scores[index])

        if score <= 0:
            continue

        chunk = chunks[index]

        results.append(
            {
                "source": chunk["source"],
                "section": chunk["section"],
                "score": round(score, 4),
                "content": chunk["content"],
            }
        )

        if len(results) >= top_k:
            break

    return results


def retrieve_incident_evidence(
    incident,
    top_k: int = 3
) -> list[dict]:
    query = (
        f"{incident.title}\n"
        f"{incident.description}\n"
        f"severity {incident.severity}\n"
        f"status {incident.status}"
    )

    return retrieve_evidence(
        query=query,
        top_k=top_k
    )
