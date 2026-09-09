"""Single launcher with process cleanup. Run from the repository root."""
import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
root=Path(__file__).resolve().parents[1]
os.chdir(root)
parser=argparse.ArgumentParser()
parser.add_argument('--production',action='store_true',help='Serve built frontend from gateway')
parser.add_argument('--test',action='store_true',help='Use disposable database and browser-test credentials')
args=parser.parse_args()
if (root/'.env').exists():
    for line in (root/'.env').read_text().splitlines():
        if line and not line.startswith('#') and '=' in line:
            key,value=line.split('=',1);os.environ.setdefault(key,value)
temp=None
if args.test:
    temp=tempfile.TemporaryDirectory()
    os.environ.update(DATABASE_PATH=str(Path(temp.name)/'test.db'),ADMIN_PASSWORD='browser-test-password-2026!',
        POLICY_TOKEN='browser-test-service-token-at-least-32-characters',AI_PROVIDER='demo',
        COOKIE_SECURE='false',ADMIN_EMAIL='admin@example.test',SEED_DEMO='true')
if args.production: os.environ['APP_ORIGIN']='http://127.0.0.1:8000'
commands=[[sys.executable,'-m','services.policy.server'],
          [sys.executable,'-m','uvicorn','services.gateway.app:app','--host','127.0.0.1','--port','8000']]
if not args.production: commands.append(['npm','run','dev'])
children=[]
def stop(*_): raise KeyboardInterrupt
signal.signal(signal.SIGTERM,stop)
signal.signal(signal.SIGINT,stop)
try:
    for command in commands: children.append(subprocess.Popen(command))
    print('Open http://127.0.0.1:8000' if args.production else 'Open http://localhost:5173',flush=True)
    while all(p.poll() is None for p in children): time.sleep(.3)
    raise SystemExit('A service exited; inspect its error above.')
except KeyboardInterrupt: pass
finally:
    for p in children:
        if p.poll() is None:p.terminate()
    for p in children:
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.kill();p.wait()
    if temp:temp.cleanup()
