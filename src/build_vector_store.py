"""Build a reproducible Chroma vector store from the project RAG corpus."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

APP_DIR = Path(__file__).resolve().parent
CORPUS_PATH = APP_DIR.parent / "data" / "rag_corpus.jsonl"
PERSIST_DIR = APP_DIR / "chroma_store"
COLLECTION_NAME = "aunp_synthesis"
BATCH_SIZE = 256


def main() -> None:
    parser = argparse.ArgumentParser(description="Embed the AuNP corpus into a local Chroma store.")
    parser.add_argument("--reset", action="store_true", help="Remove an existing store before rebuilding it.")
    args = parser.parse_args()
    if PERSIST_DIR.exists():
        if not args.reset:
            raise SystemExit(f"{PERSIST_DIR} already exists. Use --reset to rebuild reproducibly.")
        shutil.rmtree(PERSIST_DIR)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=str(PERSIST_DIR))
    collection = client.create_collection(COLLECTION_NAME)

    texts, identifiers, metadata = [], [], []
    with CORPUS_PATH.open(encoding="utf-8") as corpus:
        for line in corpus:
            row = json.loads(line)
            if not row.get("text", "").strip():
                continue
            texts.append(row["text"])
            identifiers.append(f"{row['type']}:{row['paragraph_id']}")
            metadata.append({"doi": row["doi"], "year": row["year"] or 0, "type": row["type"]})

    print(f"Embedding {len(texts)} paragraphs with all-MiniLM-L6-v2...")
    for start in range(0, len(texts), BATCH_SIZE):
        end = start + BATCH_SIZE
        collection.add(
            embeddings=model.encode(texts[start:end], show_progress_bar=False).tolist(),
            documents=texts[start:end], ids=identifiers[start:end], metadatas=metadata[start:end],
        )
        print(f"  {min(end, len(texts))}/{len(texts)}")
    print(f"Done. Vector store saved to {PERSIST_DIR}")


if __name__ == "__main__":
    main()
