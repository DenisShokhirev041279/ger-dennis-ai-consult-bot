# TODO & Checklist — Ger Dennis AI Consult Bot

## ✅ БЛОК 1 — Критичные фиксы (СДЕЛАНО)
- [x] Удалить промо-ссылки автора из AI ответов (платные получают чистый ответ)
- [x] Исправить импорты в `consult.py` — `get_trial_usage_today`, `increment_trial_messages`
- [x] Admin полный bypass — rate limit, trial, subscription, watermark
- [x] Реферал: бонус только после оплаты реферала (+3 сообщения), уведомление рефереру
- [x] `TRIAL_MAX_MESSAGES = 10` — единое число везде из config (убран hardcode)
- [x] Koyeb Volume `/app/data` — база данных сохраняется между рестартами

## ✅ БЛОК 1б — UX Reference Photo (СДЕЛАНО)
- [x] Кнопки ✅ Готово / ❌ Отмена вместо скрытых команд `/done` `/cancel`
- [x] Счётчик фото после каждой загрузки
- [x] Мультиязычные сообщения (RU/EN/DE)
- [x] Temp файлы в `data/temp_photos/` (persistent volume)
- [x] Исправлена проверка подписки (check_subscription вместо get_session_info)
- [x] Автовозврат в меню после завершения/отмены

## ✅ БЛОК 2 — Аналитика и статус (СДЕЛАНО)
- [x] `/stats` (только admin) — пользователи, подписки по планам, сообщения, рефералы, ожидают оплаты
- [x] `/mystatus` (все пользователи) — статус подписки / остаток trial сообщений
- [x] Help кнопка — показывает доступные команды

---

## ✅ БЛОК 3 — Докрутка после запуска (СДЕЛАНО)

### Пользовательский опыт
- [x] Показывать дату истечения подписки в `/mystatus` (DD.MM.YYYY)
- [x] Trial progress bar в `/mystatus` (▓░ used/total + бонусы)
- [x] Upsell мультиязычный (RU/EN/DE) при исчерпании trial
- [x] Мультиязычные rate-limit и прочие ошибки в `consult.py`

### Технические
- [x] Таймаут 180 сек для MagicHour + `asyncio.wait_for`
- [x] `cv_tools.py`: перехват `TimeoutError`, мультиязычное сообщение пользователю
- [x] `/testpay` ограничен только для ADMIN_IDS
- [x] `has_user()` helper в `utils/db.py`
- [x] `expires_at` возвращается из `check_subscription()`

### Остаток (перенесено в Блок 4)
- [ ] Индексы в БД: `payment_claims(user_id, status)`, `subscriptions(user_id, status)`
- [ ] `google.generativeai` → `google.genai` (deprecated пакет, FutureWarning)
- [ ] Python 3.10 → 3.11 в Dockerfile
- [ ] Trial: считать суммарно (не сбрасывать каждый день)
- [ ] Timezone UTC везде
- [ ] Admin approval кнопки: защита от двойного нажатия (race condition)

---

## 📋 ПЕРЕД ПОКАЗОМ ПАРТНЁРУ ПО ОПЛАТЕ

- [x] Бот деплоится автоматически из GitHub → Koyeb
- [x] Volume подключён, данные не теряются
- [x] Admin не платит, обходит все проверки
- [x] Trial 10 сообщений бесплатно
- [x] Реферальная программа работает корректно
- [ ] Убедиться что PAYMENT_IBAN / PAYMENT_WISE / PAYMENT_USDT_ADDRESS заполнены в Koyeb env
- [ ] Протестировать полный flow оплаты вручную
- [ ] Проверить что webhook URL настроен (или polling работает стабильно)

---

## ✅ БЛОК 4 — Производительность и полировка (СДЕЛАНО)

- [x] Trial: суммарный счётчик на все дни — `get_trial_usage_total()`, больше не сбрасывается
- [x] Индексы в БД: `subscriptions`, `payment_claims`, `trial_usage`, `referrals`
- [x] Реферальный дашборд: статистика (приглашено / оплатили / заработано / осталось)
- [x] `google.generativeai` → `google.genai` — async client, без FutureWarning
- [x] Python 3.10 → 3.11 в Dockerfile
- [x] `requirements.txt`: `google-genai>=1.0.0`

### Остаток (Блок 5)
- [ ] Upgrade плана без ожидания истечения
- [ ] Timezone UTC везде
- [ ] Admin approval кнопки: защита от двойного нажатия (race condition)

---

## 💡 ИДЕИ ДЛЯ БУДУЩЕГО (Блок 5+)

- [ ] Telegram WebApp для красивого UI подписок
- [ ] Email-рассылка при истечении подписки
- [ ] A/B тест текстов upsell
- [ ] Интеграция с реальной платёжной системой (Stripe/Paddle)
- [ ] Голосовые сообщения → транскрипция (Whisper)
- [ ] Расписание консультаций через Calendly или встроенный календарь
