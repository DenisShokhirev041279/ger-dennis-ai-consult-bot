"""
GET /admin/metrics?token=<ADMIN_METRICS_TOKEN>

Возвращает JSON со снимком метрик бота для внешних ingestor'ов
(например, Genesis Content OS Module C). Read-only, не модифицирует БД.

Schema ответа:
{
  "total_users": int,
  "dau": int,        # unique user_id за последние 24h в analytics_events
  "wau": int,        # 7 дней
  "mau": int,        # 30 дней
  "messages_24h": int,  # суммарно сообщений за 24h
  "captured_at": "2026-05-24T19:00:00Z"
}

Защита: ADMIN_METRICS_TOKEN env var (требуется ?token=...). Без него — 401.
"""
import os
from datetime import datetime, timedelta, timezone

import aiosqlite
from aiohttp import web

from utils.config import DB_PATH


async def admin_metrics_handler(request: web.Request) -> web.Response:
    expected = os.getenv("ADMIN_METRICS_TOKEN", "")
    if not expected:
        return web.json_response({"error": "endpoint_disabled"}, status=503)

    provided = request.query.get("token", "")
    if provided != expected:
        return web.json_response({"error": "unauthorized"}, status=401)

    now = datetime.now(timezone.utc)
    cutoff_24h = (now - timedelta(hours=24)).isoformat()
    cutoff_7d = (now - timedelta(days=7)).isoformat()
    cutoff_30d = (now - timedelta(days=30)).isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        async def scalar(sql, params=()):
            async with db.execute(sql, params) as cur:
                row = await cur.fetchone()
                return (row[0] if row and row[0] is not None else 0)

        total_users = await scalar("SELECT COUNT(*) FROM users")
        dau = await scalar(
            "SELECT COUNT(DISTINCT user_id) FROM analytics_events WHERE created_at >= ?",
            (cutoff_24h,),
        )
        wau = await scalar(
            "SELECT COUNT(DISTINCT user_id) FROM analytics_events WHERE created_at >= ?",
            (cutoff_7d,),
        )
        mau = await scalar(
            "SELECT COUNT(DISTINCT user_id) FROM analytics_events WHERE created_at >= ?",
            (cutoff_30d,),
        )
        messages_24h = await scalar(
            "SELECT COUNT(*) FROM analytics_events WHERE created_at >= ?",
            (cutoff_24h,),
        )

    return web.json_response({
        "total_users": int(total_users),
        "dau": int(dau),
        "wau": int(wau),
        "mau": int(mau),
        "messages_24h": int(messages_24h),
        "captured_at": now.isoformat(),
    })
