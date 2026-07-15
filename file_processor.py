"""
Universal File Processor
==========================
Handles CSV, PDF, DOCX, XLSX, TXT ingestion into the agent pipeline.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd


def process_file(
    filepath: str | Path,
    agent: Any,
    db_path: str = "data/database.db",
) -> dict:
    """Process an uploaded file and load it into the appropriate tool.

    Args:
        filepath: Path to the uploaded file.
        agent: DataAnalystAgent instance.
        db_path: Path to the SQLite database.

    Returns:
        Dict with keys: success, file_type, message, table_name (if CSV/XLSX),
        chunks_added (if PDF/DOCX/TXT).
    """
    fp = Path(filepath)
    ext = fp.suffix.lower()

    handlers = {
        ".csv": _process_csv,
        ".pdf": _process_pdf,
        ".docx": _process_docx,
        ".xlsx": _process_xlsx,
        ".xls": _process_xlsx,
        ".txt": _process_txt,
    }

    handler = handlers.get(ext)
    if not handler:
        return {
            "success": False,
            "file_type": ext,
            "message": f"Unsupported file type: {ext}. Supported: CSV, PDF, DOCX, XLSX, TXT",
        }

    try:
        return handler(fp, agent, db_path)
    except Exception as e:
        return {"success": False, "file_type": ext, "message": str(e)}


def _sanitize_table_name(name: str) -> str:
    raw = Path(name).stem
    tbl = re.sub(r"[^a-z0-9_]", "_", raw.lower()).strip("_")
    tbl = re.sub(r"_+", "_", tbl)
    if not tbl or not tbl[0].isalpha():
        tbl = "t_" + tbl
    return tbl[:50]


# ── CSV ──────────────────────────────────────────────────────

def _process_csv(fp: Path, agent: Any, db_path: str) -> dict:
    from utils.db_loader import load_custom_csv_to_sqlite

    df = pd.read_csv(fp)
    tbl = _sanitize_table_name(fp.name)
    load_custom_csv_to_sqlite(str(fp), tbl, db_path)

    # Reset SQL tool so it picks up new schema
    if hasattr(agent, "_sql_tool") and agent._sql_tool:
        agent._sql_tool.refresh_schema()

    return {
        "success": True,
        "file_type": "csv",
        "message": f"Loaded {len(df):,} rows into table '{tbl}'",
        "table_name": tbl,
        "row_count": len(df),
        "columns": list(df.columns),
    }


# ── PDF ──────────────────────────────────────────────────────

def _process_pdf(fp: Path, agent: Any, db_path: str) -> dict:
    rag = agent._get_rag_tool()
    n = rag.load_pdf(str(fp))
    return {
        "success": True,
        "file_type": "pdf",
        "message": f"Indexed {n} chunks from '{fp.name}'",
        "chunks_added": n,
    }


# ── DOCX ─────────────────────────────────────────────────────

def _process_docx(fp: Path, agent: Any, db_path: str) -> dict:
    from docx import Document as DocxDocument

    doc = DocxDocument(str(fp))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    full_text = "\n\n".join(paragraphs)

    if not full_text.strip():
        return {"success": False, "file_type": "docx", "message": "No text found in DOCX."}

    # Write to a temp text file for the doc loader
    from utils.doc_loader import chunk_text, DocumentChunk

    rag = agent._get_rag_tool()
    loader = rag._loader

    chunks = chunk_text(
        full_text,
        chunk_size=500,
        chunk_overlap=50,
        metadata={"source": fp.name, "doc_type": "docx"},
    )

    if not chunks:
        return {"success": False, "file_type": "docx", "message": "No chunks created."}

    # Remove existing and add new
    loader._remove_source(fp.name)
    loader._collection.add(
        ids=[c.chunk_id for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[c.metadata for c in chunks],
    )

    return {
        "success": True,
        "file_type": "docx",
        "message": f"Indexed {len(chunks)} chunks from '{fp.name}'",
        "chunks_added": len(chunks),
    }


# ── XLSX ─────────────────────────────────────────────────────

def _process_xlsx(fp: Path, agent: Any, db_path: str) -> dict:
    from utils.db_loader import load_custom_csv_to_sqlite

    xls = pd.ExcelFile(fp)
    sheets = xls.sheet_names
    total_rows = 0
    tables = []

    for sheet in sheets:
        df = pd.read_excel(xls, sheet_name=sheet)
        if df.empty:
            continue
        tbl = _sanitize_table_name(f"{fp.stem}_{sheet}")

        # Write to temp CSV for loader
        tmp = Path(db_path).parent / f"_xlsx_{tbl}.csv"
        df.to_csv(tmp, index=False)
        load_custom_csv_to_sqlite(str(tmp), tbl, db_path)
        tmp.unlink(missing_ok=True)

        total_rows += len(df)
        tables.append(tbl)

    if hasattr(agent, "_sql_tool") and agent._sql_tool:
        agent._sql_tool.refresh_schema()

    return {
        "success": True,
        "file_type": "xlsx",
        "message": f"Loaded {total_rows:,} rows from {len(tables)} sheet(s)",
        "table_names": tables,
        "row_count": total_rows,
    }


# ── TXT ──────────────────────────────────────────────────────

def _process_txt(fp: Path, agent: Any, db_path: str) -> dict:
    text = fp.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        return {"success": False, "file_type": "txt", "message": "Empty text file."}

    from utils.doc_loader import chunk_text

    rag = agent._get_rag_tool()
    loader = rag._loader

    chunks = chunk_text(
        text,
        chunk_size=500,
        chunk_overlap=50,
        metadata={"source": fp.name, "doc_type": "txt"},
    )

    if not chunks:
        return {"success": False, "file_type": "txt", "message": "No chunks created."}

    loader._remove_source(fp.name)
    loader._collection.add(
        ids=[c.chunk_id for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[c.metadata for c in chunks],
    )

    return {
        "success": True,
        "file_type": "txt",
        "message": f"Indexed {len(chunks)} chunks from '{fp.name}'",
        "chunks_added": len(chunks),
    }
