import hashlib
import hmac
import json
import os
import secrets
import sys
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager, closing
from pathlib import Path
from typing import Literal
import grpc
from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from opentelemetry import metrics
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient
from services.telemetry import configure
from services.gateway.db import connect, transaction, initialize, password_hash
from services.gateway.ai import draft

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services/policy"))
import policy_pb2 as pb
import policy_pb2_grpc as rpc

tracer = configure("atlas-gateway")
GrpcInstrumentorClient().instrument()
meter = metrics.get_meter("atlas-ux")
events = meter.create_counter("atlas.ux.events", description="Allowlisted task events")
duration = meter.create_histogram("atlas.ux.task.duration", unit="ms")
channel = grpc.insecure_channel(os.getenv("POLICY_ADDRESS", "127.0.0.1:50051"))
policy = rpc.PolicyStub(channel)
ROLES = {"viewer": 0, "operator": 1, "admin": 2}
ACTIONS = {"suspend": 0, "restore": 1, "change_role": 2}
PUBLIC = "id,name,email,role,active,version"

@asynccontextmanager
async def lifespan(app):
    if len(os.getenv("POLICY_TOKEN", "")) < 32: raise RuntimeError("POLICY_TOKEN needs at least 32 characters")
    initialize()
    yield
    channel.close()

app = FastAPI(title="Atlas Admin API", version="1.0.0", lifespan=lifespan,
              docs_url=None, redoc_url=None, openapi_url=None)
FastAPIInstrumentor.instrument_app(app, excluded_urls="/api/health")

@app.middleware("http")
async def harden(request, call_next):
    if request.headers.get("content-length", "0").isdigit() and int(request.headers.get("content-length", "0")) > 16384:
        return JSONResponse({"detail": "Request too large"}, status_code=413)
    # Mutating APIs are same-origin only. Nonbrowser clients may omit Origin but must supply CSRF.
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        if origin and origin != os.getenv("APP_ORIGIN", "http://localhost:5173"):
            return JSONResponse({"detail": "Origin not allowed"}, status_code=403)
        size = 0
        parts = []
        async for part in request.stream():
            size += len(part)
            if size > 16384: return JSONResponse({"detail": "Request too large"}, status_code=413)
            parts.append(part)
        request._body = b"".join(parts)
    response = await call_next(request)
    response.headers.update({
        "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer",
        "X-Frame-Options": "DENY", "Cache-Control": "no-store",
        "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()"})
    if os.getenv("COOKIE_SECURE", "false") == "true":
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response

def now(): return int(time.time())
def digest(value): return hashlib.sha256(value.encode()).hexdigest()
def metadata(): return (("x-policy-token", os.environ["POLICY_TOKEN"]),)
def rpc_call(method, request):
    try: return method(request, timeout=2, metadata=metadata())
    except grpc.RpcError: raise HTTPException(503, "Policy service unavailable; no change was made")
def audit(db, actor, action, target, details):
    db.execute("INSERT INTO audit(timestamp,actor_id,action,target_id,details) VALUES (?,?,?,?,?)",
               (now(), actor, action, target, json.dumps(details)))
def get_user(db, user_id):
    row = db.execute(f"SELECT {PUBLIC} FROM users WHERE id=?", (user_id,)).fetchone()
    if row is None: raise HTTPException(404, "Identity not found")
    return dict(row)

def actor(request: Request):
    token = request.cookies.get("atlas_session", "")
    if not token or len(token) > 128: raise HTTPException(401, "Sign in to continue")
    with closing(connect()) as db:
        row = db.execute('''SELECT users.id,users.name,users.email,users.role,users.active,
            sessions.csrf FROM sessions JOIN users ON users.id=sessions.user_id
            WHERE sessions.digest=? AND sessions.expires>? AND users.active=1''', (digest(token), now())).fetchone()
    if row is None: raise HTTPException(401, "Session expired; sign in again")
    result = dict(row)
    if request.method not in ("GET", "HEAD"):
        if not hmac.compare_digest(request.headers.get("x-csrf-token", ""), result["csrf"]):
            raise HTTPException(403, "Invalid CSRF token")
    return result

