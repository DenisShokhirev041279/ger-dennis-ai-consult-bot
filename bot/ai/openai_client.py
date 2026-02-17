from openai import AsyncOpenAI
from utils.logger import logger
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if OPENAI_API_KEY:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
else:
    client = None
    logger.warning("OPENAI_API_KEY is not set. AI features will fail.")

async def get_ai_response(prompt: str, lang: str = "en") -> str:
    if not client:
        return "AI Authorization Error: API Key missing."
    
    # Normalize language code (ru-RU → ru, en-US → en, etc.)
    lang = lang.split("-")[0].lower() if lang else "en"
    if lang not in ["ru", "en", "de"]:
        lang = "en"
    
    # Load system prompt
    prompt_path = os.path.join("bot", "prompts", f"system_{lang}.txt")
    if not os.path.exists(prompt_path):
        prompt_path = os.path.join("bot", "prompts", "system_en.txt")
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    try:
        model = os.getenv("OPENAI_MODEL", "gpt-4.1")
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2048,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.exception(f"OpenAI API Error with model {os.getenv('OPENAI_MODEL', 'gpt-4.1')}")
        
        # Fallback to gpt-4o-mini
        fallback_model = "gpt-4o-mini"
        try:
            logger.info(f"Trying fallback model: {fallback_model}")
            response = await client.chat.completions.create(
                model=fallback_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2048,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as fallback_error:
            logger.exception("OpenAI fallback model also failed")
            return "Temporary AI error. Please try again."
