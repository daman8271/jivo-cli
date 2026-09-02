"""FastAPI front end: login, chat over SSE, saved conversations.

Run it:
    cd jivo-chat
    pip install -r requirements.txt
    cp .env.example .env      # then fill in ANTHROPIC_API_KEY
    python -m app.server adduser you@jivo.in "Your Name" 'password' owner
    python -m app.server
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import pathlib
import sys
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from itsdangerous import BadSignature, URLSafeTimedSerializer

from .agent import Agent
from .db import Store
from .gateway import Gateway

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("jivo-chat")

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT.parent
SESSION_MAX_AGE = 12 * 3600


def _load_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env()

SECRET = os.environ.get("JIVO_CHAT_SECRET", "change-me")
DB_PATH = os.environ.get("JIVO_CHAT_DB", str(ROOT / "jivo-chat.db"))
GATEWAY_URL = os.environ.get("JIVO_GATEWAY_URL", "http://127.0.0.1:7700/mcp")
MODEL = os.environ.get("JIVO_CHAT_MODEL", "claude-opus-5")
EFFORT = os.environ.get("JIVO_CHAT_EFFORT", "high")
DAILY_CAP = float(os.environ.get("JIVO_CHAT_DAILY_CAP_INR", "0") or 0)

signer = URLSafeTimedSerializer(SECRET, salt="jivo-chat-session")
store = Store(DB_PATH)


def _corrections() -> str:
    """The team's settled truths. Injected into every system prompt."""
    path = REPO / "harness" / "corrections" / "INDEX.md"
    if path.exists():
        return path.read_text()
    log.warning("corrections digest not found at %s — running without it", path)
    return "(No corrections digest available.)"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.gateway = Gateway(GATEWAY_URL)
    try:
        await app.state.gateway.connect()
        tools = await app.state.gateway.list_tools()
        log.info("gateway ready with %d tools", len(tools))
    except Exception as exc:  # noqa: BLE001 — start anyway, report in the UI
        log.error("gateway unreachable at %s: %s", GATEWAY_URL, exc)
    app.state.agent = Agent(
        store=store,
        gateway=app.state.gateway,
        corrections=_corrections(),
        model=MODEL,
        effort=EFFORT,
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )
    yield
    await app.state.gateway.aclose()


app = FastAPI(title="JIVO Chat", lifespan=lifespan)


# --------------------------------------------------------------------- session

def current_user(request: Request):
    token = request.cookies.get("jivo_session")
    if not token:
        return None
    try:
        email = signer.loads(token, max_age=SESSION_MAX_AGE)
    except BadSignature:
        return None
    return store.get_user(email)


def require_user(request: Request):
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="not signed in")
    return user


# ----------------------------------------------------------------------- pages

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if current_user(request) is None:
        return RedirectResponse("/login", status_code=302)
    return HTMLResponse((HERE / "static" / "index.html").read_text())


@app.get("/login", response_class=HTMLResponse)
async def login_page(error: str = ""):
    return HTMLResponse((HERE / "static" / "login.html").read_text().replace("{{error}}", error))


@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    user = store.verify_user(email, password)
    if user is None:
        # Deliberately identical message for unknown email and wrong password.
        return RedirectResponse("/login?error=Wrong+email+or+password", status_code=302)
    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie(
        "jivo_session",
        signer.dumps(user["email"]),
        httponly=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
    )
    return resp


@app.get("/logout")
async def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("jivo_session")
    return resp


# ------------------------------------------------------------------------- api

@app.get("/api/me")
async def me(user=Depends(require_user)):
    return {
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "spend_today_inr": round(store.spend_today(user["email"]), 2),
        "daily_cap_inr": DAILY_CAP,
    }


@app.get("/api/conversations")
async def conversations(user=Depends(require_user)):
    return store.list_conversations(user["email"])


@app.post("/api/conversations")
async def new_conversation(user=Depends(require_user)):
    return {"id": store.new_conversation(user["email"])}


@app.get("/api/conversations/{cid}")
async def conversation(cid: str, user=Depends(require_user)):
    if not store.owns_conversation(user["email"], cid):
        raise HTTPException(status_code=404, detail="no such conversation")
    return store.history(cid)


@app.post("/api/chat")
async def chat(request: Request, user=Depends(require_user)):
    body = await request.json()
    cid = body.get("conversation_id")
    question = (body.get("question") or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="empty question")

    if not cid or not store.owns_conversation(user["email"], cid):
        cid = store.new_conversation(user["email"], title=question[:60])

    if DAILY_CAP and store.spend_today(user["email"]) >= DAILY_CAP:
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit of ₹{DAILY_CAP:.0f} reached. Resets 24h after your first question today.",
        )

    agent: Agent = request.app.state.agent

    async def stream():
        yield f"data: {json.dumps({'type': 'conversation', 'id': cid})}\n\n"
        try:
            async for event in agent.ask(user, cid, question):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:  # noqa: BLE001 — surface it, never hang the browser
            log.exception("chat failed")
            store.audit(user["email"], cid, "error", {"error": str(exc)})
            yield f"data: {json.dumps({'type': 'error', 'text': str(exc)})}\n\n"
        yield "data: {\"type\": \"end\"}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ------------------------------------------------------------------------- cli

def _cli() -> bool:
    if len(sys.argv) < 2:
        return False
    cmd = sys.argv[1]
    if cmd == "adduser":
        if len(sys.argv) < 5:
            print("usage: python -m app.server adduser EMAIL 'NAME' PASSWORD [ROLE]")
            sys.exit(2)
        email, name, password = sys.argv[2], sys.argv[3], sys.argv[4]
        role = sys.argv[5] if len(sys.argv) > 5 else "accounts"
        store.create_user(email, name, password, role)
        print(f"created {email} ({role})")
        return True
    if cmd == "roles":
        from .db import DEFAULT_ROLES
        for name, (desc, prefixes) in DEFAULT_ROLES.items():
            print(f"{name:10s} {', '.join(prefixes):55s} {desc}")
        return True
    if cmd == "tools":
        async def show():
            gw = Gateway(GATEWAY_URL)
            try:
                for t in await gw.list_tools():
                    print(f"{t['name']:34s} {t['description'][:90]}")
            finally:
                await gw.aclose()
        asyncio.run(show())
        return True
    return False


if __name__ == "__main__":
    if not _cli():
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
