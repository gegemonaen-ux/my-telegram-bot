import asyncio
import logging
import os
import time
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web

# Токен вашего бота
TOKEN = "8812919203:AAEKMvhWwD4n58MrRuyJExdA0MBJBV5k3PU"

# Username чата для проверки подписки и подсчета сообщений
CHAT_USERNAME = "@chat_nft71"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище данных (сообщения и время подписки)
# В реальном проекте это БД, в рамках кода - словарь в памяти
user_messages = {}  # {user_id: count}
user_sub_time = {}  # {user_id: timestamp_start}


# Вспомогательная функция формирования имени пользователя
def get_user_mention(user: types.User) -> str:
    if user.username:
        return f"@{user.username}"
    return user.first_name


# Вспомогательная функция расчета времени (часы и минуты)
def get_time_spent(user_id: int) -> str:
    if user_id not in user_sub_time:
        user_sub_time[user_id] = time.time()

    elapsed = int(time.time() - user_sub_time[user_id])
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60

    if hours > 0:
        return f"{hours} часа и {minutes} минут"
    else:
        return f"{minutes} минут"


# Проверка подписки на чат
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(
            chat_id=CHAT_USERNAME, user_id=user_id
        )
        if member.status in ["member", "administrator", "creator"]:
            return True
    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")
    return False


# --- ЭКРАНЫ И КЛАВИАТУРЫ ---


# 1. Приветственное сообщение (Экран 1)
async def send_welcome_screen(chat_id: int, username: str):
    text = (
        f'<b><tg-emoji emoji-id="5267102644886853973">👋</tg-emoji> Приветствую {username}, вы получили 750 звезд.</b>\n\n'
        f'<blockquote><tg-emoji emoji-id="5197288647275071607">📌</tg-emoji> Дабы получить 750 звезд вам нужно подписаться на наш чат , так как без него не было б такой раздачи звезд.</blockquote>'
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Подписаться", url="https://t.me/chat_nft71"
                ),
                InlineKeyboardButton(
                    text="💎 Проверить", callback_data="check_subs"
                ),
            ]
        ]
    )

    await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


# 2. Главное меню заданий (Экран Подписан)
def get_dashboard_data(user_id: int):
    msg_count = user_messages.get(user_id, 0)
    time_str = get_time_spent(user_id)

    text = (
        f'<b><tg-emoji emoji-id="5424746623462823358">⭐️</tg-emoji> Забирай 750 ⭐️</b>\n\n'
        f'<blockquote><tg-emoji emoji-id="5303138782004924588">💡</tg-emoji> Будь 2 часа в активе , и отправь более 500 сообщений - получи 750 ⭐️ за 1 клик , как все сделаешь нажми на кнопку ( Получить звезды )</blockquote>\n\n'
        f'<tg-emoji emoji-id="5201691993775818138">💬</tg-emoji> Кол-во сообщений вы написали в группу: {msg_count}/500\n'
        f'<tg-emoji emoji-id="5382194935057372936">⏱</tg-emoji> Вы провели: {time_str}/3 часа.\n\n'
        f"<b>📥 Чат ниже 👇</b>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💞 Чат общения", url="https://t.me/chat_nft71"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 Обновить стату", callback_data="refresh_stats"
                ),
                InlineKeyboardButton(
                    text="🛡 Отзывы", url="https://t.me/kkepersot"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⭐️ Вывести", callback_data="withdraw"
                )
            ],
        ]
    )

    return text, keyboard


# --- ОБРАБОТЧИКИ КОМАНД И НАЖАТИЙ ---


# Подсчет сообщений от пользователей в самом чате
@dp.message(F.chat.type.in_(["group", "supergroup"]))
async def track_group_messages(message: types.Message):
    if message.from_user:
        user_id = message.from_user.id
        user_messages[user_id] = user_messages.get(user_id, 0) + 1


# Старт бота
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    username = get_user_mention(message.from_user)
    await send_welcome_screen(message.chat.id, username)


# Проверка подписки по кнопке "Проверить"
@dp.callback_query(F.data == "check_subs")
async def process_check_subs(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = get_user_mention(callback.from_user)

    is_subbed = await check_subscription(user_id)

    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except Exception:
        pass

    if is_subbed:
        # Устанавливаем время подписки, если пользователь зашел впервые
        if user_id not in user_sub_time:
            user_sub_time[user_id] = time.time()

        text, keyboard = get_dashboard_data(user_id)
        await callback.message.answer(
            text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard
        )
    else:
        # Не подписан
        text = f'<tg-emoji emoji-id="5190741648237161191">⚠️</tg-emoji> Вы не подписались на наш чат! Перепроверьте подписку и нажмите снова.'
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔚 Назад", callback_data="go_back"
                    )
                ]
            ]
        )
        await callback.message.answer(
            text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard
        )

    await callback.answer()


# Кнопка "Назад" к первому экрану
@dp.callback_query(F.data == "go_back")
async def process_go_back(callback: types.CallbackQuery):
    username = get_user_mention(callback.from_user)
    try:
        await callback.message.delete()
    except Exception:
        pass

    await send_welcome_screen(callback.message.chat.id, username)
    await callback.answer()


# Кнопка "Обновить стату" (редактирует существующее сообщение)
@dp.callback_query(F.data == "refresh_stats")
async def process_refresh_stats(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    text, keyboard = get_dashboard_data(user_id)

    try:
        await callback.message.edit_text(
            text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard
        )
        await callback.answer("Статистика обновлена!")
    except Exception:
        await callback.answer("Данные уже актуальны.")


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
            [
                InlineKeyboardButton(
                    text="🔚 Назад", callback_data="go_back_dashboard"
                )
            ]
        ]
    )

    await callback.message.answer(
        text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard
    )
    await callback.answer()


# Кнопка "Назад" из раздела вывода в Главное Меню
@dp.callback_query(F.data == "go_back_dashboard")
async def process_go_back_dashboard(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    try:
        await callback.message.delete()
    except Exception:
        pass

    text, keyboard = get_dashboard_data(user_id)
    await callback.message.answer(
        text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard
    )
    await callback.answer()


# --- ВЕБ-СЕРВЕР ДЛЯ РАБОТЫ НА RENDER 24/7 ---
async def handle_ping(request):
    return web.Response(text="Bot is running!")


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
