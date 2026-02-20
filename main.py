import telebot
from telebot import types

TOKEN = "8519990554:AAHHDWdCTl6lAVYwCqkQ_4WT1mDOomax3a0"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

IMAGE_PATH = "image.png"

# ---- ФЕЙК БАЗА ----
users = {}
withdraw_requests = []  # для хранения заявок на вывод

# Один TikTok канал
TIKTOK_CHANNEL = "https://www.tiktok.com/@stardast_bot"

REWARD = 1000 # награда за задание

# ---- USER ----
def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "stars": 0,
            "task_done": False
        }
    return users[user_id]

# ---- START ----
@bot.message_handler(commands=["start"])
def start(message):
    get_user(message.from_user.id)

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📋 Задание", "⭐ Баланс")
    kb.add("💸 Вывод")

    with open(IMAGE_PATH, "rb") as photo:
        bot.send_photo(
            message.chat.id,
            photo,
            caption=(
                "<b>⭐ TELEGRAM STARS BOT ⭐</b>\n\n"
                "<b>Зарабатывай звёзды за подписки✨</b>\n\n"
                "<b>Приводи друзей и получай ещё больше звёзд!</b>\n\n"
                "<i>Выбери действие в меню ниже 👇</i>"
            ),
            reply_markup=kb
        )

# ---- БАЛАНС ----
@bot.message_handler(func=lambda m: m.text == "⭐ Баланс")
def balance(message):
    user = get_user(message.from_user.id)

    bot.send_message(
        message.chat.id,
        (
            "<b>💰 Твой баланс:</b>\n\n"
            f"⭐ <b>{user['stars']} звёзд</b>"
        )
    )

# ---- ЗАДАНИЕ ----
@bot.message_handler(func=lambda m: m.text == "📋 Задание")
def task(message):
    user = get_user(message.from_user.id)

    if user["task_done"]:
        bot.send_message(
            message.chat.id,
            "<b>✅ Задание уже выполнено</b>\n\n<i>Ожидай новые задания</i>"
        )
        return

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            "🔗 TikTok канал",
            url=TIKTOK_CHANNEL
        )
    )
    kb.add(
        types.InlineKeyboardButton(
            "✅ Проверить задание",
            callback_data="check_task"
        )
    )

    text = (
        "<b>📌 Задание:</b>\n\n"
        "Подпишись на <b>наш TikTok канал</b> 👇\n\n"
        f"🎁 Награда: <b>⭐ {REWARD}</b>\n\n"
        "<i>После подписки нажми «Проверить задание»</i>"
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=kb
    )

# ---- ПРОВЕРКА (ФЕЙК) ----
@bot.callback_query_handler(func=lambda call: call.data == "check_task")
def check_task(call):
    user = get_user(call.from_user.id)

    if user["task_done"]:
        bot.answer_callback_query(call.id, "Задание уже выполнено")
        return

    user["task_done"] = True
    user["stars"] += REWARD

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=(
            "<b>✅ Задание выполнено!</b>\n\n"
            f"➕ <b>{REWARD} ⭐ начислено</b>\n"
            f"💰 Баланс: <b>{user['stars']} ⭐</b>"
        )
    )

    bot.answer_callback_query(call.id, "⭐ Звёзды начислены")

# ---- ВЫВОД ----
@bot.message_handler(func=lambda m: m.text == "💸 Вывод")
def withdraw(message):
    user = get_user(message.from_user.id)

    if user["stars"] <= 0:
        bot.send_message(message.chat.id, "❌ У тебя нет звёзд для вывода")
        return

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            "🚀 Вывести звёзды",
            callback_data="withdraw_request"
        )
    )

    bot.send_message(
        message.chat.id,
        (
            "<b>💸 Вывод Telegram Stars</b>\n\n"
            f"⭐ Доступно: <b>{user['stars']} звёзд</b>\n\n"
            "⏳ <i>Заявки обрабатываются автоматически</i>\n"
            "📨 <i>Уведомление придёт в этом чате</i>"
        ),
        reply_markup=kb
    )

# ---- CALLBACK ВЫВОД ----
@bot.callback_query_handler(func=lambda call: call.data == "withdraw_request")
def withdraw_request(call):
    user = get_user(call.from_user.id)

    if user["stars"] <= 0:
        bot.answer_callback_query(call.id, "❌ Недостаточно звёзд")
        return

    # Просим пользователя указать TikTok username
    msg = bot.send_message(
        call.message.chat.id,
        "📌 <b>Укажи Telegram username для вывода звёзд (например, @username)</b>", parse_mode="HTML"
    )
    bot.register_next_step_handler(msg, process_withdraw_username, user)

    bot.answer_callback_query(call.id, "Введите Telegram username")

# ---- ОБРАБОТКА USERNAME ----
def process_withdraw_username(message, user):
    username = message.text.strip()
    if not username.startswith("@"):
        username = "@" + username

    stars = user["stars"]
    user["stars"] = 0  # обнуляем баланс после заявки

    # Сохраняем заявку для админа
    withdraw_requests.append({
        "user_id": message.from_user.id,
        "username": username,
        "stars": stars
    })

    bot.send_message(
        message.chat.id,
        (
            "<b>✅ Заявка на вывод принята</b>\n\n"
            f"⭐ Сумма: <b>{stars} звёзд</b>\n"
            f"📌 Telegram: <b>{username}</b>\n\n"
            "⏳ <i>Статус: в обработке</i>\n"
            "📬 <i>Ожидайте уведомление</i>"
        )
    )

# ---- RUN ----
bot.infinity_polling()
