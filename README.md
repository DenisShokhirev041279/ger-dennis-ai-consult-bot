# Ger Dennis AI Consult Bot

## 🚀 1-Click Run (Locally)
1.  **Open in VS Code**.
2.  **Fill `.env`**: Add your keys (do NOT commit this file).
3.  **Run**: Go to "Run and Debug" tab -> Click Play (Run Bot).
    *   *Dependencies will install automatically via tasks.json if configured, else run `pip install -r requirements.txt` manually first.*

## ☁️ Deployment (Koyeb)
See [koyeb.md](koyeb.md) for 1-click deployment steps.

## 🔐 Security Features
- **Prompt Injection Guard**: Heuristics block malicious ignores/overrides.
- **Hardened Rules**: System prompts strictly forbid unmasking secrets or admin roleplay.
- **Secrets Management**: `.env` driven. No hardcoded keys.

## 💰 Subscriptions & Monetization
- **Starter (1990 Stars/mo)**: 30 daily requests.
- **Pro (5990 Stars/mo)**: Unlimited AI, CV Tools (MagicHour).
- **Business (14990 Stars/mo)**: All above + custom prompt logic.
- **Referrals**: Users can invite friends via deep links (`/start ref_ID`) to earn bonus messages.
- Payments handled natively via Telegram Stars XTR invoices or External logic.

## ⚖️ Progressive Trial System
- **Free Users**: Get 5 full messages, 5 shortened messages, then an upsell screen. Bonus credits can extend this.
- non-subscribers have an AI watermark appended.

## 🧩 Reference Photo / CV Tools
- Support for Image/Video generation and background removal via MagicHour & Gemini Vision.
- Accessed via the "AI Tools" menu (Requires Pro/Business).

## ☁️ Deployment & Webhook
- Operates on `aiohttp` webhooks on port 8080.
- Check `/health` endpoint for Koyeb/Docker liveness probes.
- Requires `WEBHOOK_URL` in `.env`.
