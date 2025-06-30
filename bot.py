# bot.py

import telebot
from telebot import types
import json
import asyncio

BOT_TOKEN = "8053288183:AAGwAyf0qvh_ArlPtQOJ_9H1zVa89Wf6o9Q"
bot = telebot.TeleBot(BOT_TOKEN)

admin_state = {}

@bot.message_handler(commands=["start"])
def handle_start(message):
    bot.reply_to(message, "🔍 Введите поисковый запрос (например: фитнес клубы Москва):")
    bot.register_next_step_handler(message, lambda msg: asyncio.run(process_query(msg)))

async def process_query(message):
    from main import yandex_api, is_real_site, is_city_in_domain
    from gpt_classifier import classify_url_async
    from google_checker import load_domains_from_sheet, get_main_domain

    query = message.text.strip()
    city_name = query.split()[-1].lower()
    msg = bot.send_message(message.chat.id, "🔍 Начинаю поиск...")

    try:
        donor_domains = load_domains_from_sheet()
    except:
        donor_domains = set()

    urls = yandex_api(query)
    total = len(urls)

    result_links = []
    found_in_sheet = set()

    filtered_urls = [
        url for url in urls
        if is_real_site(url)
        and get_main_domain(url) not in donor_domains
        and not is_city_in_domain(url, city_name)
    ]

    steps = 5
    urls_per_step = max(1, len(filtered_urls) // steps)
    current_step = 0

    results = await asyncio.gather(*(classify_url_async(url) for url in filtered_urls))

    for idx, (url, category) in enumerate(zip(filtered_urls, results)):
        if "🟢" in category:
            domain = get_main_domain(url)
            if domain not in donor_domains:
                result_links.append(url)
            else:
                found_in_sheet.add(domain)

        if (idx + 1) % urls_per_step == 0 or idx == len(filtered_urls) - 1:
            current_step = min(steps, current_step + 1)
            progress_bar = "🟩" * current_step + "⬜" * (steps - current_step)
            percent = int((idx + 1) / len(filtered_urls) * 100)
            try:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=msg.message_id,
                    text=f"{progress_bar} Обработка {percent}%..."
                )
            except:
                pass

    if result_links:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text=f"✅ Найдено {len(result_links)} новых сайтов:\n\n" + "\n".join(result_links)
        )
    else:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text="😐 Новых сайтов не найдено."
        )

    msg2 = bot.send_message(message.chat.id, "\n🔍 Введите новый поисковый запрос:")
    bot.register_next_step_handler(msg2, lambda msg: asyncio.run(process_query(msg)))

@bot.message_handler(commands=["admin"])
def handle_admin(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("API_KEY", "FOLDER_ID", "api_key")
    bot.send_message(message.chat.id, "🔧 Выберите параметр для изменения:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["API_KEY", "FOLDER_ID", "api_key"])
def handle_config_key_choice(message):
    admin_state[message.chat.id] = message.text
    bot.send_message(message.chat.id, f"✏️ Введите новое значение для {message.text}:")

@bot.message_handler(func=lambda m: m.chat.id in admin_state)
def handle_config_value(message):
    key = admin_state.pop(message.chat.id)
    value = message.text.strip()

    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        config[key] = value

        if key == "API_KEY" and not value.startswith("AQV"):
            raise ValueError("Неверный API ключ")
        if key == "openai_key" and not value.startswith("sk-"):
            raise ValueError("Неверный ключ OpenAI")

        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)

        bot.reply_to(message, f"✅ Значение {key} успешно обновлено.")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}\nПопробуйте снова.")
        admin_state[message.chat.id] = key

bot.polling()
