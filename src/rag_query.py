"""Grounded RAG search over the AuNP literature corpus.

Use --retrieve-only to verify retrieval without an API key. Full answers use
Groq and are generated only from the retrieved excerpts.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

APP_DIR = Path(__file__).resolve().parent
PERSIST_DIR = APP_DIR / "chroma_store"
COLLECTION_NAME = "aunp_synthesis"
DEFAULT_MODEL = "openai/gpt-oss-20b"


def get_collection():
    if not PERSIST_DIR.exists():
        raise RuntimeError(
            f"No vector store found at {PERSIST_DIR}. Run `python build_vector_store.py --reset` first."
        )
    client = chromadb.PersistentClient(path=str(PERSIST_DIR))
    try:
        return client.get_collection(COLLECTION_NAME)
    except Exception as error:
        raise RuntimeError("The AuNP collection is missing. Rebuild it with build_vector_store.py --reset.") from error


def get_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


def retrieve(question: str, k: int = 5):
    model = get_embedding_model()
    collection = get_collection()
    result = collection.query(query_embeddings=model.encode([question]).tolist(), n_results=k)
    return list(zip(result["documents"][0], result["metadatas"][0], result["ids"][0]))


def answer(question: str, chunks, model_name: str):
    if not os.environ.get("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is not set. Use --retrieve-only or set the key to generate an answer.")
    from groq import Groq

    context = "\n\n".join(
        f"[Source {index} | DOI: {metadata['doi']} | type: {metadata['type']}]\n{text}"
        for index, (text, metadata, _identifier) in enumerate(chunks, start=1)
    )
    prompt = f"""Answer the question using only the excerpts below from text-mined scientific literature.
The excerpts can be incomplete. If they do not support an answer, say so. Do not infer facts
that are absent. Cite each factual statement using the bracketed source number.

EXCERPTS:
{context}

QUESTION: {question}"""
    response = Groq().chat.completions.create(
        model=model_name,
        max_tokens=500,
        messages=[
            {"role": "system", "content": "You are a careful scientific-literature assistant. Never add facts that are absent from the supplied excerpts."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


def main() -> None:
    parser = argparse.ArgumentParser(description="Search AuNP literature with grounded RAG.")
    parser.add_argument("question", nargs="+", help="Question to search for")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--retrieve-only", action="store_true", help="Print evidence without making an LLM request")
    parser.add_argument("--model", default=os.getenv("GROQ_MODEL", DEFAULT_MODEL))
    args = parser.parse_args()
    question = " ".join(args.question)
    chunks = retrieve(question, args.top_k)
    if args.retrieve_only:
        print("=== RETRIEVED EVIDENCE ===")
    else:
        print("=== GROUNDED ANSWER ===")
        print(answer(question, chunks, args.model))
        print("\n=== SUPPORTING SOURCES ===")
    for index, (text, metadata, _identifier) in enumerate(chunks, start=1):
        print(f"[{index}] {metadata['doi']} ({metadata['type']})\n{text}\n")


if __name__ == "__main__":
    main()