def require_admin(user):
    if not user["active"]: raise HTTPException(401, "Account inactive")
    if user["role"] != "admin": raise HTTPException(403, "Administrator role required")

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
class Login(StrictModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)
class Change(StrictModel):
    target_id: str = Field(min_length=1, max_length=64)
    action: Literal["suspend", "restore", "change_role"]
    role: Literal["viewer", "operator", "admin"] = "viewer"
class Draft(StrictModel):
    target_id: str = Field(min_length=1, max_length=64)
    prompt: str = Field(min_length=3, max_length=1000)
class Confirm(StrictModel):
    confirmed: Literal[True]
class NewUser(StrictModel):
    name: str = Field(min_length=1, max_length=80, pattern=r"^[^\x00-\x1f]+$")
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    role: Literal["viewer", "operator", "admin"] = "viewer"
class Flag(StrictModel):
    percent: int = Field(ge=0, le=100, strict=True)
    version: int = Field(ge=1, strict=True)
class Event(StrictModel):
    name: Literal["task_started", "proposal_created", "task_completed", "task_failed"]
    surface: Literal["admin", "review"]
    duration_ms: int = Field(default=0, ge=0, le=3600000)

attempts = defaultdict(deque)
limit_lock = threading.Lock()
def rate_limit(key, maximum, window=60):
    current = time.monotonic()
    with limit_lock:
        # Bound memory used by inactive clients.
        for k in list(attempts):
            while attempts[k] and attempts[k][0] < current - window: attempts[k].popleft()
            if not attempts[k]: del attempts[k]
        queue = attempts[key]
        if len(queue) >= maximum: raise HTTPException(429, "Too many requests; try again later")
        queue.append(current)

@app.get("/api/health")
def health(): return {"status": "ok", "version": "1.0.0"}
@app.get("/api/ready")
def ready():
    rpc_call(policy.Flight, pb.FlightRequest(subject="health", flag="health", percent=0))
    with closing(connect()) as db: db.execute("SELECT 1 FROM flags").fetchone()
    return {"status": "ready"}
@app.post("/api/login")
def login(body: Login, request: Request, response: Response):
    rate_limit("login:" + (request.client.host if request.client else "unknown"), 10)
    with transaction() as db:
        row = db.execute("SELECT * FROM users WHERE email=? AND active=1", (body.email.lower(),)).fetchone()
        salt = row["salt"] if row and row["salt"] else "00" * 16
        hashed = password_hash(body.password, salt)
        if not row or not row["password_hash"] or not hmac.compare_digest(hashed, row["password_hash"]):
            raise HTTPException(401, "Invalid email or password")
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        db.execute("DELETE FROM sessions WHERE expires<=?", (now(),))
        db.execute("INSERT INTO sessions VALUES (?,?,?,?)", (digest(token), row["id"], csrf, now() + 3600))
        audit(db, row["id"], "session.created", row["id"], {})
    response.set_cookie("atlas_session", token, httponly=True, samesite="strict", max_age=3600,
                        secure=os.getenv("COOKIE_SECURE", "false") == "true", path="/")
    return {"csrf": csrf}
@app.post("/api/logout")
def logout(request: Request, response: Response, user=Depends(actor)):
    with transaction() as db: db.execute("DELETE FROM sessions WHERE digest=?", (digest(request.cookies["atlas_session"]),))
    response.delete_cookie("atlas_session", path="/")
    return {"ok": True}
@app.get("/api/me")
def me(user=Depends(actor)): return user
@app.get("/api/users")
def users(user=Depends(actor)):
    with closing(connect()) as db:
        return [dict(r) for r in db.execute(f"SELECT {PUBLIC} FROM users ORDER BY name")]
