# AGENTS.md

## Cursor Cloud specific instructions

### Overview
Single-process Python Telegram bot (aiogram 3.25+) for AI consulting sessions. Uses OpenAI GPT-4.1 for chat, Google Gemini + DALL-E 3 for reference photo merging, and embedded SQLite (`data/bot.db`, auto-created).

### Running the bot
```
PYTHONPATH=/workspace python bot/main.py
```
Requires `BOT_TOKEN` (Telegram) and `OPENAI_API_KEY` (OpenAI) environment variables. `GEMINI_API_KEY` is optional (only for reference photo feature). See `.env.example` for all variables.

### Checks / testing
- **Compile check**: `python -m compileall . -q` (no lint tools configured in the project)
- **Import validation**: `python -c "import aiogram; import openai; import aiosqlite; import dotenv; import google.generativeai"`
- **Smoke test**: run `python bot/main.py` — exits with `BOT_TOKEN is not set!` if no token is configured; that confirms the full import chain works

### Non-obvious notes
- `PYTHONPATH` must include the workspace root (`/workspace`) because `utils/` and `bot/` are plain packages without `__init__.py` at the repo root level.
- The `consult` router must be registered last in the dispatcher (it's a catch-all handler).
- SQLite DB file is created automatically at `data/bot.db` on first run — no migrations needed.
- The `google.generativeai` package emits a `FutureWarning` about deprecation; this is cosmetic and does not affect functionality.
- No automated test suite exists; the project's testing checklist (in `.mcp/rules.md`) relies on `compileall` and manual smoke testing.
