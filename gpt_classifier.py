# gpt_classifier.py

import json
from openai import AsyncOpenAI
import asyncio

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

async def classify_url_async(url):
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": url}
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        if hasattr(e, "status_code") and e.status_code == 401:
            print("❌ API нейросетки сгорела, обратитесь к админу")
            return "❌ API нейросетки сгорела, обратитесь к админу"
        else:
            print(f"❌ Непредвиденная ошибка: {e}")
            return "❌ Ошибка нейросети"
