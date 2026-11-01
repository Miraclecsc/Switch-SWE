#!/usr/bin/env python3
"""Check the unchanged launcher without loading user configuration or credentials."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="context-wrapper-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.binary = self.directory / "fake-opencode"
        self.binary.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "print(json.dumps({'args': sys.argv[1:], "
            "'config': json.loads(os.environ.get('OPENCODE_CONFIG_CONTENT', '{}'))}))\n"
        )
        self.binary.chmod(0o755)

    def invoke(self, mode=None):
        config = {"model": "local/model", "plugin": ["existing-plugin"]}
        env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": str(self.directory),
            "OPENCODE_UPSTREAM_BIN": str(self.binary),
            "OPENCODE_CONFIG_CONTENT": json.dumps(config),
        }
        if mode is not None:
            env["OPENCODE_CONTEXT_MODE"] = mode
        args = ["run", "--session", "session-test", "--", "request with spaces"]
        completed = subprocess.run(
            [str(ROOT / "opencode_plus"), *args], env=env, cwd=self.directory,
            capture_output=True, text=True, timeout=10,
        )
        return completed, config, args

    def test_default_x_preserves_configuration_and_arguments(self):
        completed, config, args = self.invoke()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        data = json.loads(completed.stdout)
        self.assertEqual(data["args"], args)
        self.assertEqual(data["config"]["model"], config["model"])
        self.assertEqual(data["config"]["plugin"], [
            "existing-plugin", [(ROOT / "plugin.mjs").as_uri(), {"mode": "x"}],
        ])

    def test_a_mode_is_registered(self):
        completed, _, _ = self.invoke("a")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["config"]["plugin"][-1][1], {"mode": "a"})

    def test_off_does_not_register_plugin(self):
        completed, config, args = self.invoke("off")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), {"config": config, "args": args})

    def test_invalid_mode_fails_before_launch(self):
        completed, _, _ = self.invoke("invalid")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must be off, a, or x", completed.stderr)
        self.assertEqual(completed.stdout, "")


if __name__ == "__main__":
    unittest.main()
