import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

IBAN = os.getenv("IBAN", "")
WISE_DETAILS = os.getenv("WISE_DETAILS", "")
USDT_WALLET = os.getenv("USDT_WALLET", "")
TON_WALLET = os.getenv("TON_WALLET", "")
