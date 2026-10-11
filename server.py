"""Web UI backend: live chat with the agent + the eval results.  Run: uvicorn server:app"""
import json
import os
import secrets
import threading
from collections import OrderedDict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from groq import GroqError
from pydantic import BaseModel, Field

from agent import MAX_MESSAGE_CHARS, MODEL, Session

ROOT = Path(__file__).parent
MAX_SESSIONS = 200   # ponytail: in-memory, oldest evicted; use Redis if this ever runs multi-process
MAX_TURNS = 30

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
sessions: "OrderedDict[str, Session]" = OrderedDict()
sessions_lock = threading.Lock()


CSP = ("default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
       "img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")


@app.middleware("http")
async def security_headers(request, call_next):
    resp = await call_next(request)
    resp.headers.update({"Content-Security-Policy": CSP, "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer"})
    return resp


class ChatIn(BaseModel):
    session_id: str | None = Field(None, max_length=64)
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_CHARS)


def get_session(sid):
    with sessions_lock:
        if sid and sid in sessions:
            sessions.move_to_end(sid)
            return sid, sessions[sid]
        sid, s = secrets.token_urlsafe(16), Session()
        s.lock, s.turns = threading.Lock(), 0
        sessions[sid] = s
        while len(sessions) > MAX_SESSIONS:
            sessions.popitem(last=False)
        return sid, s


@app.post("/api/chat")
def chat(body: ChatIn):  # sync def: FastAPI runs it in a thread pool, the Groq call blocks
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(503, "GROQ_API_KEY is not set on the server. Add it to .env and restart.")
    sid, s = get_session(body.session_id)
    if s.turns >= MAX_TURNS:
        raise HTTPException(429, "This conversation is too long. Start a new one.")
    if not s.lock.acquire(blocking=False):
        raise HTTPException(409, "Still answering your last message.")
    try:
        reply, tools = s.send(body.message.strip())
        s.turns += 1
    except GroqError:
        raise HTTPException(502, "The language model didn't respond. Try again in a moment.")
    finally:
        s.lock.release()
    return {"session_id": sid, "reply": reply, "tools": tools,
            "customer": {"name": s.customer["name"], "status": s.customer["status"]} if s.customer else None}


@app.get("/api/meta")
def meta():
    return {"model": MODEL}


@app.get("/api/results")
def results():
    p = ROOT / "results.json"
    if not p.exists():
        raise HTTPException(404, "No eval results yet. Run: python run_eval.py")
    return json.loads(p.read_text(encoding="utf-8"))


app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
