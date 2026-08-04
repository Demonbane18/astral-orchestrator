import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "plugins/astral-orchestrator/scripts/configure-effort.py"
with tempfile.TemporaryDirectory() as directory:
    settings = Path(directory) / "effort-levels.toml"
    settings.write_text('[effort]\norchestrator = "high"\nluna = "max"\nterra = "xhigh"\nreviewer = "high"\n', encoding="utf-8")
    before = settings.read_bytes()
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--settings-file", str(settings), "--check", "--expect", "luna=max", "--expect", "reviewer=high", "--json"],
        check=False, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["changed"] is False
    assert report["matched"] is True
    assert report["settings_file"] == str(settings)
    assert settings.read_bytes() == before
    mismatch = subprocess.run(
        [sys.executable, str(SCRIPT), "--settings-file", str(settings), "--check", "--expect", "luna=low", "--json"],
        check=False, capture_output=True, text=True,
    )
    assert mismatch.returncode != 0
    assert settings.read_bytes() == before
