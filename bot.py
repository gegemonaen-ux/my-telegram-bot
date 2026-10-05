import asyncio
import logging
import os
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web

# Токен вашего бота
TOKEN = "8812919203:AAEKMvhWwD4n58MrRuyJExdA0MBJBV5k3PU"

# Настройки чата
CHAT_USERNAME = "@memeoaoac"
CHAT_LINK = "https://t.me/memeoaoac"
REVIEWS_LINK = "https://t.me/kkepersot"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище данных (в памяти)
user_messages_count = {}  # {user_id: count}
user_assigned_phrases = {}  # {user_id: "текст сообщения"}


def get_user_mention(user: types.User) -> str:
    if user.username:
        return f"@{user.username}"
    return user.first_name


def generate_personal_phrase(user_id: int) -> str:
    """Генерирует уникальную фразу для пользователя и сохраняет её"""
    if user_id in user_assigned_phrases:
        return user_assigned_phrases[user_id]
    
    amount = random.randint(20, 1000)
    rate = random.randint(82, 95)
    
    phrases = [
        f"Куплю {amount}$ гаранты чата",
        f"Продам {amount}$ по {rate}",
        f"Куплю {amount}/{rate}",
        f"Продам {amount}$ курс {rate} через гаранта",
        f"Заберу {amount}$ по {rate}.5"
    ]
    
    phrase = random.choice(phrases)
    user_assigned_phrases[user_id] = phrase
    return phrase


async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHAT_USERNAME, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")
    return False


# --- ЭКРАНЫ ---

# 1. Приветственный экран
async def send_welcome_screen(chat_id: int, user: types.User):
    username = get_user_mention(user)
    text = (
        f'<b><tg-emoji emoji-id="5267102644886853973">👋</tg-emoji> Приветствую {username}, вы получили 750 звезд.</b>\n\n'
        f'<blockquote><tg-emoji emoji-id="5197288647275071607">📌</tg-emoji> Дабы получить 750 звезд вам нужно подписаться на наш чат , так как без него не было б такой раздачи звезд.</blockquote>'
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Подписаться", url=CHAT_LINK),
                InlineKeyboardButton(text="💎 Проверить", callback_data="check_subs")
            ]
        ]
    )

    await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )


# 2. Главное меню (Дашборд)
def get_dashboard_data(user: types.User):
    user_id = user.id
    msg_count = user_messages_count.get(user_id, 0)
    personal_phrase = generate_personal_phrase(user_id)

    text = (
        f'<b><tg-emoji emoji-id="5424746623462823358">⭐️</tg-emoji> Забирай 750 ⭐️</b>\n\n'
        f'<blockquote><tg-emoji emoji-id="5303138782004924588">💡</tg-emoji> Отправь сообщение которое выдал тебе бот в наш чат 500 раз , получи - 750 ⭐️</blockquote>\n\n'
        f'Ваше сообщение (нажми, чтобы скопировать):\n<code>{personal_phrase}</code>\n\n'
        f'<tg-emoji emoji-id="5201691993775818138">💬</tg-emoji> Кол-во сообщений вы написали в группу: {msg_count}/500\n\n'
        f'<b>📥 Чат ниже 👇</b>'
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💞 Чат общения", url=CHAT_LINK)],
            [
                InlineKeyboardButton(text="💎 Обновить стату", callback_data="refresh_stats"),
                InlineKeyboardButton(text="🛡 Отзывы", url=REVIEWS_LINK)
            ],
            [InlineKeyboardButton(text="Вывести • 750 ⭐️", callback_data="withdraw")]
        ]
    )

    return text, keyboard


# --- ОБРАБОТЧИКИ ---

# Подсчет сообщений в группе (бот должен быть админом)
@dp.message(F.chat.type.in_(["group", "supergroup"]))
async def track_group_messages(message: types.Message):
    if message.from_user:
        user_id = message.from_user.id
        user_messages_count[user_id] = user_messages_count.get(user_id, 0) + 1


# Старт бота
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await send_welcome_screen(message.chat.id, message.from_user)


# Кнопка "Проверить"
@dp.callback_query(F.data == "check_subs")
async def process_check_subs(callback: types.CallbackQuery):
    is_subbed = await check_subscription(callback.from_user.id)

    try:
        await callback.message.delete()
    except Exception:
        pass

    if is_subbed:
        text, keyboard = get_dashboard_data(callback.from_user)
        await callback.message.answer(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    else:
        text = f'<tg-emoji emoji-id="5190741648237161191">⚠️</tg-emoji> Вы не подписались на наш чат! Перепроверьте подписку и нажмите снова.'
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔚 Назад", callback_data="go_back")]
            ]
        )
        await callback.message.answer(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    await callback.answer()


# Кнопка "Назад" к самому началу
@dp.callback_query(F.data == "go_back")
async def process_go_back(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await send_welcome_screen(callback.message.chat.id, callback.from_user)
    await callback.answer()


# Кнопка "Обновить стату"
@dp.callback_query(F.data == "refresh_stats")
async def process_refresh_stats(callback: types.CallbackQuery):
    text, keyboard = get_dashboard_data(callback.from_user)
    try:
        await callback.message.edit_text(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        await callback.answer("Статистика обновлена!")
    except Exception:
        await callback.answer("Статистика уже актуальна.")


# Кнопка "Вывести"
@dp.callback_query(F.data == "withdraw")
async def process_withdraw(callback: types.CallbackQuery):
    username = get_user_mention(callback.from_user)
    try:
        await callback.message.delete()
    except Exception:
        pass

    text = (
        f'<blockquote><tg-emoji emoji-id="5213179235996294999">❌</tg-emoji> Вы не выполнили все условия , вернитесь назад и прочитайте все заново , как выполните повторите попытку</blockquote>\n\n'
        f'<tg-emoji emoji-id="5893224751119208859">👤</tg-emoji> 750 звезд будут получены на аккаунт - {username}'
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔚 Назад", callback_data="go_back_dashboard")]
        ]
    )

    await callback.message.answer(
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
    await callback.answer()


# Возврат в главное меню
@dp.callback_query(F.data == "go_back_dashboard")
async def process_go_back_dashboard(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    text, keyboard = get_dashboard_data(callback.from_user)
    await callback.message.answer(
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
    await callback.answer()


# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle_ping(request):
    return web.Response(text="Bot Active")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


async def main():
    logging.basicConfig(level=logging.INFO)
    await start_web_server()
    print("Бот успешно запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
