from anthropic import AsyncAnthropic
from utils.config import ANTHROPIC_API_KEY
from utils.logger import logger
import os

if ANTHROPIC_API_KEY:
    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
else:
    client = None
    logger.warning("ANTHROPIC_API_KEY is not set. AI features will fail.")

async def get_claude_response(prompt: str, lang: str = "en") -> str:
    if not client:
        return "AI Authorization Error: API Key missing."
    
    # Load system prompt
    prompt_path = os.path.join("prompts", f"system_{lang}.md")
    if not os.path.exists(prompt_path):
        prompt_path = os.path.join("prompts", "system_en.md")
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    try:
        response = await client.messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest"),
            max_tokens=2048,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Claude API Error: {e}")
        return "Temporary AI error. Please try again."
