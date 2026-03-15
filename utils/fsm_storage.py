import json
import aiosqlite
from typing import Any, Dict, Optional, Tuple
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType

class SQLiteStorage(BaseStorage):
    def __init__(self, db_path: str = "data/bot.db"):
        self.db_path = db_path

    async def _init_table(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS fsm_storage ("
                "key TEXT PRIMARY KEY, "
                "state TEXT, "
                "data TEXT)"
            )
            await db.commit()

    def _get_key(self, key: StorageKey) -> str:
        return f"{key.bot_id}:{key.chat_id}:{key.user_id}"

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        await self._init_table()
        s_key = self._get_key(key)
        state_str = state.state if hasattr(state, "state") else str(state) if state else None
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO fsm_storage (key, state, data) VALUES (?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET state = excluded.state",
                (s_key, state_str, "{}")
            )
            await db.commit()

    async def get_state(self, key: StorageKey) -> Optional[str]:
        await self._init_table()
        s_key = self._get_key(key)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT state FROM fsm_storage WHERE key = ?", (s_key,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        await self._init_table()
        s_key = self._get_key(key)
        data_json = json.dumps(data)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO fsm_storage (key, state, data) VALUES (?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET data = excluded.data",
                (s_key, None, data_json)
            )
            await db.commit()

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        await self._init_table()
        s_key = self._get_key(key)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT data FROM fsm_storage WHERE key = ?", (s_key,)) as cursor:
                row = await cursor.fetchone()
                return json.loads(row[0]) if row and row[0] else {}

    async def close(self) -> None:
        pass
