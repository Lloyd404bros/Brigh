"""
Detectors module for Brígh.

Takes raw scan data and identifies frameworks, tools, patterns,
and conventions. This is where the intelligence lives.
"""

from pathlib import Path
from typing import Any


def detect_all(scan_data: dict[str, Any]) -> dict[str, Any]:
    """
    Run all detectors against the scan data and return
    a structured summary of everything we found.
    """
    configs = scan_data.get("configs", {})
    extensions = scan_data.get("file_extensions", {})
    files = scan_data.get("files", [])
    folders = scan_data.get("folders", [])
    root_path = scan_data.get("root_path")

    # Parse package.json if present — most JS/TS projects have one.
    from brigh.scanner import (
        parse_package_json,
        parse_pyproject_toml,
        parse_requirements_txt,
    )

    pkg = None
    if "package.json" in configs:
        pkg = parse_package_json(configs["package.json"])

    py_deps: set[str] = set()
    if "requirements.txt" in configs:
        py_deps.update(parse_requirements_txt(configs["requirements.txt"]))
    if "pyproject.toml" in configs:
        py_deps.update(parse_pyproject_toml(configs["pyproject.toml"]))
    py_deps_list = sorted(py_deps)

    languages, language_evidence = _detect_languages_with_evidence(extensions)
    framework, framework_evidence = _detect_framework_with_evidence(pkg, py_deps_list, configs, files)
    build_tool, build_tool_evidence = _detect_build_tool_with_evidence(pkg, configs)
    styling, styling_evidence = _detect_styling_with_evidence(pkg, configs, files)
    backend, backend_evidence = _detect_backend_with_evidence(pkg, py_deps_list, configs, files)
    database, database_evidence = _detect_database_with_evidence(pkg, py_deps_list, configs, files)
    auth, auth_evidence = _detect_auth_with_evidence(pkg, py_deps_list, files)
    testing, testing_evidence = _detect_testing_with_evidence(pkg, py_deps_list, configs, files, root_path)
    deployment, deployment_evidence = _detect_deployment_with_evidence(configs)
    linting, linting_evidence = _detect_linting_with_evidence(configs, files)
    structure = detect_structure(folders, files)
    package_manager, package_manager_evidence = _detect_package_manager_with_evidence(files)
    project_map = build_project_map(files, folders, configs, languages, package_manager)

    evidence: dict[str, list[str]] = {}
    if language_evidence:
        evidence["languages"] = language_evidence
    if framework_evidence:
        evidence["framework"] = [framework_evidence]
    if build_tool_evidence:
        evidence["build_tool"] = [build_tool_evidence]
    if styling_evidence:
        evidence["styling"] = styling_evidence
    if backend_evidence:
        evidence["backend"] = [backend_evidence]
    if database_evidence:
        evidence["database"] = [database_evidence]
    if auth_evidence:
        evidence["auth"] = [auth_evidence]
    if testing_evidence:
        evidence["testing"] = testing_evidence
    if deployment_evidence:
        evidence["deployment"] = [deployment_evidence]
    if linting_evidence:
        evidence["linting"] = linting_evidence
    if package_manager_evidence:
        evidence["package_manager"] = [package_manager_evidence]

    return {
        "languages": languages,
        "framework": framework,
        "build_tool": build_tool,
        "styling": styling,
        "backend": backend,
        "database": database,
        "auth": auth,
        "testing": testing,
        "deployment": deployment,
        "linting": linting,
        "structure": structure,
        "package_manager": package_manager,
        "project_map": project_map,
        "evidence": evidence,
    }


def detect_languages(extensions: dict[str, int]) -> list[str]:
    """Figure out what languages are in use from file extensions."""
    return _detect_languages_with_evidence(extensions)[0]


def _detect_languages_with_evidence(extensions: dict[str, int]) -> tuple[list[str], list[str]]:
    """Detect languages plus evidence lines."""
    lang_map = {
        ".js": "JavaScript",
        ".jsx": "React (JSX)",
        ".ts": "TypeScript",
        ".tsx": "React (TSX)",
        ".py": "Python",
        ".rb": "Ruby",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".cs": "C#",
        ".vue": "Vue",
        ".svelte": "Svelte",
    }
    found = []
    evidence = []
    for ext, count in extensions.items():
        if ext in lang_map and count > 0:
            found.append(lang_map[ext])
            evidence.append(f"{lang_map[ext]} from {ext} files ({count})")
    return found, evidence


