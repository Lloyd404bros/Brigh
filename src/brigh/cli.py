"""
CLI module for Brígh.

This is the entry point. When someone types 'brigh scan',
this is what runs.
"""

import argparse
import sys
import time
from pathlib import Path

from brigh import __codename__, __version__
from brigh.scanner import scan_project
from brigh.detectors import detect_all
from brigh.generator import generate_context, generate_json_payload, write_all

# This took longer to name than to build. — LAT

GITIGNORE_CONTEXT_ENTRIES = [
    ".brigh.md",
    "CLAUDE.md",
    ".cursorrules",
    "AGENTS.md",
    ".github/copilot-instructions.md",
    ".brigh.json",
]


def main():
    """Main entry point for the brigh CLI."""
    parser = argparse.ArgumentParser(
        prog="brigh",
        # This took longer to name than to build. — LAT
        description="Brígh — The essence of your codebase, understood.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"brigh {__version__}",
    )
    parser.add_argument(
        "--about",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    subparsers = parser.add_subparsers(dest="command")

    # ── scan command ─────────────────────────────────────────
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan your project and generate AI context files.",
    )
    scan_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the project root (defaults to current directory).",
    )
    scan_parser.add_argument(
        "--targets",
        nargs="+",
        choices=["claude", "agents", "cursor", "copilot", "brigh", "json"],
        default=None,
        help="Which context files to generate (default: all).",
    )
    scan_parser.add_argument(
        "--add-ignore",
        action="store_true",
        help="Add generated context files to .gitignore automatically.",
    )
    subparsers.add_parser(
        "credits",
        help=argparse.SUPPRESS,
    )

    args = parser.parse_args()

    if args.about:
        print("\"Everyone's going to kill me when I tell them I've been using this for the past 18 months.\"")
        sys.exit(0)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "scan":
        _run_scan(args)
    elif args.command == "credits":
        _print_credits()


def _print_credits() -> None:
    print(f'Brígh v{__version__} "{__codename__}"')
    print("404Bros LTD")
    print("Born from baked beans and Buxton air.")


def _run_scan(args):
    """Execute the scan command."""
    project_path = Path(args.path).resolve()

    if not project_path.is_dir():
        print(f"Error: '{project_path}' is not a directory.")
        sys.exit(1)

    print(f'Brígh v{__version__} "{__codename__}"')
    print()

    started_at = time.perf_counter()

    # Step 1: Scan.
    print(f"Sniffing {project_path.name}/...")
    scan_data = scan_project(project_path)
    print(f"  Found {scan_data['total_files']} files across {len(scan_data['folders'])} directories.")

    # Step 2: Detect.
    print("  Detecting frameworks, tools, and patterns...")
    detections = detect_all(scan_data)

    # Quick summary of what we found.
    framework = detections.get("framework")
    languages = detections.get("languages", [])
    if framework:
        print(f"  Framework: {framework}")
    if languages:
        print(f"  Languages: {', '.join(languages)}")

    # Step 3: Generate.
    print("  Generating context files...")
    content = generate_context(detections)
    json_payload = generate_json_payload(detections)
    written = write_all(
        content,
        project_path,
        targets=args.targets,
        json_payload=json_payload,
    )

    elapsed_seconds = time.perf_counter() - started_at

    # Done.
    print()
    print(f"Done. Rubber ducked in {elapsed_seconds:.1f} seconds.")
    print()
    print("Generated:")
    for path in written:
        relative = path.relative_to(project_path)
        print(f"  {relative}")

    print()
    print("Your AI tools will pick these up automatically.")
    _print_gitignore_guidance(project_path, add_ignore=args.add_ignore)


def _print_gitignore_guidance(project_path: Path, add_ignore: bool) -> None:
    """Print .gitignore reminder and optionally append recommended entries."""
    print()
    print(
        "Reminder: If this project is public, add .brigh.md, CLAUDE.md, .cursorrules, "
        "AGENTS.md, .github/copilot-instructions.md, and .brigh.json to .gitignore."
    )

    gitignore_path = project_path / ".gitignore"
    if add_ignore:
        added = _ensure_gitignore_entries(gitignore_path, GITIGNORE_CONTEXT_ENTRIES)
        if added:
            print(f"Added to .gitignore: {', '.join(added)}")
        else:
            print(".gitignore already contains those entries.")
        return

    if gitignore_path.exists():
        print("Found .gitignore. Re-run with --add-ignore to add those entries automatically.")
    else:
        print("No .gitignore found. Re-run with --add-ignore to create one with those entries.")


def _ensure_gitignore_entries(gitignore_path: Path, entries: list[str]) -> list[str]:
    """Append missing entries to .gitignore and return which entries were added."""
    existing_lines: list[str] = []
    if gitignore_path.exists():
        existing_lines = gitignore_path.read_text(encoding="utf-8").splitlines()

    existing_set = set(existing_lines)
    to_add = [entry for entry in entries if entry not in existing_set]
    if not to_add:
        return []

    if gitignore_path.exists():
        current = gitignore_path.read_text(encoding="utf-8")
        prefix = "" if current.endswith("\n") or not current else "\n"
    else:
        prefix = ""
    new_content = prefix + "\n".join(to_add) + "\n"
    with gitignore_path.open("a", encoding="utf-8") as f:
        f.write(new_content)

    return to_add


if __name__ == "__main__":
    main()
