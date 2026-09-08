"""Primary effort must not constrain independently selected child effort."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / 'plugins/astral-orchestrator/scripts/check-primary.py'


class FlexibleAstraPrimaryTests(unittest.TestCase):
    def test_observed_efforts_override_saved_high_in_every_mode(self):
        thread = '12345678-1234-1234-1234-123456789abc'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = root / 'settings.toml'
            original = '[effort]\norchestrator = "high"\nreviewer = "ultra"\n'
            settings.write_text(original)
            rollout = root / f'rollout-primary-{thread}.jsonl'
            command = ['python3', str(CHECK), '--thread-id', thread,
                       '--sessions-dir', str(root), '--settings-file', str(settings)]
            for effort in ('none', 'minimal', 'light', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra'):
                with self.subTest(effort=effort):
                    rollout.write_text('\n'.join(json.dumps(row) for row in (
                        {'type': 'session_meta', 'payload': {'id': thread}},
                        {'type': 'turn_context', 'payload': {
                            'model': 'gpt-6-astra', 'effort': effort,
                            'permission_profile': {'type': 'managed'}, 'cwd': str(ROOT), 'sandbox_policy': {'type': 'workspace-write'}}},
                    )) + '\n')
                    result = subprocess.run(command, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertEqual(json.loads(result.stdout)['observed_effort'], effort)
                    strict = subprocess.run(command + ['--require-astra-ultra'], capture_output=True, text=True)
                    self.assertEqual(strict.returncode, 0 if effort == 'ultra' else 1)
                    self.assertEqual(settings.read_text(), original)
            for model, effort, status in [('gpt-5.6-sol', 'low', 'mismatch'),
                                           ('gpt-6-astra', 'invented', 'invalid')]:
                rollout.write_text('\n'.join(json.dumps(row) for row in (
                    {'type': 'session_meta', 'payload': {'id': thread}},
                    {'type': 'turn_context', 'payload': {'model': model, 'effort': effort,
                     'permission_profile': {'type': 'managed'}, 'cwd': str(ROOT), 'sandbox_policy': {'type': 'workspace-write'}}},
                )) + '\n')
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stdout)['status'], status)

    def test_modes_keep_child_effort_independent_and_nonworker_modes_closed(self):
        base = ROOT / 'plugins/astral-orchestrator/skills/astral-orchestrator'
        skill = (base / 'SKILL.md').read_text()
        hypernova = (base / 'references/hypernova-mode.md').read_text()
        self.assertIn('Comet and Singularity still never spawn', skill)
        self.assertIn('Worker effort is independent of primary effort', skill)
        self.assertIn('Astra Light primary can therefore launch Astra Ultra workers', hypernova)
        self.assertIn('mandatory fresh reviewer', hypernova)
        self.assertIn('user confirmation cannot replace runtime evidence', hypernova)
        self.assertIn('workers cannot delegate', hypernova)