@app.post("/api/users", status_code=201)
def create_user(body: NewUser, user=Depends(actor)):
    require_admin(user)
    uid = "u-" + secrets.token_hex(8)
    with transaction() as db:
        require_admin(get_user(db, user["id"]))
        if db.execute("SELECT 1 FROM users WHERE email=?", (body.email.lower(),)).fetchone():
            raise HTTPException(409, "Email already exists")
        db.execute("INSERT INTO users(id,name,email,role) VALUES (?,?,?,?)", (uid, body.name.strip(), body.email.lower(), body.role))
        audit(db, user["id"], "identity.created", uid, {"role": body.role})
        return get_user(db, uid)

def evaluate(db, user, target, action, role):
    active_admins = db.execute("SELECT count(*) FROM users WHERE role='admin' AND active=1").fetchone()[0]
    decision = rpc_call(policy.Evaluate, pb.EvaluationRequest(
        actor_role=ROLES[user["role"]], is_self=user["id"] == target["id"],
        target_role=ROLES[target["role"]], target_active=bool(target["active"]),
        active_admins=active_admins, action=ACTIONS[action], requested_role=ROLES[role]))
    if not decision.allowed: raise HTTPException(403, decision.reason)
    return decision

def propose(change, user, reason="Manually requested change", provider="manual"):
    with transaction() as db:
        fresh = get_user(db, user["id"])
        if not fresh["active"]: raise HTTPException(401, "Account inactive")
        target = get_user(db, change.target_id)
        decision = evaluate(db, fresh, target, change.action, change.role)
        pid = secrets.token_hex(16)
        db.execute("INSERT INTO proposals VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
            pid, user["id"], target["id"], change.action, change.role, target["version"],
            reason, provider, decision.risk, "pending", now(), now() + 600))
        audit(db, user["id"], "proposal.created", target["id"], {"proposal_id": pid, "provider": provider})
        return dict(db.execute("SELECT * FROM proposals WHERE id=?", (pid,)).fetchone())

@app.post("/api/proposals", status_code=201)
def create_proposal(body: Change, user=Depends(actor)): return propose(body, user)
@app.post("/api/ai/draft", status_code=201)
def ai_draft(body: Draft, user=Depends(actor)):
    if user["role"] == "viewer": raise HTTPException(403, "Viewer accounts cannot draft changes")
    rate_limit("ai:" + user["id"], 10)
    if not flags(user)["effective"]["ai_assistant"]: raise HTTPException(403, "AI assistant is not enabled for your cohort")
    with closing(connect()) as db: get_user(db, body.target_id)
    try:
        with tracer.start_as_current_span("ai.draft"):
            result = draft(body.prompt)
    except ValueError as error: raise HTTPException(422, str(error))
    except Exception: raise HTTPException(502, "AI provider unavailable; use the manual controls")
    return propose(Change(target_id=body.target_id, action=result["action"], role=result["role"]),
                   user, result["reason"], result["provider"])
@app.get("/api/proposals")
def proposals(user=Depends(actor)):
    with closing(connect()) as db:
        return [dict(r) for r in db.execute("SELECT * FROM proposals WHERE actor_id=? ORDER BY created DESC LIMIT 100", (user["id"],))]
