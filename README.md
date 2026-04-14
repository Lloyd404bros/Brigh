# Brígh

**Pronounced "bree"** — from the Irish Gaelic *brígh*, meaning *essence, meaning, pith*.

> Your AI tools should already know your codebase.

Brígh scans your project and generates context files that AI coding tools actually understand. No more writing `CLAUDE.md` by hand. No more explaining your own architecture to a machine. One command. Done.

Current implementation status lives in [STATUS.md](STATUS.md).

---

## The Problem

Every AI coding tool — Claude Code, Cursor, GitHub Copilot — needs to understand your project to give useful help. Right now, developers either:

- Write context files manually (tedious, goes stale in a week)
- Don't bother (and get suggestions for Firebase when they use Supabase)
- Paste the same explanation into every new chat

Vibe coders have it worse. If you built your app with AI, you might not even know your own codebase well enough to describe it. So your AI tools are flying blind, and you can't fix it.

## The Solution

```bash
pip install brigh
```

```bash
brigh scan
```

That's it. Brígh reads your project — files, configs, folder structure, dependencies, patterns — and generates a clear, accurate context file that any AI tool can use.

## How It Works

```bash
brigh scan
```

Free. Local. Offline. No accounts, no API keys, no internet required. Brígh scans your repo and generates context from what it finds. Works everywhere, costs nothing.

### Privacy by Default

Brígh does not send your code, metadata, or scan results to any server in this phase. Everything runs locally and writes files into your repository only.

### BrighAI — Coming Soon

A paid service that adds an AI layer on top of the scan. Instead of a list of dependencies, you get intelligent, natural-language context like: "This project uses Supabase auth with row-level security, a React frontend with custom hooks, and Tailwind for styling." No API keys to manage — just log in and go.

## Output

Brígh generates a `.brigh.md` file as the single source of truth, plus ready-to-use files for:

- `CLAUDE.md` — for Claude Code
- `AGENTS.md` — for agent-based coding workflows
- `.cursorrules` — for Cursor
- `copilot-instructions.md` — for GitHub Copilot
- `.brigh.json` — machine-readable output for scripts and integrations (optional target)

One scan. Every tool. Always in sync.

## What It Detects

- **Frameworks & languages** — React, Vue, Next.js, Django, Flask, Express, and more
- **Package managers & dependencies** — what you actually use, not what you don't
- **Project structure** — how your folders are organised, where things live
- **Patterns & conventions** — functional vs class components, hook patterns, file naming
- **Infrastructure** — Supabase, Firebase, Docker, CI/CD configs
- **Auth & data flow** — how your app handles users, data, and state
- **Style & formatting** — Tailwind, CSS modules, linting rules, formatting preferences

## Quick Start

```bash
# Install
pip install brigh

# Navigate to your project
cd your-project

# Generate context files
brigh scan

# Specify output formats
brigh scan --targets claude agents cursor copilot

# Generate machine-readable JSON output
brigh scan --targets json

# Add generated context files to .gitignore automatically
brigh scan --add-ignore
```

## Example Output

After running `brigh scan` in a React project:

```markdown
# Project Context

## Stack
- React 18 with TypeScript
- Vite build tooling
- Supabase (auth + database + storage)
- Tailwind CSS
- React Router v6

## Architecture
- Functional components with custom hooks
- Feature-based folder structure: src/features/{feature}/
- Shared components in src/components/
- Supabase client initialised in src/lib/supabase.ts

## Conventions
- Named exports preferred over default exports
- Custom hooks prefixed with "use" in dedicated hooks/ directories
- Environment variables prefixed with VITE_
- Absolute imports via @ alias

## Auth
- Supabase Auth with email/password
- Row-level security enabled
- Auth state managed via useAuth() custom hook

## Testing
- No test framework currently configured
```

## Who This Is For

- **Vibe coders** who built with AI and need AI to keep understanding what it built
- **Solo developers** who are sick of writing context files by hand
- **Teams** who want consistent AI assistance across the whole codebase
- **Anyone** who switches between AI tools and wants them all on the same page

## Contributing

Brígh is open source and contributions are welcome. Fork the repo, make your changes, and submit a pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas where contributions are especially valued:
- Support for additional languages and frameworks
- Smarter pattern detection
- Output format plugins for new AI tools

## Roadmap

### Phase 1 — Now

- [x] Core scanning engine
- [x] CLI interface
- [x] CLAUDE.md generation
- [x] AGENTS.md generation
- [x] .cursorrules generation
- [x] copilot-instructions.md generation

### Phase 2 — Next

- [ ] BrighAI smart context mode
- [ ] Watch mode for automatic regeneration
- [ ] Pre-commit hook integration

### Phase 3 — Future

- [ ] VS Code extension
- [ ] Support for Python, Go, Rust, Java projects
- [ ] Team configuration sharing
- [ ] Context drift detection

## Etymology

Brígh (pronounced "bree") is an Irish Gaelic word meaning *essence*, *meaning*, or *pith* — the core substance of something. It felt right for a tool that distils the essence of your codebase into something an AI can understand.

Built by [404Bros LTD](https://github.com/404bros).

## Licence

MIT — Copyright 2026 404Bros LTD. See [LICENSE](LICENSE) for details.
