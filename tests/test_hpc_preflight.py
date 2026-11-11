import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CHECK = Path(__file__).resolve().parents[1] / "scripts" / "hpc-preflight.py"

class HPCPreflightTests(unittest.TestCase):
    def run_check(self, root, stage="prestart"):
        return subprocess.run(
            [sys.executable, str(CHECK), "--root", str(root), "--stage", stage],
            capture_output=True, text=True, timeout=10,
        )
    def fixture(self, root):
        (root / "server_config.json").write_text('{"namespace":"yphotosharing"}')
        (root / "prompts_ygram.json").write_text('{"caption":"test"}')
        (root / "client_test-pilot.json").write_text(json.dumps({
            "servers": {"llm":"http://192.168.68.61:8000/v1"},
            "agents": {"llm_agents":["Qwen2.5-1.5B-Instruct"]},
            "image_generation":{"enabled":False}
        }))
    def test_valid_prestart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            r = self.run_check(root)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
    def test_missing_prompts_is_actionable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            (root / "prompts_ygram.json").unlink()
            r = self.run_check(root)
            self.assertEqual(r.returncode, 1)
            self.assertIn("Missing prompts_ygram.json", r.stdout)
    def test_ray_server_markers_are_required_after_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            r = self.run_check(root, "server")
            self.assertEqual(r.returncode, 1)
            self.assertIn("ray_config.temp: absent", r.stdout)
            (root / "ray_config.temp").write_text("127.0.0.1:6379")
            (root / "ray_ready.temp").write_text("ready")
            r = self.run_check(root, "server")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

if __name__ == "__main__":
    unittest.main()