@app.post("/api/proposals/{pid}/apply")
def apply_proposal(pid: str, body: Confirm, user=Depends(actor)):
    with transaction() as db:
        row = db.execute("SELECT * FROM proposals WHERE id=? AND actor_id=?", (pid, user["id"])).fetchone()
        if not row: raise HTTPException(404, "Proposal not found")
        if row["status"] != "pending": raise HTTPException(409, "Proposal is already resolved")
        if row["expires"] <= now(): raise HTTPException(409, "Proposal expired; create a new one")
        fresh = get_user(db, user["id"])
        if not fresh["active"]: raise HTTPException(401, "Account inactive")
        target = get_user(db, row["target_id"])
        if target["version"] != row["target_version"]: raise HTTPException(409, "Identity changed since this proposal; review a new proposal")
        if row["provider"] != "manual":
            percent = db.execute("SELECT percent FROM flags WHERE name='ai_assistant'").fetchone()[0]
            if not rpc_call(policy.Flight, pb.FlightRequest(subject=user["id"], flag="ai_assistant", percent=percent)).enabled:
                raise HTTPException(403, "AI assistant disabled; create a manual proposal")
        evaluate(db, fresh, target, row["action"], row["role"])
        if row["action"] == "change_role":
            db.execute("UPDATE users SET role=?,version=version+1 WHERE id=?", (row["role"], target["id"]))
        else:
            db.execute("UPDATE users SET active=?,version=version+1 WHERE id=?", (int(row["action"] == "restore"), target["id"]))
        db.execute("DELETE FROM sessions WHERE user_id=?", (target["id"],))
        db.execute("UPDATE proposals SET status='applied' WHERE id=?", (pid,))
        updated = get_user(db, target["id"])
        audit(db, user["id"], "identity." + row["action"], target["id"], {
            "proposal_id": pid, "before": {k: target[k] for k in ("role", "active", "version")},
            "after": {k: updated[k] for k in ("role", "active", "version")}})
        return updated
@app.post("/api/proposals/{pid}/cancel")
def cancel(pid: str, user=Depends(actor)):
    with transaction() as db:
        row = db.execute("SELECT * FROM proposals WHERE id=? AND actor_id=?", (pid, user["id"])).fetchone()
        if not row: raise HTTPException(404, "Proposal not found")
        if row["status"] != "pending": raise HTTPException(409, "Proposal is already resolved")
        db.execute("UPDATE proposals SET status='cancelled' WHERE id=?", (pid,))
        audit(db, user["id"], "proposal.cancelled", row["target_id"], {"proposal_id": pid})
    return {"ok": True}
@app.get("/api/flags")
def flags(user=Depends(actor)):
    with closing(connect()) as db: rows = [dict(r) for r in db.execute("SELECT * FROM flags ORDER BY name")]
    effective = {r["name"]: rpc_call(policy.Flight, pb.FlightRequest(subject=user["id"], flag=r["name"], percent=r["percent"])).enabled for r in rows}
    return {"flags": rows, "effective": effective, "ai_provider": os.getenv("AI_PROVIDER", "demo")}
@app.put("/api/flags/{name}")
def update_flag(name: str, body: Flag, user=Depends(actor)):
    require_admin(user)
    with transaction() as db:
        require_admin(get_user(db, user["id"]))
        row = db.execute("SELECT * FROM flags WHERE name=?", (name,)).fetchone()
        if not row: raise HTTPException(404, "Flag not found")
        if row["version"] != body.version: raise HTTPException(409, "Flag changed; refresh first")
        db.execute("UPDATE flags SET percent=?,version=version+1 WHERE name=?", (body.percent, name))
        audit(db, user["id"], "flag.updated", name, {"before": row["percent"], "after": body.percent})
    return {"ok": True}
@app.get("/api/audit")
def audit_log(user=Depends(actor)):
    if user["role"] == "viewer": raise HTTPException(403, "Operator or administrator role required")
    with closing(connect()) as db:
        return [dict(r) for r in db.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 200")]
@app.post("/api/events", status_code=202)
def event(body: Event, user=Depends(actor)):
    rate_limit("events:" + user["id"], 60)
    attributes = {"event.name": body.name, "surface": body.surface}
    events.add(1, attributes)
    if body.name in ("task_completed", "task_failed"): duration.record(body.duration_ms, attributes)
    return {"ok": True}

dist = ROOT / "apps/admin/dist"
if dist.is_dir():
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")
    @app.get("/")
    @app.get("/review")
    def index(): return FileResponse(dist / "index.html")
