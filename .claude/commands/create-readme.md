---
name: create-readme
description: Generate or update README.md from current project structure and code
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

Generate or update `README.md` based on actual project content — no invented features.

## Steps

**Step 1** — Read existing README (if any):
```bash
cat README.md 2>/dev/null || echo "No README found"
```

**Step 2** — Gather project facts from code:
```bash
# Language and framework detection
cat package.json 2>/dev/null | head -20
cat pyproject.toml 2>/dev/null | head -30
cat requirements.txt 2>/dev/null | head -20
cat Dockerfile 2>/dev/null | head -10

# Entry points
find . -name "main.py" -o -name "app.py" -o -name "server.py" -o -name "index.ts" 2>/dev/null | head -5

# Test framework
ls tests/ 2>/dev/null || ls test/ 2>/dev/null || echo "No tests dir"

# Scripts
cat package.json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f'  {k}: {v}') for k,v in d.get('scripts',{}).items()]" 2>/dev/null || true
```

**Step 3** — Read key source files for accurate descriptions:
- Read `main.py` / `app.py` / `index.ts` for what the project does
- Read any config files to confirm actual setup steps

**Step 4** — Generate README structure:

```markdown
# [Project Name]

[One sentence — what this project does and who it's for]

## Prerequisites

- [Runtime/language + version]
- [Database/service if required]
- [Any other dependency]

## Setup

```bash
# 1. Clone and install
git clone [repo-url]
cd [project-dir]
[install command — pip install / npm install]

# 2. Configure environment
cp .env.example .env
# Edit .env with your values

# 3. Run database migrations (if applicable)
[migration command]

# 4. Start the application
[start command]
```

## Development

```bash
# Run tests
[test command]

# Run linting
[lint command]

# Run type checking
[type-check command]
```

## Project Structure

```
[show top-level structure with brief description of each directory]
```

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `ENV_VAR` | Yes | [what it does] |

## API / Usage

[Only include if there's an API — show actual endpoints from code, not invented ones]

## Contributing

1. Create a branch: `feature/[description]`
2. Make changes with tests
3. Run the full quality check: `[validation command]`
4. Open a pull request

## License

[License from package.json or LICENSE file]
```

**Step 5** — Write or update the file:
- If README exists and is substantial: use Edit to update specific sections
- If README is missing or minimal: Write the full generated version

## Rules

- Only describe features that exist in the code — verify before writing
- Include actual commands from package.json scripts / Makefile / setup files
- Do not invent API endpoints or configuration that isn't in the code
- If uncertain about a section: omit it rather than guess
- Keep setup instructions runnable — test each command mentally
- Link to `.claude/rules/` or ticket system only if they exist
