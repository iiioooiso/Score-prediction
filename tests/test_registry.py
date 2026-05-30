import subprocess
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_prepare_data_creates_registry(tmp_path):
    # run prepare_data
    res = subprocess.run(["python", str(ROOT / "scripts" / "prepare_data.py")], capture_output=True, text=True)
    assert res.returncode == 0, f"prepare_data failed: {res.stderr}"
    out = ROOT / "data" / "processed" / "facet_registry.json"
    assert out.exists(), "facet_registry.json not created"
    with out.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) > 0
    sample = data[0]
    assert "facet_id" in sample
    assert "facet_name" in sample
