# Koyeb Deployment Guide

## Environment Variables (Required)

Set these in Koyeb dashboard under Service Settings → Environment:

```
BOT_TOKEN=<your_telegram_bot_token>
OPENAI_API_KEY=<your_openai_api_key>
GEMINI_API_KEY=<your_gemini_api_key>  # Optional, for Reference Photo feature
ADMIN_IDS=123456789,987654321  # Comma-separated Telegram user IDs
```

## Payment Configuration (Optional)

Configure at least one payment method:

```
PAYMENT_IBAN=<your_iban>
PAYMENT_WISE=<your_wise_email_or_tag>
PAYMENT_USDT_ADDRESS=<your_trc20_usdt_address>
PAYMENT_TON_ADDRESS=<your_ton_wallet_address>
```

**Important**: Payment methods without configured requisites will be automatically hidden from users.

## Trial & Session Settings (Optional)

```
TRIAL_LIMIT_PER_DAY=1           # Free trial attempts per day
TRIAL_MAX_MESSAGES=3            # Message limit during trial
SESSION_DEFAULT_MINUTES=30      # Default session duration
OPENAI_MODEL=gpt-4.1            # OpenAI model (fallback: gpt-4o-mini)
```

## Deploy Steps

1. **Push to GitHub**: Ensure your repository is up to date
   ```bash
   git push origin main
   ```

2. **Create Koyeb Service**:
   - Go to [Koyeb Dashboard](https://app.koyeb.com/)
   - Create App → Create Service → GitHub
   - Select repository: `ger-dennis-ai-consult-bot`
   - Builder: Dockerfile (auto-detected)

3. **Configure Environment Variables**: Copy all required values from above

4. **Deploy**: Click Deploy. The bot runs in polling mode (no ports needed).

## Verifying Deployment

Use `/selftest` command (admin only) to verify:
- BOT_TOKEN & API keys status
- Payment methods configured
- Active sessions count
- Trial usage stats

## Security Notes

- `.env` file is gitignored - never commit secrets
- Admin approval required for all manual payments (IBAN/Crypto)
- Telegram Stars payments process automatically after successful Telegram payment event
