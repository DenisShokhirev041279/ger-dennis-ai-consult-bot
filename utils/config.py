import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Admin IDs (comma-separated)
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", os.getenv("ADMIN_ID", "0"))
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_STR.split(",") if x.strip().isdigit()]

# Payment requisites
IBAN = os.getenv("PAYMENT_IBAN", "")
WISE_DETAILS = os.getenv("PAYMENT_WISE", "")
USDT_WALLET = os.getenv("PAYMENT_USDT_ADDRESS", "")
TON_WALLET = os.getenv("PAYMENT_TON_ADDRESS", "")

# Trial limits
TRIAL_LIMIT_PER_DAY = int(os.getenv("TRIAL_LIMIT_PER_DAY", "1"))
TRIAL_MAX_MESSAGES = int(os.getenv("TRIAL_MAX_MESSAGES", "3"))
SESSION_DEFAULT_MINUTES = int(os.getenv("SESSION_DEFAULT_MINUTES", "30"))