def detect_framework(
    pkg: dict | None,
    py_deps: list[str],
    configs: dict[str, str],
    files: list[str],
) -> str | None:
    """Detect the primary framework."""
    return _detect_framework_with_evidence(pkg, py_deps, configs, files)[0]


def _detect_framework_with_evidence(
    pkg: dict | None,
    py_deps: list[str],
    configs: dict[str, str],
    files: list[str],
) -> tuple[str | None, str | None]:
    """Detect the primary framework plus evidence."""
    if pkg:
        deps = set(pkg.get("dependencies", []) + pkg.get("dev_dependencies", []))

        if "next" in deps or any(f in configs for f in ("next.config.js", "next.config.ts", "next.config.mjs")):
            return "Next.js", "Detected from Next.js dependency/config"
        if "nuxt" in deps or "nuxt3" in deps:
            return "Nuxt", "Detected from Nuxt dependency"
        if "gatsby" in deps:
            return "Gatsby", "Detected from Gatsby dependency"
        if "remix" in deps or "@remix-run/node" in deps:
            return "Remix", "Detected from Remix dependency"
        if "astro" in deps:
            return "Astro", "Detected from Astro dependency"
        if "svelte" in deps or "@sveltejs/kit" in deps:
            if "@sveltejs/kit" in deps:
                return "SvelteKit", "Detected from @sveltejs/kit dependency"
            return "Svelte", "Detected from svelte dependency"
        if "vue" in deps:
            return "Vue", "Detected from vue dependency"
        if "react" in deps:
            return "React", "Detected from react dependency"
        if "angular" in deps or "@angular/core" in deps:
            return "Angular", "Detected from Angular dependency"
        if "express" in deps:
            return "Express", "Detected from express dependency"

    # Python frameworks.
    if "django" in py_deps:
        return "Django", "Detected from django dependency"
    if "flask" in py_deps:
        return "Flask", "Detected from flask dependency"
    if "fastapi" in py_deps:
        return "FastAPI", "Detected from fastapi dependency"

    return None, None


def detect_build_tool(
    pkg: dict | None, configs: dict[str, str]
) -> str | None:
    """Detect the build tool or bundler."""
    return _detect_build_tool_with_evidence(pkg, configs)[0]


def _detect_build_tool_with_evidence(
    pkg: dict | None, configs: dict[str, str]
) -> tuple[str | None, str | None]:
    """Detect build tool plus evidence."""
    if any(f in configs for f in ("vite.config.js", "vite.config.ts")):
        return "Vite", "Detected from vite config file"
    if "webpack.config.js" in configs:
        return "Webpack", "Detected from webpack config file"
    if pkg:
        deps = set(pkg.get("dependencies", []) + pkg.get("dev_dependencies", []))
        if "vite" in deps:
            return "Vite", "Detected from vite dependency"
        if "esbuild" in deps:
            return "esbuild", "Detected from esbuild dependency"
        if "parcel" in deps:
            return "Parcel", "Detected from parcel dependency"
        if "turbo" in deps:
            return "Turborepo", "Detected from turbo dependency"
    return None, None


def detect_styling(
    pkg: dict | None,
    configs: dict[str, str],
    files: list[str],
) -> list[str]:
    """Detect CSS/styling approaches."""
    return _detect_styling_with_evidence(pkg, configs, files)[0]


def _detect_styling_with_evidence(
    pkg: dict | None,
    configs: dict[str, str],
    files: list[str],
) -> tuple[list[str], list[str]]:
    """Detect styling approaches plus evidence."""
    found = []
    evidence = []
    has_tailwind_config = any(
        f in configs
        for f in ("tailwind.config.js", "tailwind.config.ts")
    )

    if pkg:
        deps = set(pkg.get("dependencies", []) + pkg.get("dev_dependencies", []))
        if "tailwindcss" in deps or has_tailwind_config:
            found.append("Tailwind CSS")
            evidence.append("Tailwind CSS from dependency/config")
        if "styled-components" in deps:
            found.append("Styled Components")
            evidence.append("Styled Components from dependency")
        if "@emotion/react" in deps or "@emotion/styled" in deps:
            found.append("Emotion")
            evidence.append("Emotion from dependency")
        if "sass" in deps or "node-sass" in deps:
            found.append("Sass/SCSS")
            evidence.append("Sass/SCSS from dependency")

    # Check for CSS modules by file naming pattern.
    if any(".module.css" in f or ".module.scss" in f for f in files):
        found.append("CSS Modules")
        evidence.append("CSS Modules from *.module.css/scss files")

    return found, evidence


