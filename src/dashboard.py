"""
Mini-ELN dashboard. Run with: streamlit run dashboard.py
Requires eln.db to already exist (run load_to_db.py first).
"""
import io
import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st
from lab_ingest import import_rows, read_and_validate_csv

APP_DIR = Path(__file__).resolve().parent
conn = sqlite3.connect(APP_DIR / "eln.db")

st.set_page_config(page_title="AuNP Mini-ELN", layout="wide")
st.title("Gold Nanoparticle Synthesis — Mini ELN")

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Browse recipes", "Query by precursor", "Lab CSV import"])

with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("Articles", conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0])
    col2.metric("Recipes", conn.execute("SELECT COUNT(*) FROM recipes").fetchone()[0])
    col3.metric("Characterization records", conn.execute("SELECT COUNT(*) FROM characterization").fetchone()[0])

    st.subheader("Top 15 precursors")
    df = pd.read_sql(
        "SELECT material, COUNT(*) as uses FROM precursors GROUP BY material ORDER BY uses DESC LIMIT 15",
        conn,
    )
    st.bar_chart(df.set_index("material"))

with tab2:
    st.subheader("Browse recipes")
    n = st.slider("Rows to show", 5, 50, 10)
    df = pd.read_sql(
        f"SELECT paragraph_id, doi, seed_mediated, target, text_snippet FROM recipes LIMIT {n}",
        conn,
    )
    st.dataframe(df, use_container_width=True)

with tab3:
    st.subheader("Find recipes that use a given precursor")
    material = st.text_input("Precursor name (e.g. CTAB, AgNO3, HAuCl4)", "CTAB")
    if material:
        df = pd.read_sql(
            """SELECT r.paragraph_id, r.doi, r.seed_mediated, r.text_snippet
               FROM recipes r
               JOIN precursors p ON r.paragraph_id = p.paragraph_id
               WHERE p.material LIKE ?
               LIMIT 25""",
            conn,
            params=(f"%{material}%",),
        )
        st.write(f"{len(df)} matching recipes")
        st.dataframe(df, use_container_width=True)

with tab4:
    st.subheader("Validated laboratory CSV ingestion")
    st.caption("Each record preserves its original source-file label and the UTC import time for provenance.")
    st.code("experiment_id,experiment_date,operator,sample_id,procedure,conditions,outcome,instrument,source_file", language="text")
    uploaded = st.file_uploader("Upload a laboratory or instrument-export CSV", type="csv")
    if uploaded:
        rows, errors = read_and_validate_csv(io.StringIO(uploaded.getvalue().decode("utf-8-sig")))
        if errors:
            st.error("The file was not imported.")
            st.markdown("\n".join(f"- {error}" for error in errors))
        else:
            st.success(f"Validation passed for {len(rows)} record(s).")
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            if st.button("Import validated records"):
                count = import_rows(APP_DIR / "eln.db", rows, uploaded.name)
                st.success(f"Imported or updated {count} record(s).")
    st.divider()
    imported = pd.read_sql("SELECT * FROM lab_experiments ORDER BY imported_at DESC LIMIT 50", conn)
    st.caption(f"Stored laboratory records: {len(imported)}")
    st.dataframe(imported, use_container_width=True)
