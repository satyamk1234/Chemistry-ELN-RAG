# AuNP Mini-ELN and Evidence-Grounded RAG Search

A portfolio prototype for chemistry data operations. It combines a normalized, queryable experiment database with a retrieval-augmented search workflow over text-mined gold-nanoparticle literature. It is explicit about the distinction between public literature data and a production laboratory ELN.

## What it demonstrates

- **ETL and SQL:** 5,154 articles, 7,608 synthesis recipes, 34,283 precursor entries, and 12,519 characterization records are loaded into SQLite.
- **ELN-style records:** a Streamlit interface can browse recipe data, search by precursor, and validate/import lab or instrument-export CSV records with source-file and import-time provenance.
- **Grounded RAG:** a local Chroma vector store retrieves source excerpts before an LLM answers. The prompt requires citation by retrieved-source number and allows abstention when the excerpts are insufficient.
- **Evaluation:** ten fixed retrieval cases report Recall@5 against expected literature DOIs.

## Data and limitations

The source is a public text-mined dataset of nanoparticle synthesis and characterization paragraphs from Cruse et al., *Scientific Data* (2022). It is a realistic data shape for prototyping, but it is **not** NanoFrontier data or a real laboratory record system. Source text is truncated in this processed corpus; precursor amounts and conditions are inconsistently parsed; and literature recipe/outcome links are incomplete. The RAG tool must therefore not be used for experimental decisions.

## Quick start

Run all commands from `src/`.

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Rebuild the structured database, then launch the ELN-style dashboard
python load_to_db.py --reset
streamlit run dashboard.py
```

The dashboard includes a **Lab CSV import** tab. Use `../data/lab_experiments_example.csv` as a valid example. The required columns are `experiment_id`, `experiment_date` (`YYYY-MM-DD`), `operator`, `sample_id`, `procedure`, `outcome`, and `source_file`.

## RAG build, evidence demo, and evaluation

```bash
# Downloads all-MiniLM-L6-v2 on first run and creates src/chroma_store/
python build_vector_store.py --reset

# This needs no API key and is the recommended demo screenshot command.
python rag_query.py --retrieve-only "Which source describes gold nanorod synthesis?"

# Retrieval evaluation; reports Recall@5 over data/rag_eval.json.
python rag_eval.py

# Optional generated answer. Create a Groq API key, set it locally, and never commit it.
$env:GROQ_API_KEY="your_key_here"  # PowerShell
python rag_query.py "Which sources describe gold nanorod synthesis?"
```

The answer-generation backend is Groq. Its default model is `openai/gpt-oss-20b`; override it without changing source code with `GROQ_MODEL` or `--model`. Retrieval and evaluation do not send corpus text to Groq.

## Pilot test protocol

Use this compact test before presenting the project. Record the terminal output and one screenshot for each step.

1. Rebuild the database: `python load_to_db.py --reset`. Confirm the four printed row counts.
2. Launch `streamlit run dashboard.py`. Upload `../data/lab_experiments_example.csv` in **Lab CSV import**, verify the two-row preview, then import it. Confirm that the stored-record table shows the source file and import time.
3. Build the vector store: `python build_vector_store.py --reset`.
4. Run an evidence-only question: `python rag_query.py --retrieve-only "Which source describes gold nanorod synthesis?"`. Save a screenshot showing the question and retrieved DOI evidence.
5. Run `python rag_eval.py`. Record its Recall@5 result, date, corpus version, embedding model (`all-MiniLM-L6-v2`), and `top_k=5`.
6. Set `GROQ_API_KEY` and repeat the same question without `--retrieve-only`. Check that every factual claim in the answer has a `[source number]`, and that those numbers match the printed evidence.
7. Negative test: ask a question outside the snippets, for example `What is the exact yield of every nanorod procedure?`. Pass only if the answer says the excerpts are insufficient instead of inventing a result.

## Docker

From the repository root (the directory containing `src/` and `data/`):

```bash
docker build -f src/Dockerfile -t aunp-mini-eln .
docker run --rm -p 8501:8501 aunp-mini-eln
```

Then open `http://localhost:8501`. The image includes the code and source data but does not prebuild the embedding store, download the embedding model, or contain API keys.

## Repository map

| File | Purpose |
|---|---|
| `schema.sql` | SQLite schema for literature records and provenance-aware lab imports |
| `load_to_db.py` | CSV-to-SQLite ETL loader |
| `lab_ingest.py` | Reusable CSV validator and provenance-preserving importer |
| `dashboard.py` | Streamlit browser, precursor search, and lab CSV import UI |
| `build_vector_store.py` | Resettable/reproducible local Chroma vector-store builder |
| `rag_query.py` | Evidence-only or grounded-answer RAG CLI |
| `rag_eval.py` | Retrieval Recall@k evaluator |
| `../data/rag_eval.json` | Fixed evaluation cases and expected source DOIs |

## Interview-ready demo flow

1. Run the dashboard and show precursor search plus the validated CSV import preview.
2. Run the `--retrieve-only` command above and screenshot its retrieved DOI evidence.
3. Run `python rag_eval.py`, record the resulting Recall@5, and state the date, corpus version, embedding model, and top-k alongside that number.
4. Explain the limitations honestly and describe the next step: a versioned schema for samples, instruments, measurements, and researcher-authored lab notes.
