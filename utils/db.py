import aiosqlite
import os
import time
from utils.logger import logger

DB_PATH = os.path.join("data", "bot.db")

async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language_code TEXT DEFAULT 'en',
                username TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                user_id INTEGER PRIMARY KEY,
                start_time INTEGER,
                duration_minutes INTEGER,
                is_active BOOLEAN DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payment_claims (
                claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                package_key TEXT,
                payment_method TEXT,
                status TEXT DEFAULT 'pending',
                created_at INTEGER,
                ref TEXT,
                amount_text TEXT,
                chat_id INTEGER,
                approved_by INTEGER,
                approved_at INTEGER,
                admin_note TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS trial_usage (
                user_id INTEGER,
                date TEXT,
                message_count INTEGER DEFAULT 0,
                photo_count INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, date)
            )
        """)
        await db.commit()
    logger.info("Database initialized.")

async def set_user_lang(user_id, lang_code, username=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, language_code, username) 
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET 
                language_code=excluded.language_code,
                username=COALESCE(excluded.username, users.username)
        """, (user_id, lang_code, username))
        await db.commit()

async def get_user_lang(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT language_code FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else "en"

async def activate_session(user_id, duration_minutes):
    start_time = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO sessions (user_id, start_time, duration_minutes, is_active)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                start_time=excluded.start_time,
                duration_minutes=excluded.duration_minutes,
                is_active=1
        """, (user_id, start_time, duration_minutes))
        await db.commit()

async def get_session_info(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT start_time, duration_minutes, is_active FROM sessions WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def end_session(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE sessions SET is_active = 0 WHERE user_id = ?", (user_id,))
        await db.commit()
