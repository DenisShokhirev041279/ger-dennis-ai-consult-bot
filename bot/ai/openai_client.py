from openai import AsyncOpenAI
from utils.logger import logger
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if OPENAI_API_KEY:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
else:
    client = None
    logger.warning("OPENAI_API_KEY is not set. AI features will fail.")

async def get_ai_response(prompt: str = None, lang: str = "en", mode: str = "paid", messages: list = None) -> str:
    if not client:
        return "AI Authorization Error: API Key missing."
    
    # Token limits
    if mode == "paid":
        max_tokens = 2048
    elif mode == "trial_short":
        max_tokens = 150 # Shorter response
    else:
        max_tokens = 600
    
    # Normalize language code
    lang = lang.split("-")[0].lower() if lang else "en"
    if lang not in ["ru", "en", "de"]:
        lang = "en"
    
    # Load system prompt
    prompt_path = os.path.join("prompts", f"system_{lang}.md")
    if not os.path.exists(prompt_path):
        prompt_path = os.path.join("prompts", "system_en.md")
    
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        system_prompt = "You are a helpful assistant."

    # Prepare messages
    if messages:
        # If user passed full messages, use it but insert system prompt if missing
        full_messages = messages
        if not any(m["role"] == "system" for m in full_messages):
            full_messages.insert(0, {"role": "system", "content": system_prompt})
    else:
        # Legacy/Simple call
        full_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

    try:
        model = os.getenv("OPENAI_MODEL", "gpt-4.1")
        response = await client.chat.completions.create(
            model=model,
            messages=full_messages,
            max_tokens=max_tokens,
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
                messages=full_messages,
                max_tokens=max_tokens,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as fallback_error:
            logger.exception("OpenAI fallback model also failed")
            return "Temporary AI error. Please try again."
