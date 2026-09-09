"""Real gRPC + compiled C + HTTP ASGI + SQLite integration tests."""
import os
import socket
import subprocess
import sys
import time
import secrets
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

@pytest.fixture(scope="session")
def client(tmp_path_factory):
    from fastapi.testclient import TestClient
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    os.environ.update(DATABASE_PATH=str(tmp_path_factory.mktemp("db") / "test.db"),
        ADMIN_PASSWORD="test-only-password-9284!", POLICY_TOKEN=secrets.token_hex(32),
        POLICY_ADDRESS=f"127.0.0.1:{port}", POLICY_BIND=f"127.0.0.1:{port}", AI_PROVIDER="demo")
    proc = subprocess.Popen([sys.executable, "-m", "services.policy.server"], cwd=ROOT)
    import grpc
    ch = grpc.insecure_channel(f"127.0.0.1:{port}")
    grpc.channel_ready_future(ch).result(timeout=15)
    ch.close()
    from services.gateway.app import app
    try:
        with TestClient(app) as c: yield c
    finally:
        proc.terminate(); proc.wait(timeout=10)

@pytest.fixture
def auth(client):
    from services.gateway.app import attempts
    attempts.clear()
    client.cookies.clear()
    result = client.post("/api/login", json={"email":"admin@example.test", "password":"test-only-password-9284!"})
    assert result.status_code == 200
    client.headers["x-csrf-token"] = result.json()["csrf"]
    return client

def new_identity(c, role="viewer"):
    result = c.post("/api/users", json={"name":"Test Identity", "email":secrets.token_hex(6)+"@example.test", "role":role})
    assert result.status_code == 201, result.text
    return result.json()
def proposal(c, uid, action="suspend", role="viewer"):
    return c.post("/api/proposals", json={"target_id":uid,"action":action,"role":role})

def test_unauthenticated(client):
    client.cookies.clear()
    assert client.get("/api/users").status_code == 401
def test_secure_session_and_headers(auth):
    assert "password" not in str(auth.get('/api/me').json())
    response = auth.get('/api/users')
    assert response.headers['x-frame-options'] == 'DENY'
    assert response.headers['cache-control'] == 'no-store'
    assert all('salt' not in row for row in response.json())
def test_csrf_and_origin(auth):
    body={"target_id":"u-priya","action":"suspend"}
    assert auth.post('/api/proposals',json=body,headers={'x-csrf-token':'bad'}).status_code == 403
    assert auth.post('/api/proposals',json=body,headers={'origin':'https://evil.example'}).status_code == 403
def test_self_and_last_admin_denied(auth):
    assert proposal(auth,'u-admin').status_code == 403
def test_apply_audit_and_replay(auth):
    u=new_identity(auth)
    p=proposal(auth,u['id']).json()
    assert p['status']=='pending'
    result=auth.post(f"/api/proposals/{p['id']}/apply",json={'confirmed':True})
    assert result.status_code==200, result.text
    assert result.json()['active']==0
    assert auth.post(f"/api/proposals/{p['id']}/apply",json={'confirmed':True}).status_code==409
    assert any(a['action']=='identity.suspend' and a['target_id']==u['id'] for a in auth.get('/api/audit').json())
def test_explicit_confirmation(auth):
    u=new_identity(auth); p=proposal(auth,u['id']).json()
    assert auth.post(f"/api/proposals/{p['id']}/apply",json={'confirmed':False}).status_code==422
def test_stale_version(auth):
    u=new_identity(auth)
    first=proposal(auth,u['id']).json(); second=proposal(auth,u['id'],'change_role','operator').json()
    assert auth.post(f"/api/proposals/{first['id']}/apply",json={'confirmed':True}).status_code==200
    assert auth.post(f"/api/proposals/{second['id']}/apply",json={'confirmed':True}).status_code==409
def test_expired_proposal(auth):
    from services.gateway.db import transaction
    u=new_identity(auth); p=proposal(auth,u['id']).json()
    with transaction() as db: db.execute('UPDATE proposals SET expires=0 WHERE id=?',(p['id'],))
    assert auth.post(f"/api/proposals/{p['id']}/apply",json={'confirmed':True}).status_code==409
