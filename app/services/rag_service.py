from functools import lru_cache
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


@lru_cache(maxsize=1)
def build_index():
    """Load the runbooks and fit the TF-IDF index once per process.

    Previously every request re-read every file and re-fitted the
    vectorizer. Restart the API (or call build_index.cache_clear())
    after editing the runbooks.
    """
    chunks = load_knowledge_base()

    if not chunks:
        return [], None, None

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2)
    )

    document_vectors = vectorizer.fit_transform(
        [chunk["content"] for chunk in chunks]
    )

    return chunks, vectorizer, document_vectors


def retrieve_evidence(
    query: str,
    top_k: int = 3
) -> list[dict]:
    chunks, vectorizer, document_vectors = build_index()

    if not chunks:
        return []

    query_vector = vectorizer.transform(
        [query]
    )

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
