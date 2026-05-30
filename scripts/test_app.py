import sys
from pathlib import Path

# ensure project root is on sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)
resp = client.get('/health')
print(resp.status_code)
print(resp.json())
