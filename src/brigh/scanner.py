"""
Scanner module for Brígh.

Walks the project directory and collects raw data about the codebase:
files, configs, dependencies, and structure.
"""

import json
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    tomllib = None

# Directories we should never scan — node_modules alone
# could take minutes and tells us nothing useful.
# No thanks, we don't need to sniff 400,000 files of someone else's code. — LAT
IGNORED_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".output",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    "egg-info",
}

# Config files we specifically want to read and parse.
CONFIG_FILES = {
    "package.json",
    "tsconfig.json",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "setup.py",
    "setup.cfg",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Dockerfile",
    ".env.example",
    ".env.local.example",
    "tailwind.config.js",
    "tailwind.config.ts",
    "vite.config.js",
    "vite.config.ts",
    "next.config.js",
    "next.config.ts",
    "next.config.mjs",
    "webpack.config.js",
    ".eslintrc",
    ".eslintrc.js",
    ".eslintrc.json",
    ".prettierrc",
    ".prettierrc.json",
    "jest.config.js",
    "jest.config.ts",
    "vitest.config.ts",
    "vitest.config.js",
    "supabase/config.toml",
    "firebase.json",
    ".firebaserc",
    "vercel.json",
    "netlify.toml",
    "fly.toml",
    "render.yaml",
    "Procfile",
    "Cargo.toml",
    "go.mod",
    "composer.json",
    "Gemfile",
}


def scan_project(root: Path) -> dict[str, Any]:
    """
    Walk the project tree and collect everything we need.

    Returns a dictionary with:
        - files: list of all file paths (relative to root)
        - file_extensions: count of each extension
        - configs: dict of config filename -> contents
        - folders: list of top-level directory names
        - total_files: int
    """
    root = root.resolve()
    files: list[str] = []
    file_extensions: dict[str, int] = {}
    configs: dict[str, str] = {}
    folders: set[str] = set()

    for item in _walk(root, visited_realpaths={root.resolve()}):
        relative = item.relative_to(root)

        # Track top-level folders for structure analysis.
        parts = relative.parts
        if len(parts) > 1 and parts[0] not in IGNORED_DIRS:
            folders.add(parts[0])

        if item.is_file():
            files.append(str(relative))

            # Count file extensions.
            ext = item.suffix.lower()
            if ext:
                file_extensions[ext] = file_extensions.get(ext, 0) + 1

            # Read config files we care about.
            relative_str = str(relative).replace("\\", "/")
            if item.name in CONFIG_FILES or relative_str in CONFIG_FILES:
                try:
                    content = item.read_text(encoding="utf-8", errors="ignore")
                    key = relative_str if relative_str in CONFIG_FILES else item.name
                    configs[key] = content
                except (OSError, PermissionError):
                    pass

    return {
        "root_path": str(root),
        "files": sorted(files),
        "file_extensions": dict(
            sorted(file_extensions.items(), key=lambda x: x[1], reverse=True)
        ),
        "configs": configs,
        "folders": sorted(folders),
        "total_files": len(files),
    }


def parse_package_json(raw: str) -> dict[str, Any] | None:
    """Pull the useful bits out of a package.json."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    return {
        "name": data.get("name"),
        "dependencies": list(data.get("dependencies", {}).keys()),
        "dev_dependencies": list(data.get("devDependencies", {}).keys()),
        "scripts": list(data.get("scripts", {}).keys()),
    }


def parse_requirements_txt(raw: str) -> list[str]:
    """Parse a requirements.txt into a list of package names."""
    packages = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("-"):
            # Strip version specifiers: "flask>=2.0" -> "flask"
            name = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0]
            name = name.split("[")[0].strip()
            if name:
                packages.append(name.lower())
    return packages


def parse_pyproject_toml(raw: str) -> list[str]:
    """Parse pyproject.toml and extract dependency package names."""
    if tomllib is None:
        return []

    try:
        data = tomllib.loads(raw)
    except (tomllib.TOMLDecodeError, TypeError):
        return []

    packages: list[str] = []

    project = data.get("project", {})
    dependencies = project.get("dependencies", [])
    if isinstance(dependencies, list):
        packages.extend(_normalize_dependency_name(dep) for dep in dependencies)

    optional_deps = project.get("optional-dependencies", {})
    if isinstance(optional_deps, dict):
        for dep_group in optional_deps.values():
            if isinstance(dep_group, list):
                packages.extend(_normalize_dependency_name(dep) for dep in dep_group)

    poetry = data.get("tool", {}).get("poetry", {})
    poetry_deps = poetry.get("dependencies", {})
    if isinstance(poetry_deps, dict):
        packages.extend(_normalize_dependency_name(name) for name in poetry_deps.keys())

    return sorted({pkg for pkg in packages if pkg and pkg != "python"})


def _normalize_dependency_name(dep: str) -> str:
    """
    Normalize dependency strings to bare package names.
    Examples:
    - "flask>=2.3" -> "flask"
    - "uvicorn[standard]>=0.22" -> "uvicorn"
    """
    normalized = dep.strip().lower()
    for separator in (";", "==", ">=", "<=", "~=", "!=", ">", "<", "=", " "):
        if separator in normalized:
            normalized = normalized.split(separator, 1)[0]
    if "[" in normalized:
        normalized = normalized.split("[", 1)[0]
    return normalized.strip()


def _walk(root: Path, visited_realpaths: set[Path] | None = None):
    """
    Recursively yield all paths under root, skipping ignored directories.
    We roll our own instead of using os.walk so we can bail out of
    ignored directories early without descending into them.
    """
    if visited_realpaths is None:
        visited_realpaths = set()

    try:
        entries = sorted(root.iterdir())
    except (OSError, PermissionError):
        return

    for entry in entries:
        if entry.is_dir():
            if entry.name in IGNORED_DIRS or entry.name.startswith("."):
                continue
            # Avoid symlink recursion and out-of-tree traversal via linked dirs.
            if entry.is_symlink():
                continue
            try:
                real_dir = entry.resolve()
            except OSError:
                continue
            if real_dir in visited_realpaths:
                continue
            visited_realpaths.add(real_dir)
            yield entry
            yield from _walk(entry, visited_realpaths)
        else:
            yield entry
