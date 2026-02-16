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
    
    # Load system prompt
    prompt_path = os.path.join("prompts", f"system_{lang}.md")
    if not os.path.exists(prompt_path):
        prompt_path = os.path.join("prompts", "system_en.md")
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    try:
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2048,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API Error: {e}")
        return "Temporary AI error. Please try again."
