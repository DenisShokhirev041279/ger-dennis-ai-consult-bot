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

## 💰 Payments
- **Telegram Stars**: Native XTR invoices.
- **External**: Fiat/Crypto instructions with Admin Approval workflow.

## 🧩 Reference Photo (Gemini Vision)
- **Usage**: Send 2-14 photos via "🧩 Reference Photo" menu to get a merged concept.
- **Tech**: Uses Gemini to analyze and DALL-E 3 to generate.
- **Limits**: Trial users limited by `TRIAL_LIMIT_PER_DAY`.

## ⚖️ Trial System
- **Free Users**: Limited to `TRIAL_MAX_MESSAGES` per day.
- **Paid Users**: Unlimited access for session duration.
- **Hard Stop**: After limit, user must buy a package.
