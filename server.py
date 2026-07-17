"""
FastAPI Server — Parse Line Backend
=====================================
REST API wrapping the existing agent, auth, history, and file-upload logic.

Usage:
    python server.py          # starts on :8000
    uvicorn server:app --reload
"""

from __future__ import annotations

# ── Inject xxhash mock to bypass DLL blockade under Application Control ──
import sys
import types
import hashlib

class MockXXHash:
    def __init__(self, data=b""):
        self.m = hashlib.sha256()
        self.update(data)
    def update(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif not isinstance(data, (bytes, bytearray)):
            data = str(data).encode('utf-8')
        self.m.update(data)
    def hexdigest(self):
        return self.m.hexdigest()[:16]
    def digest(self):
        return self.m.digest()[:8]

mock_xxhash = types.ModuleType("xxhash")
mock_xxhash.xxh64 = lambda data=b"": MockXXHash(data)
mock_xxhash.xxh32 = lambda data=b"": MockXXHash(data)
mock_xxhash.xxh3_64 = lambda data=b"": MockXXHash(data)
mock_xxhash.xxh3_128 = lambda data=b"": MockXXHash(data)
mock_xxhash.xxh3_128_hexdigest = lambda data=b"", seed=0: hashlib.sha256(data if isinstance(data, bytes) else str(data).encode('utf-8')).hexdigest()[:32]
mock_xxhash.xxh3_64_hexdigest = lambda data=b"", seed=0: hashlib.sha256(data if isinstance(data, bytes) else str(data).encode('utf-8')).hexdigest()[:16]
sys.modules["xxhash"] = mock_xxhash
# ────────────────────────────────────────────────────────────────────────

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ── Bootstrap ─────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
load_dotenv()

from auth.auth_manager import AuthManager
from chat_history.history_manager import ChatHistoryManager
from file_processor import process_file

# ── App ───────────────────────────────────────────────────────
app = FastAPI(title="Parse Line API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singletons ────────────────────────────────────────────────
_auth = AuthManager()
_history = ChatHistoryManager()
_agent = None
_agent_ready = False

DB_PATH = str(ROOT / "data" / "database.db")
DOCS_DIR = str(ROOT / "data" / "docs")
UPLOAD_DIR = ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _get_agent():
    global _agent, _agent_ready
    if _agent is not None:
        return _agent
    try:
        from agent.graph import DataAnalystAgent
        from utils.generate_data import generate_all
        from utils.db_loader import load_csvs_to_sqlite

        if not Path(DB_PATH).exists():
            lightweight = os.environ.get("LIGHTWEIGHT_MODE", "").lower() in ("1", "true", "yes")
            if lightweight:
                Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
                # Create empty SQLite DB
                import sqlite3
                conn = sqlite3.connect(DB_PATH)
                conn.close()
            else:
                generate_all(data_dir=str(ROOT / "data"))
                load_csvs_to_sqlite(data_dir=str(ROOT / "data"), db_path=DB_PATH)

        dd = Path(DOCS_DIR)
        if not dd.exists() or not list(dd.glob("*.pdf")):
            lightweight = os.environ.get("LIGHTWEIGHT_MODE", "").lower() in ("1", "true", "yes")
            if lightweight:
                dd.mkdir(parents=True, exist_ok=True)
            else:
                from utils.generate_docs import generate_all_docs
                generate_all_docs(outdir=DOCS_DIR)

        _agent = DataAnalystAgent(db_path=DB_PATH, docs_dir=DOCS_DIR, verbose=False)
        _agent_ready = True
        return _agent
    except Exception as e:
        print(f"[ERROR] Agent init: {e}")
        return None


# ══════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ══════════════════════════════════════════════════════════════

class LoginReq(BaseModel):
    username: str
    password: str

class RegisterReq(BaseModel):
    username: str
    password: str
    display_name: str = ""

class ChatReq(BaseModel):
    username: str
    session_id: str
    question: str

class SessionCreate(BaseModel):
    username: str
    title: str = "New Chat"
    document_name: str = ""

class SessionRename(BaseModel):
    title: str


# ══════════════════════════════════════════════════════════════
# HEALTH
# ══════════════════════════════════════════════════════════════

@app.get("/api/health")
def health():
    return {"status": "ok", "agent_ready": _agent_ready}


# ══════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════

@app.post("/api/auth/register")
def register(req: RegisterReq):
    return _auth.register(req.username, req.password, req.display_name or None)

@app.post("/api/auth/login")
def login(req: LoginReq):
    return _auth.login(req.username, req.password)


# ══════════════════════════════════════════════════════════════
# SESSIONS
# ══════════════════════════════════════════════════════════════

@app.get("/api/sessions")
def list_sessions(username: str):
    return _history.get_sessions(username)

@app.post("/api/sessions")
def create_session(req: SessionCreate):
    sid = _history.create_session(req.username, req.title, req.document_name or None)
    return {"id": sid}

@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    _history.delete_session(session_id)
    return {"ok": True}

@app.patch("/api/sessions/{session_id}")
def rename_session(session_id: str, req: SessionRename):
    _history.rename_session(session_id, req.title)
    return {"ok": True}

@app.get("/api/sessions/{session_id}/messages")
def get_messages(session_id: str):
    return _history.get_messages(session_id)


# ══════════════════════════════════════════════════════════════
# CHAT
# ══════════════════════════════════════════════════════════════

@app.post("/api/chat")
def chat(req: ChatReq):
    agent = _get_agent()
    if not agent:
        raise HTTPException(500, "Agent not ready")

    # Guardrails
    from agent.extras import Guardrails, ConfidenceScorer
    v = Guardrails.validate(req.question)
    if not v["is_safe"]:
        blocked = "🛡️ Query blocked by safety guardrails.\n" + "\n".join(f"- {w}" for w in v["warnings"])
        _history.add_message(req.session_id, "user", req.question)
        _history.add_message(req.session_id, "assistant", blocked, {"blocked": True})
        return {
            "answer": blocked,
            "tools_used": [],
            "confidence": 0,
            "sql": None,
            "sources": [],
            "figures_json": [],
            "execution_time": 0,
            "warnings": v["warnings"],
        }

    warnings = v.get("warnings", [])
    query = v["sanitized_query"]

    # Load session history messages before saving current user message
    history = _history.get_messages(req.session_id)
    from langchain_core.messages import HumanMessage, AIMessage
    chat_history = []
    for msg in history:
        if msg["role"] == "user":
            chat_history.append(HumanMessage(content=msg["content"]))
        else:
            chat_history.append(AIMessage(content=msg["content"]))

    # Save user message
    _history.add_message(req.session_id, "user", query)

    # Get active document for this chat session
    session = _history.get_session(req.session_id)
    doc_name = session.get("document_name") if session else None

    # Run agent
    try:
        result = agent.run(query, active_document=doc_name, chat_history=chat_history)
    except Exception as e:
        err = f"Agent error: {e}"
        _history.add_message(req.session_id, "assistant", err, {"error": True})
        raise HTTPException(500, err)

    answer = result.get("answer", "I couldn't generate a response.")
    tools = result.get("tools_used", [])

    from agent.extras import ConfidenceScorer
    conf = ConfidenceScorer.score(result).get("overall", 0)

    sr = result.get("sql_result") or {}
    sql = sr.get("sql")
    sources = result.get("sources", [])
    et = result.get("execution_time", 0)

    # Serialize Plotly figures to JSON
    figures_json = []
    for fig in result.get("figures", []):
        try:
            figures_json.append(json.loads(fig.to_json()))
        except Exception:
            pass

    # Save assistant message (without figures for DB)
    meta = {
        "tools_used": tools,
        "confidence": conf,
        "sql": sql,
        "sources": sources,
        "execution_time": et,
    }
    _history.add_message(req.session_id, "assistant", answer, meta)

    return {
        "answer": answer,
        "tools_used": tools,
        "confidence": conf,
        "sql": sql,
        "sources": sources,
        "figures_json": figures_json,
        "execution_time": et,
        "warnings": warnings,
    }


# ══════════════════════════════════════════════════════════════
# FILE UPLOAD
# ══════════════════════════════════════════════════════════════

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    username: str = Form(...),
):
    try:
        agent = _get_agent()
        if not agent:
            raise HTTPException(500, "Agent not ready — server may be initializing. Please try again in 30 seconds.")

        # Save to disk
        dest = UPLOAD_DIR / file.filename
        with open(dest, "wb") as f:
            content = await file.read()
            f.write(content)

        # Also copy PDFs/DOCX to docs dir for RAG indexing
        if file.filename.lower().endswith((".pdf", ".docx", ".txt")):
            docs = Path(DOCS_DIR)
            docs.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dest, docs / file.filename)

        # Process
        result = process_file(str(dest), agent, DB_PATH)

        if result["success"]:
            title = f"📄 {file.filename}"
            sid = _history.create_session(username, title, file.filename)
            result["session_id"] = sid
        else:
            raise HTTPException(400, result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")
        raise HTTPException(500, f"Upload processing failed: {str(e)}")


# ══════════════════════════════════════════════════════════════
# SCHEMA
# ══════════════════════════════════════════════════════════════

@app.get("/api/schema")
def get_schema():
    try:
        from agent.extras import SchemaDiscovery
        s = SchemaDiscovery(db_path=DB_PATH)
        return {"schema": s.get_schema(), "tables": s.get_table_names()}
    except Exception as e:
        return {"schema": str(e), "tables": []}


# ══════════════════════════════════════════════════════════════
# STARTUP EVENT — Preload agent in background
# ══════════════════════════════════════════════════════════════

@app.on_event("startup")
def startup_preload():
    """Preload the agent in a background thread on server start.

    This is critical for Render deployments where `uvicorn server:app`
    doesn't trigger __main__, so without this the first request would
    bear the full agent initialization cost (and likely timeout).
    """
    import threading
    threading.Thread(target=_get_agent, daemon=True).start()
    print("[STARTUP] Agent preloading in background thread...")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    print("Starting Parse Line API on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
