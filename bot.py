import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web

# Токен вашего бота
TOKEN = "8812919203:AAHQyxYuOfjd9zLG-GEBK_-pNN4wS4xrXd4"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Список каналов для проверки (username каналов)
CHANNELS_TO_CHECK = ["@chat_nft71", "@kkepersinfo"]


# Функция проверки подписки на каналы
async def check_subscription(user_id: int) -> bool:
    for channel in CHANNELS_TO_CHECK:
        try:
            member = await bot.get_chat_member(
                chat_id=channel, user_id=user_id
            )
            # Если статус пользователя не входит в разрешенные — он не подписан
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            logging.error(f"Ошибка проверки подписки в {channel}: {e}")
            # Если бот не админ в канале, проверка вернет False.
            # На время тестов (пока не добавили бота в админы) можно временно заменить на: return True
            return False
    return True


# Клавиатура главного экрана подписки
def get_main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔗 Подписаться", url="https://t.me/chat_nft71"
                ),
                InlineKeyboardButton(
                    text="🔗 Подписаться", url="https://t.me/kkepersinfo"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✅ Проверить подписки", callback_data="check_subs"
                )
            ],
        ]
    )


# Функция отправки главного приветственного сообщения
async def send_welcome_message(chat_id: int, username: str):
    text = (
        f'<tg-emoji emoji-id="5469670422305861628">👋</tg-emoji> Приветствую {username}, '
        f"подпишись на каналы и забирай Telegram Stars абсолютно бесплатно!\n\n"
        f'<blockquote><tg-emoji emoji-id="5235570365094188078">📢</tg-emoji> '
        f"подпишись на телеграм каналы наших спонсоров так как без них не было б такой раздачи звезд!</blockquote>"
    )
    await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard(),
    )


# Обработчик команды /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else message.from_user.first_name
    )
    await send_welcome_message(message.chat.id, username)


# Обработчик кнопки "Проверить подписки"
@dp.callback_query(lambda c: c.data == "check_subs")
async def process_check_subs(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = (
        f"@{callback.from_user.username}"
        if callback.from_user.username
        else callback.from_user.first_name
    )

    is_subscribed = await check_subscription(user_id)

    if is_subscribed:
        # Успешно подписан: удаляем старое сообщение
        try:
            await callback.message.delete()
        except Exception:
            pass

        # Отправляем сообщение "Заработай свои звездочки!"
        success_text = '<b><tg-emoji emoji-id="5386521874089914548">⭐️</tg-emoji> Заработай свои звездочки!</b>'
        success_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💸 Заработать", callback_data="earn"
                    ),
                    InlineKeyboardButton(
                        text="👤 Профиль", callback_data="profile"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="💬 Отзывы", callback_data="reviews"
                    ),
                    InlineKeyboardButton(
                        text="💳 Вывести", callback_data="withdraw"
                    ),
                ],
            ]
        )
        await callback.message.answer(
            text=success_text,
            parse_mode=ParseMode.HTML,
            reply_markup=success_keyboard,
        )

    else:
        # Не подписан: удаляем старое сообщение
        try:
            await callback.message.delete()
        except Exception:
            pass

        # Отправляем сообщение об ошибке
        fail_text = f'<tg-emoji emoji-id="5220197908342648622">⚠️</tg-emoji> {username} вы не подписались на все каналы , перепроверьте!'
        fail_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", callback_data="go_back"
                    )
                ]
            ]
        )
        await callback.message.answer(
            text=fail_text,
            parse_mode=ParseMode.HTML,
            reply_markup=fail_keyboard,
        )

    await callback.answer()


# Обработчик кнопки "Назад"
@dp.callback_query(lambda c: c.data == "go_back")
async def process_go_back(callback: types.CallbackQuery):
    username = (
        f"@{callback.from_user.username}"
        if callback.from_user.username
        else callback.from_user.first_name
    )

    # Удаляем сообщение с ошибкой
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Возвращаем на первый шаг (где надо подписаться)
    await send_welcome_message(callback.message.chat.id, username)
    await callback.answer()


# Заглушки для новых кнопок меню (чтобы бот не выдавал ошибку при нажатии)
@dp.callback_query(lambda c: c.data in ["earn", "profile", "reviews", "withdraw"])
async def process_menu_buttons(callback: types.CallbackQuery):
    actions = {
        "earn": "Вы перешли в раздел 'Заработать'!",
        "profile": "Ваш профиль пуст.",
        "reviews": "Тут будут отзывы.",
        "withdraw": "Вывод пока недоступен.",
    }
    await callback.answer(actions.get(callback.data), show_alert=True)


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
    # Запускаем фоновый веб-сервер
    await start_web_server()
    # Запускаем бота
    print("Бот успешно запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