def detect_backend(
    pkg: dict | None,
    py_deps: list[str],
    configs: dict[str, str],
    files: list[str],
) -> str | None:
    """Detect backend/BaaS services."""
    return _detect_backend_with_evidence(pkg, py_deps, configs, files)[0]


def _detect_backend_with_evidence(
    pkg: dict | None,
    py_deps: list[str],
    configs: dict[str, str],
    files: list[str],
) -> tuple[str | None, str | None]:
    """Detect backend/BaaS plus evidence."""
    if "supabase/config.toml" in configs:
        return "Supabase", "Detected from supabase/config.toml"
    if pkg:
        deps = set(pkg.get("dependencies", []) + pkg.get("dev_dependencies", []))
        if "@supabase/supabase-js" in deps:
            return "Supabase", "Detected from @supabase/supabase-js dependency"
        if "firebase" in deps or "firebase-admin" in deps:
            return "Firebase", "Detected from firebase dependency"
        if "@aws-amplify/core" in deps or "aws-amplify" in deps:
            return "AWS Amplify", "Detected from aws-amplify dependency"
        if "@prisma/client" in deps:
            return "Prisma", "Detected from @prisma/client dependency"

    if "firebase.json" in configs or ".firebaserc" in configs:
        return "Firebase", "Detected from Firebase config files"

    if "supabase" in py_deps:
        return "Supabase", "Detected from supabase Python dependency"

    return None, None


def detect_database(
    pkg: dict | None,
    py_deps: list[str],
    configs: dict[str, str],
    files: list[str],
) -> str | None:
    """Detect database technology."""
    return _detect_database_with_evidence(pkg, py_deps, configs, files)[0]


def _detect_database_with_evidence(
    pkg: dict | None,
    py_deps: list[str],
    configs: dict[str, str],
    files: list[str],
) -> tuple[str | None, str | None]:
    """Detect database technology plus evidence."""
    if pkg:
        deps = set(pkg.get("dependencies", []) + pkg.get("dev_dependencies", []))
        if "mongoose" in deps or "mongodb" in deps:
            return "MongoDB", "Detected from mongodb/mongoose dependency"
        if "pg" in deps or "postgres" in deps:
            return "PostgreSQL", "Detected from pg/postgres dependency"
        if "mysql2" in deps or "mysql" in deps:
            return "MySQL", "Detected from mysql dependency"
        if "better-sqlite3" in deps or "sqlite3" in deps:
            return "SQLite", "Detected from sqlite dependency"
        if "@prisma/client" in deps:
            return "Prisma ORM", "Detected from @prisma/client dependency"
        if "drizzle-orm" in deps:
            return "Drizzle ORM", "Detected from drizzle-orm dependency"
        if "typeorm" in deps:
            return "TypeORM", "Detected from typeorm dependency"
        if "sequelize" in deps:
            return "Sequelize", "Detected from sequelize dependency"

    if "sqlalchemy" in py_deps:
        return "SQLAlchemy", "Detected from sqlalchemy dependency"
    if "psycopg2" in py_deps or "psycopg" in py_deps:
        return "PostgreSQL", "Detected from psycopg dependency"
    if "pymongo" in py_deps:
        return "MongoDB", "Detected from pymongo dependency"

    return None, None


def detect_auth(
    pkg: dict | None, py_deps: list[str], files: list[str]
) -> str | None:
    """Detect authentication approach."""
    return _detect_auth_with_evidence(pkg, py_deps, files)[0]


def _detect_auth_with_evidence(
    pkg: dict | None, py_deps: list[str], files: list[str]
) -> tuple[str | None, str | None]:
    """Detect authentication approach plus evidence."""
    if pkg:
        deps = set(pkg.get("dependencies", []) + pkg.get("dev_dependencies", []))
        if "@supabase/auth-helpers-react" in deps or "@supabase/ssr" in deps:
            return "Supabase Auth", "Detected from Supabase auth helper dependency"
        if "next-auth" in deps or "@auth/core" in deps:
            return "NextAuth / Auth.js", "Detected from next-auth/auth.js dependency"
        if "@clerk/nextjs" in deps or "@clerk/clerk-react" in deps:
            return "Clerk", "Detected from Clerk dependency"
        if "firebase" in deps:
            # Could be auth, check for auth-specific imports later.
            return "Firebase Auth", "Detected from firebase dependency"
        if "passport" in deps:
            return "Passport.js", "Detected from passport dependency"
        if "@auth0/auth0-react" in deps or "auth0" in deps:
            return "Auth0", "Detected from Auth0 dependency"

    if "django-allauth" in py_deps:
        return "django-allauth", "Detected from django-allauth dependency"
    if "flask-login" in py_deps:
        return "Flask-Login", "Detected from flask-login dependency"

    return None, None


