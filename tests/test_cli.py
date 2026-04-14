import io
import sys
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from brigh.cli import _run_scan


class CLITests(unittest.TestCase):
    def test_run_scan_generates_all_outputs_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir(parents=True, exist_ok=True)
            (root / "src" / "main.py").write_text("print('hello')\n")

            args = Namespace(path=str(root), targets=None, add_ignore=False)
            with redirect_stdout(io.StringIO()):
                _run_scan(args)

            self.assertTrue((root / ".brigh.md").exists())
            self.assertTrue((root / "CLAUDE.md").exists())
            self.assertTrue((root / "AGENTS.md").exists())
            self.assertTrue((root / ".cursorrules").exists())
            self.assertTrue((root / ".github" / "copilot-instructions.md").exists())

    def test_run_scan_respects_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir(parents=True, exist_ok=True)
            (root / "src" / "main.py").write_text("print('hello')\n")

            args = Namespace(path=str(root), targets=["cursor"], add_ignore=False)
            with redirect_stdout(io.StringIO()):
                _run_scan(args)

            self.assertFalse((root / ".brigh.md").exists())
            self.assertFalse((root / "CLAUDE.md").exists())
            self.assertFalse((root / "AGENTS.md").exists())
            self.assertTrue((root / ".cursorrules").exists())
            self.assertFalse((root / ".github" / "copilot-instructions.md").exists())

    def test_run_scan_writes_json_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir(parents=True, exist_ok=True)
            (root / "src" / "main.py").write_text("print('hello')\n")

            args = Namespace(path=str(root), targets=["json"], add_ignore=False)
            with redirect_stdout(io.StringIO()):
                _run_scan(args)

            self.assertTrue((root / ".brigh.json").exists())
            self.assertFalse((root / ".brigh.md").exists())

    def test_run_scan_writes_agents_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir(parents=True, exist_ok=True)
            (root / "src" / "main.py").write_text("print('hello')\n")

            args = Namespace(path=str(root), targets=["agents"], add_ignore=False)
            with redirect_stdout(io.StringIO()):
                _run_scan(args)

            self.assertTrue((root / "AGENTS.md").exists())
            self.assertFalse((root / "CLAUDE.md").exists())

    def test_run_scan_adds_gitignore_entries_with_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir(parents=True, exist_ok=True)
            (root / "src" / "main.py").write_text("print('hello')\n")
            (root / ".gitignore").write_text("__pycache__/\n")

            args = Namespace(path=str(root), targets=["agents"], add_ignore=True)
            with redirect_stdout(io.StringIO()):
                _run_scan(args)

            content = (root / ".gitignore").read_text()
            self.assertIn(".brigh.md", content)
            self.assertIn("CLAUDE.md", content)
            self.assertIn(".cursorrules", content)
            self.assertIn("AGENTS.md", content)
            self.assertIn(".github/copilot-instructions.md", content)
            self.assertIn(".brigh.json", content)

    def test_run_scan_prints_gitignore_offer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir(parents=True, exist_ok=True)
            (root / "src" / "main.py").write_text("print('hello')\n")
            (root / ".gitignore").write_text("")

            args = Namespace(path=str(root), targets=["agents"], add_ignore=False)
            output = io.StringIO()
            with redirect_stdout(output):
                _run_scan(args)

            text = output.getvalue()
            self.assertIn("Reminder: If this project is public", text)
            self.assertIn(".github/copilot-instructions.md", text)
            self.assertIn(".brigh.json", text)
            self.assertIn("Found .gitignore. Re-run with --add-ignore", text)

    def test_run_scan_fails_for_invalid_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "does-not-exist"
            args = Namespace(path=str(missing), targets=None, add_ignore=False)

            with self.assertRaises(SystemExit) as ctx:
                with redirect_stdout(io.StringIO()):
                    _run_scan(args)

            self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
