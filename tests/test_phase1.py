import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from brigh.detectors import detect_all
from brigh.generator import write_all
from brigh.scanner import parse_pyproject_toml, scan_project


class Phase1Tests(unittest.TestCase):
    def test_scan_project_detects_nested_config_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "supabase").mkdir(parents=True, exist_ok=True)
            (root / "src").mkdir(parents=True, exist_ok=True)
            (root / "supabase" / "config.toml").write_text("project_id = 'abc'\n")
            (root / "src" / "main.py").write_text("print('hello')\n")

            result = scan_project(root)

            self.assertIn("supabase/config.toml", result["configs"])
            self.assertIn("src", result["folders"])
            self.assertIn("supabase", result["folders"])

    def test_scan_project_skips_symlinked_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir(parents=True, exist_ok=True)
            (root / "src" / "main.py").write_text("print('hello')\n")
            (root / "linked-src").symlink_to(root / "src", target_is_directory=True)

            result = scan_project(root)

            self.assertIn("src/main.py", result["files"])
            self.assertNotIn("linked-src/main.py", result["files"])

    def test_parse_pyproject_toml_collects_project_and_poetry_dependencies(self):
        raw = """
[project]
dependencies = [
  "fastapi>=0.100",
  "uvicorn[standard]>=0.22; python_version >= '3.10'"
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.poetry.dependencies]
python = "^3.11"
sqlalchemy = "^2.0"
"""
        deps = set(parse_pyproject_toml(raw))
        self.assertIn("fastapi", deps)
        self.assertIn("uvicorn", deps)
        self.assertIn("pytest", deps)
        self.assertIn("sqlalchemy", deps)
        self.assertNotIn("python", deps)

    def test_detect_all_uses_pyproject_dependencies(self):
        scan_data = {
            "configs": {
                "pyproject.toml": """
[project]
dependencies = ["fastapi>=0.100", "sqlalchemy>=2.0", "pytest>=8.0"]
"""
            },
            "file_extensions": {".py": 2},
            "files": ["src/main.py"],
            "folders": ["src"],
        }

        result = detect_all(scan_data)
        self.assertEqual(result["framework"], "FastAPI")
        self.assertEqual(result["database"], "SQLAlchemy")
        self.assertIn("pytest", result["testing"])

    def test_detect_testing_infers_unittest_from_test_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tests").mkdir(parents=True, exist_ok=True)
            (root / "tests" / "test_sample.py").write_text(
                "import unittest\n\nclass T(unittest.TestCase):\n    pass\n"
            )

            scan_data = scan_project(root)
            result = detect_all(scan_data)

            self.assertIn("unittest", result["testing"])
            self.assertIn("testing", result["evidence"])

    def test_write_all_writes_json_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_all(
                "content",
                Path(tmp),
                targets=["json"],
                json_payload={"ok": True},
            )
            self.assertEqual([p.name for p in paths], [".brigh.json"])
            self.assertTrue((Path(tmp) / ".brigh.json").exists())

    def test_write_all_validates_unknown_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                write_all("content", Path(tmp), targets=["unknown"])

    def test_write_all_is_deterministic_and_deduplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_all("content", Path(tmp), targets=["agents", "cursor", "brigh", "cursor"])
            names = [p.name for p in paths]
            self.assertEqual(names, [".brigh.md", ".cursorrules", "AGENTS.md"])


if __name__ == "__main__":
    unittest.main()
