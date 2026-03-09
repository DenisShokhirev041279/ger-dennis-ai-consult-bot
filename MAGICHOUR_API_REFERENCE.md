# MagicHour API — Справочник для агента

## Установка
```bash
pip install magic-hour
```

## Инициализация (AsyncClient — для aiogram)
```python
from magic_hour import AsyncClient

client = AsyncClient(token="MAGIC_HOUR_API_KEY")  # из .env
```

## Ключевые эндпоинты для бота

### 1. AI Image Generator (для Brand Audit / Product Photo)
```python
response = await client.v1.ai_image_generator.generate(
    style={"prompt": "Professional product photo of [item] on white background"},
    name="Product Photo",
    wait_for_completion=True,
    download_outputs=True,
    download_directory="./temp/"
)
# response.downloaded_paths содержит пути к файлам
```

### 2. Animation (фото → видео, ключевая WOW-фича)
```
POST https://api.magichour.ai/v1/animation
Authorization: Bearer <token>

{
  "name": "Animation video",
  "fps": 12,
  "end_seconds": 15,
  "height": 960,
  "width": 512,
  "style": {
    "art_style": "Painterly Illustration",  // или "Custom"
    "camera_effect": "Simple Zoom Out",
    "prompt_type": "custom",
    "prompt": "Description of desired animation",
    "transition_speed": 5
  },
  "assets": {
    "audio_source": "none",
    "image_file_path": "api-assets/id/1234.png"  // from upload API
  }
}
```

### 3. Face Swap Photo
```python
response = await client.v1.face_swap_photo.generate(
    assets={
        "face_swap_mode": "all-faces",
        "source_file_path": "/path/to/source.png",
        "target_file_path": "/path/to/target.png",
    },
    name="Face Swap",
    wait_for_completion=True,
    download_outputs=True,
)
```

### 4. Background Removal (альтернатива rembg)
MagicHour тоже умеет удалять фон — можно использовать вместо rembg API.

### 5. AI Voice Generator
Генерация голоса с голосами знаменитостей. Потенциал для озвучки видео.

## Паттерн работы: generate() vs create()
- `generate()` — high-level: создаёт, ждёт, скачивает. Блокирующий.
- `create()` — low-level: только стартует. Нужно самому polling статуса.

Для Telegram бота лучше `create()` + polling, чтобы не блокировать event loop:
```python
# 1. Создай проект
project = await client.v1.animation.create(...)

# 2. Покажи юзеру "⏳ Генерирую видео..."

# 3. Poll статус
import asyncio
while True:
    status = await client.v1.video_projects.get(id=project.id)
    if status.status in ("complete", "error", "canceled"):
        break
    await asyncio.sleep(3)

# 4. Скачай и отправь юзеру
if status.status == "complete":
    video_url = status.downloads[0].url
    # отправь через aiogram
```

## Стоимость (credits)
- У Denis 2000 кредитов
- AI Image: ~5 кредитов за картинку
- Animation: зависит от длины, ~20-50 кредитов за 15 сек видео
- Face Swap: ~10-20 кредитов

## Важно для агента:
1. СПРОСИ Denis API ключ перед интеграцией
2. Добавь MAGIC_HOUR_API_KEY в .env.example
3. Добавь `magic-hour` в requirements.txt
4. Используй AsyncClient (не sync Client)
5. Храни кредит-баланс в analytics — трекай расход
6. MagicHour features = PRO tier only (платные кредиты)