def test_cancel(auth):
    u=new_identity(auth); p=proposal(auth,u['id']).json()
    assert auth.post(f"/api/proposals/{p['id']}/cancel").status_code==200
    assert auth.post(f"/api/proposals/{p['id']}/apply",json={'confirmed':True}).status_code==409
def test_ai_and_kill_switch(auth):
    u=new_identity(auth)
    p=auth.post('/api/ai/draft',json={'target_id':u['id'],'prompt':'change role to operator'}).json()
    assert p['provider']=='demo (rules, no model)'
    assert p['action']=='change_role'
    f=next(f for f in auth.get('/api/flags').json()['flags'] if f['name']=='ai_assistant')
    assert auth.put('/api/flags/ai_assistant',json={'percent':0,'version':f['version']}).status_code==200
    assert auth.post(f"/api/proposals/{p['id']}/apply",json={'confirmed':True}).status_code==403
    assert auth.post('/api/ai/draft',json={'target_id':u['id'],'prompt':'suspend access'}).status_code==403
    auth.put('/api/flags/ai_assistant',json={'percent':100,'version':f['version']+1})
def test_invalid_ai_and_fields(auth):
    assert auth.post('/api/ai/draft',json={'target_id':'u-priya','prompt':'do something clever'}).status_code==422
    assert auth.post('/api/proposals',json={'target_id':'u-priya','action':'delete_everything'}).status_code==422
    assert auth.post('/api/events',json={'name':'task_started','surface':'admin','email':'secret@example.test'}).status_code==422
def test_flag_conflict(auth):
    f=next(f for f in auth.get('/api/flags').json()['flags'] if f['name']=='compact_rows')
    assert auth.put('/api/flags/compact_rows',json={'percent':30,'version':f['version']}).status_code==200
    assert auth.put('/api/flags/compact_rows',json={'percent':60,'version':f['version']}).status_code==409
def test_viewer_and_operator_roles(auth):
    from services.gateway.db import transaction
    from services.gateway.app import digest, now
    u=new_identity(auth)
    token=secrets.token_urlsafe(32)
    with transaction() as db:
        db.execute('INSERT INTO sessions VALUES (?,?,?,?)',(digest(token),'u-priya','test-csrf',now()+600))
    auth.cookies.clear(); auth.cookies.set('atlas_session',token); auth.headers['x-csrf-token']='test-csrf'
    assert auth.get('/api/users').status_code==200
    assert proposal(auth,u['id']).status_code==403
    assert auth.get('/api/audit').status_code==403
    with transaction() as db: db.execute("UPDATE users SET role='operator' WHERE id='u-priya'")
    assert proposal(auth,u['id']).status_code==201
    assert proposal(auth,u['id'],'change_role','admin').status_code==403
    assert proposal(auth,'u-admin').status_code==403
    with transaction() as db: db.execute("UPDATE users SET role='viewer' WHERE id='u-priya'")
def test_policy_credential(client):
    import grpc
    from services.gateway.app import pb, rpc
    ch=grpc.insecure_channel(os.environ['POLICY_ADDRESS'])
    with pytest.raises(grpc.RpcError) as exc:
        rpc.PolicyStub(ch).Flight(pb.FlightRequest(subject='test',flag='ai',percent=100),timeout=2)
    assert exc.value.code()==grpc.StatusCode.UNAUTHENTICATED
    ch.close()
def test_oversized_body(auth):
    assert auth.post('/api/ai/draft',content='x'*17000,headers={'content-type':'application/json'}).status_code==413
def test_login_limit(auth):
    from services.gateway.app import attempts
    attempts.clear()
    statuses=[auth.post('/api/login',json={'email':'unknown@example.test','password':'bad'}).status_code for _ in range(11)]
    assert statuses[:10]==[401]*10 and statuses[-1]==429
def test_readiness(auth):
    assert auth.get('/api/ready').status_code==200
def test_logout(auth):
    assert auth.post('/api/logout').status_code==200
    assert auth.get('/api/me').status_code==401
