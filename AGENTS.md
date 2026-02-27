# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Telegram AI consulting bot built with **aiogram 3.25+** and **Python 3.12**. Single-process long-polling bot (no HTTP server). SQLite database auto-created at `data/bot.db` on startup.

### Required environment variables

| Variable | Required | Notes |
|---|---|---|
| `BOT_TOKEN` | Yes | Telegram Bot API token |
| `OPENAI_API_KEY` | Yes | OpenAI API key (GPT-4.1 / DALL-E 3) |
| `GEMINI_API_KEY` | Optional | Google Gemini for vision features |

Full list in `.env.example`. Copy to `.env` and fill in values.

### Running the bot

```bash
PYTHONPATH=/workspace python3 bot/main.py
```

The bot requires a valid `BOT_TOKEN` to reach the polling phase. Without it, the process exits with `BOT_TOKEN is not set!`. With an invalid token format, aiogram raises `TokenValidationError` after DB init.

### Linting

```bash
flake8 --max-line-length=120 bot/ utils/
```

The codebase has pre-existing style warnings (whitespace, unused imports). No autofix or strict lint gate exists.

### Compilation check

```bash
python3 -m compileall . -q
```

### Testing

No automated test suite exists. The project's testing checklist (from `.mcp/rules.md`) is:
1. `pip install -r requirements.txt`
2. `python3 -m compileall .`
3. `python3 bot/main.py` (smoke test — requires valid `BOT_TOKEN`)

### Caveats

- `Pillow` is used in `bot/ai/gemini_client.py` but **not listed in `requirements.txt`**. Install it separately: `pip install Pillow`.
- `PYTHONPATH` must include the workspace root for imports to resolve (the Dockerfile sets `PYTHONPATH=/app`).
- The `google-generativeai` package shows a deprecation warning; upstream recommends migrating to `google.genai`.
- `bot/handlers/selftest.py` references undefined names `TRIAL_MAX_MESSAGES` and `TRIAL_LIMIT_PER_DAY` (missing import from `utils.config`).
