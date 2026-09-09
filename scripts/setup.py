"""Generate local secrets once; never prints passwords to logs."""
import secrets
from pathlib import Path
path=Path(__file__).resolve().parents[1]/'.env'
if path.exists(): raise SystemExit('.env exists; leaving it unchanged.')
text=(path.parent/'.env.example').read_text().replace('REPLACE_WITH_RANDOM_PASSWORD',secrets.token_urlsafe(24)).replace('REPLACE_WITH_RANDOM_SERVICE_TOKEN',secrets.token_hex(32))
path.write_text(text)
path.chmod(0o600)
print('Created .env with unique credentials. Open it locally to read ADMIN_PASSWORD.')
