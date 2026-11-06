"""Execute Task 9 Node unit tests under the existing frontend unittest CI job."""
import shutil
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


class Task9NodeRunner(unittest.TestCase):
    def test_task9_node_suite(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js not installed; Task 9 JS tests not run")
        result = subprocess.run(
            [node, "--test", str(HERE / "test_task9_clarify.cjs")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=40,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)


if __name__ == "__main__":
    unittest.main()
