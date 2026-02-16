# Project Rules: ger-dennis-ai-consult-bot

## Security (non-negotiable)
- NEVER hardcode BOT_TOKEN, ANTHROPIC_API_KEY, ADMIN_ID, wallets, IBAN, Wise details.
- Secrets only via environment variables. Provide .env.example only.
- Add .env and secrets to .gitignore.
- Do not print secrets in logs.

## Payments
- Telegram Stars (XTR) is the ONLY built-in Telegram payment.
- EUR/USD and Crypto are EXTERNAL flows only: show instructions + "I paid" button + manual admin approve.
- No Stripe. No provider_token for cards.

## UX / Flow
- /start => language inline buttons ONLY. No extra text before lang choice.
- Persist language in FSM + SQLite.
- After payment success: unlock consult, start timer, enforce end.
- No freeform AI consult before payment.

## Code quality
- aiogram 3.25+ only.
- One responsibility per module: handlers, payments, ai, utils.
- Use type hints. Keep functions small.
- Logging: concise, no sensitive data.

## Testing checklist (must run locally)
- pip install -r requirements.txt
- python -m compileall .
- python bot/main.py (smoke)
- Stars invoice flow (mock/stub if needed)
- External approve flow end-to-end (admin approve -> unlock)

## Output requirements
- Generate ALL files, ready to copy-paste.
- README includes Windows setup steps and Railway deploy steps.
- Use PowerShell commands in README.
