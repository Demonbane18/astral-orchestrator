import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "plugins/astral-orchestrator/scripts/run-agent.py"
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    prompt = root / "prompt.txt"
    prompt.write_text("review only\n", encoding="utf-8")
    os.chmod(prompt, 0o600)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--role", "reviewer", "--workdir", str(root), "--prompt-file", str(prompt), "--dry-run"],
        cwd=ROOT, check=False, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    evidence = json.loads(result.stdout)
    assert evidence["role"] == "reviewer"
    assert evidence["model"] == "gpt-5.6-sol"
    assert evidence["effort"] == "high"
    assert evidence["sandbox"] == "read-only"
