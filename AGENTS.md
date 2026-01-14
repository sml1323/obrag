# Repository Guidelines

## Project Structure & Module Organization
- `src/`: Python prototypes and implementation stubs (current code lives here).
- `reference/`: Research notebooks and supporting notes (`*.ipynb`, `reference.md`).
- `plan.md` and `prd.md`: Product planning and requirements; keep these in sync with major changes.

## Build, Test, and Development Commands
- No formal build/test scripts are defined yet.
- If you need to review notebooks locally: `jupyter lab reference`.
- When adding runnable code, document the exact command here (for example, a CLI entry point under `src/`).

## Coding Style & Naming Conventions
- Python: 4-space indentation, use type hints where practical, `snake_case` for functions/variables, `PascalCase` for classes.
- Markdown: concise headings and bullet lists; keep docs focused and scannable.
- Filenames: prefer lowercase with underscores (e.g., `study_plan.md`).

## Testing Guidelines
- No automated tests are present.
- If you introduce tests, place them in `tests/` and use a clear naming pattern like `test_*.py`.
- Document the chosen test runner and commands in this section once added.

## Commit & Pull Request Guidelines
- Existing commits show short subjects with optional prefixes (e.g., `feat:`) and simple `init` messages.
- Keep commit messages concise, present tense, and scoped to a single change.
- PRs should include: a brief summary, linked issue or plan item when applicable, and UI screenshots for any dashboard work.
- Update `plan.md`/`prd.md` when behavior or scope changes.

## Security & Configuration Tips
- Store API keys in environment variables; do not commit secrets.
- If you add local config (e.g., `.env`), ensure it is gitignored.
