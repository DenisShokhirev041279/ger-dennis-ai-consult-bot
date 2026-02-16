# Koyeb Deployment Guide

## Deploy Steps

1. **Push to GitHub**: Ensure repo is pushed with latest changes.

2. **Create Koyeb Service**:
   - Go to [Koyeb Dashboard](https://app.koyeb.com/)
   - Create App → Create Service → GitHub
   - Select repository: `ger-dennis-ai-consult-bot`
   - Builder: Dockerfile (auto-detected)

3. **Environment Variables** (Required):
   - `BOT_TOKEN`: Your Telegram Bot Token
   - `OPENAI_API_KEY`: Your OpenAI API Key
   - `ADMIN_ID`: Your Telegram User ID
   - `OPENAI_MODEL`: `gpt-4.1` (optional, has default)
   - `IBAN`: Your IBAN (optional, for fiat payments)
   - `WISE_DETAILS`: Your Wise email/tag (optional)
   - `USDT_WALLET`: Your TRC20 address (optional)
   - `TON_WALLET`: Your TON address (optional)

4. **Deploy**: Click Deploy. Bot runs in polling mode, no ports needed.
