# gpt_classifier.py

import json
from openai import AsyncOpenAI

with open("config.json", "r") as f:
    config = json.load(f)

client = AsyncOpenAI(api_key=config["openai_key"])

SYSTEM_PROMPT = """
Ты — помощник, который классифицирует сайты по их адресу.
Категории:
🟢 Реальные сайты — сайты с уникальным контентом или услугами, сайт компании или сервиса.
🟡 Каталоги и агрегаторы — сайты с подборками, списками, справочники, маркетплейсы.
🔴 Шум/мусор/нерелевантное — пустые страницы, сайты с ошибками, реклама, нерелевантные результаты.
Возвращай только Реальные сайты, другие игнорируй и не выдавай.
"""

gpt_cache = {}

async def classify_url_async(url: str) -> str:
    if url in gpt_cache:
        return gpt_cache[url]

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"К какой категории относится сайт: {url}?"}
            ],
            temperature=0.2
        )
        result = response.choices[0].message.content.strip()
        gpt_cache[url] = result
        return result
    except Exception as e:
        print(f"GPT ошибка: {e}")
        return "⚠️ Ошибка"