def detect_testing(
    pkg: dict | None,
    py_deps: list[str],
    configs: dict[str, str],
    files: list[str] | None = None,
    root_path: str | None = None,
) -> list[str]:
    """Detect testing frameworks."""
    return _detect_testing_with_evidence(pkg, py_deps, configs, files or [], root_path)[0]


def _detect_testing_with_evidence(
    pkg: dict | None,
    py_deps: list[str],
    configs: dict[str, str],
    files: list[str],
    root_path: str | None,
) -> tuple[list[str], list[str]]:
    """Detect testing frameworks plus evidence."""
    found = []
    evidence = []
    if pkg:
        deps = set(pkg.get("dependencies", []) + pkg.get("dev_dependencies", []))
        if "jest" in deps or any(f in configs for f in ("jest.config.js", "jest.config.ts")):
            found.append("Jest")
            evidence.append("Jest from dependency/config")
        if "vitest" in deps or any(f in configs for f in ("vitest.config.ts", "vitest.config.js")):
            found.append("Vitest")
            evidence.append("Vitest from dependency/config")
        if "@testing-library/react" in deps:
            found.append("React Testing Library")
            evidence.append("React Testing Library from dependency")
        if "cypress" in deps:
            found.append("Cypress")
            evidence.append("Cypress from dependency")
        if "playwright" in deps or "@playwright/test" in deps:
            found.append("Playwright")
            evidence.append("Playwright from dependency")

    if "pytest" in py_deps:
        found.append("pytest")
        evidence.append("pytest from Python dependency metadata")
    if "unittest" in py_deps:
        found.append("unittest")
        evidence.append("unittest from Python dependency metadata")

    inferred_unittest = _detect_unittest_from_files(files, root_path)
    if inferred_unittest and "unittest" not in found:
        found.append("unittest")
        evidence.append(inferred_unittest)

    return found, evidence


def detect_deployment(configs: dict[str, str]) -> str | None:
    """Detect deployment platform."""
    return _detect_deployment_with_evidence(configs)[0]


def _detect_deployment_with_evidence(configs: dict[str, str]) -> tuple[str | None, str | None]:
    """Detect deployment platform plus evidence."""
    if "vercel.json" in configs:
        return "Vercel", "Detected from vercel.json"
    if "netlify.toml" in configs:
        return "Netlify", "Detected from netlify.toml"
    if "fly.toml" in configs:
        return "Fly.io", "Detected from fly.toml"
    if "render.yaml" in configs:
        return "Render", "Detected from render.yaml"
    if "Procfile" in configs:
        return "Heroku", "Detected from Procfile"
    if "Dockerfile" in configs or "docker-compose.yml" in configs:
        return "Docker", "Detected from Docker config files"
    return None, None


def detect_linting(configs: dict[str, str], files: list[str]) -> list[str]:
    """Detect linting and formatting tools."""
    return _detect_linting_with_evidence(configs, files)[0]


def _detect_linting_with_evidence(configs: dict[str, str], files: list[str]) -> tuple[list[str], list[str]]:
    """Detect linting/formatting plus evidence."""
    found = []
    evidence = []
    eslint_files = (".eslintrc", ".eslintrc.js", ".eslintrc.json")
    if any(f in configs for f in eslint_files):
        found.append("ESLint")
        evidence.append("ESLint from .eslintrc config")
    if ".prettierrc" in configs or ".prettierrc.json" in configs:
        found.append("Prettier")
        evidence.append("Prettier from .prettierrc config")
    if any(f.endswith("biome.json") for f in files):
        found.append("Biome")
        evidence.append("Biome from biome.json file")
    return found, evidence


