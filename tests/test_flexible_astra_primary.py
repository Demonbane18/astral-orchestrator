"""Primary effort must not constrain independently selected child effort."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / 'plugins/astral-orchestrator/scripts/check-primary.py'


class FlexiblePrimaryTests(unittest.TestCase):
    def test_sol_and_astra_primary_use_the_observed_effort(self):
        thread = '12345678-1234-1234-1234-123456789abc'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = root / 'settings.toml'
            original = '[effort]\norchestrator = "high"\nastra = "medium"\nreviewer = "ultra"\n'
            settings.write_text(original)
            rollout = root / f'rollout-primary-{thread}.jsonl'
            command = ['python3', str(CHECK), '--thread-id', thread,
                       '--sessions-dir', str(root), '--settings-file', str(settings)]
            for model in ('gpt-5.6-sol', 'gpt-6-astra'):
                for effort in ('none', 'minimal', 'light', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra'):
                    with self.subTest(model=model, effort=effort):
                        rollout.write_text('\n'.join(json.dumps(row) for row in (
                            {'type': 'session_meta', 'payload': {'id': thread}},
                            {'type': 'turn_context', 'payload': {
                                'model': model, 'effort': effort,
                                'permission_profile': {'type': 'managed'}, 'cwd': str(ROOT),
                                'sandbox_policy': {'type': 'workspace-write'}}},
                        )) + '\n')
                        result = subprocess.run(command, capture_output=True, text=True)
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        evidence = json.loads(result.stdout)
                        self.assertEqual(evidence['observed_model'], model)
                        self.assertEqual(evidence['observed_effort'], effort)
                        strict_flag = '--require-sol-ultra' if model == 'gpt-5.6-sol' else '--require-astra-ultra'
                        strict = subprocess.run(command + [strict_flag], capture_output=True, text=True)
                        self.assertEqual(strict.returncode, 0 if effort == 'ultra' else 1)
                        self.assertEqual(settings.read_text(), original)

            for model, effort, status in [('gpt-5.6-terra', 'low', 'mismatch'),
                                           ('gpt-6-astra', 'invented', 'invalid')]:
                rollout.write_text('\n'.join(json.dumps(row) for row in (
                    {'type': 'session_meta', 'payload': {'id': thread}},
                    {'type': 'turn_context', 'payload': {
                            'model': model, 'effort': effort,
                            'permission_profile': {'type': 'managed'}, 'cwd': str(ROOT), 'sandbox_policy': {'type': 'workspace-write'}}},
                )) + '\n')
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stdout)['status'], status)

    def test_modes_keep_child_effort_independent_and_nonworker_modes_closed(self):
        base = ROOT / 'plugins/astral-orchestrator/skills/astral-orchestrator'
        skill = ' '.join((base / 'SKILL.md').read_text().split()).lower()
        primary = ' '.join((base / 'references/primary-verification.md').read_text().split()).lower()
        hypernova = ' '.join((base / 'references/hypernova-mode.md').read_text().split()).lower()
        self.assertIn('comet and singularity never spawn', skill)
        self.assertIn('primary and child settings are independent', skill)
        self.assertIn('configured `astra` effort', hypernova)
        self.assertIn('higher configured worker effort than a light or medium sol or astra primary', primary)
        self.assertIn('mandatory fresh reviewer', hypernova)
        self.assertIn('user confirmation cannot replace runtime evidence', hypernova)
        self.assertIn('workers cannot delegate', hypernova)