def detect_structure(folders: list[str], files: list[str]) -> dict[str, Any]:
    """Analyse the project's folder structure."""
    info: dict[str, Any] = {}

    if "src" in folders:
        info["source_dir"] = "src/"

        # Check for common patterns inside src.
        src_subdirs = set()
        for f in files:
            parts = f.split("/")
            if len(parts) > 2 and parts[0] == "src":
                src_subdirs.add(parts[1])

        if "features" in src_subdirs:
            info["pattern"] = "Feature-based"
        elif "components" in src_subdirs and "pages" in src_subdirs:
            info["pattern"] = "Pages + Components"
        elif "components" in src_subdirs:
            info["pattern"] = "Component-based"

        info["src_subdirs"] = sorted(src_subdirs)

    if "app" in folders:
        info["source_dir"] = info.get("source_dir", "app/")
        info["uses_app_router"] = True

    if "pages" in folders:
        info["uses_pages_dir"] = True

    return info


def detect_package_manager(files: list[str]) -> str | None:
    """Detect which package manager is in use from lock files."""
    return _detect_package_manager_with_evidence(files)[0]


def _detect_package_manager_with_evidence(files: list[str]) -> tuple[str | None, str | None]:
    """Detect package manager plus evidence."""
    file_set = set(files)

    if "bun.lockb" in file_set or "bun.lock" in file_set:
        return "Bun", "Detected from bun lockfile"
    if "pnpm-lock.yaml" in file_set:
        return "pnpm", "Detected from pnpm-lock.yaml"
    if "yarn.lock" in file_set:
        return "Yarn", "Detected from yarn.lock"
    if "package-lock.json" in file_set:
        return "npm", "Detected from package-lock.json"
    if "Pipfile.lock" in file_set:
        return "Pipenv", "Detected from Pipfile.lock"
    if "poetry.lock" in file_set:
        return "Poetry", "Detected from poetry.lock"
    if "uv.lock" in file_set:
        return "uv", "Detected from uv.lock"

    return None, None


def build_project_map(
    files: list[str],
    folders: list[str],
    configs: dict[str, str],
    languages: list[str],
    package_manager: str | None,
) -> dict[str, Any]:
    """Build a concise project map with useful starting points."""
    file_set = set(files)
    config_set = set(configs.keys())

    priority_files = [
        "README.md",
        "pyproject.toml",
        "requirements.txt",
        "package.json",
        "src/main.py",
        "src/brigh/cli.py",
        "src/brigh/detectors.py",
        "tests/test_cli.py",
        "tests/test_phase1.py",
        "Dockerfile",
    ]
    key_files = [path for path in priority_files if path in file_set or path in config_set]
    if len(key_files) < 8:
        remaining = sorted(
            path
            for path in (file_set | config_set) - set(key_files)
            if _is_project_map_candidate(path)
        )
        key_files.extend(remaining[: 8 - len(key_files)])

    commands = []
    if "Python" in languages or any(path.endswith(".py") for path in files):
        commands.append("python3 -m brigh.cli scan .")
    if any(_is_python_test_file(path) for path in files):
        commands.append("python3 -m unittest discover -s tests -p 'test_*.py' -v")
    if package_manager == "npm":
        commands.append("npm test")
    if package_manager == "pnpm":
        commands.append("pnpm test")
    if package_manager == "Yarn":
        commands.append("yarn test")
    if package_manager == "Bun":
        commands.append("bun test")

    return {
        "key_files": key_files[:8],
        "top_directories": folders[:8],
        "suggested_commands": commands,
        "config_files_detected": sorted(config_set),
    }


def _is_project_map_candidate(path: str) -> bool:
    """Filter noisy/generated paths from project map key files."""
    generated = {
        ".brigh.md",
        "CLAUDE.md",
        ".cursorrules",
        ".brigh.json",
        ".github/copilot-instructions.md",
    }
    if path in generated:
        return False
    if path.startswith(".") and not path.startswith(".github/"):
        return False
    if "/." in path:
        return False
    return True


def _is_python_test_file(path: str) -> bool:
    if not path.endswith(".py"):
        return False
    name = Path(path).name
    return (
        path.startswith("tests/")
        or "/tests/" in path
        or name.startswith("test_")
        or name.endswith("_test.py")
    )


def _detect_unittest_from_files(files: list[str], root_path: str | None) -> str | None:
    """Infer unittest usage from test file patterns/imports."""
    candidates = [path for path in files if _is_python_test_file(path)]
    if not candidates:
        return None

    # Strong signal: explicit unittest import in test files.
    if root_path:
        root = Path(root_path)
        for rel_path in candidates[:25]:
            file_path = root / rel_path
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "import unittest" in text or "from unittest" in text:
                return f"unittest inferred from import in {rel_path}"

    # Fallback signal: Python test directory/file naming conventions.
    return f"unittest inferred from Python test file structure ({len(candidates)} files)"
