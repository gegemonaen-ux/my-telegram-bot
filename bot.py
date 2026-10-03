import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Токен вашего бота
BOT_TOKEN = "8812919203:AAFgJLtosHkdCEflL3vl2nq36X6kINUaxmQ"

bot = Bot(token=BOT_TOKEN, default=properties=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Временная база данных в памяти для имитации прогресса пользователей
user_data = {}

def get_user_stats(user_id: int):
    """Инициализирует или обновляет прогресс пользователя для реалистичности"""
    if user_id not in user_data:
        # Стартовые значения: например, 12 сообщений и 2 часа 50 минут (170 минут) осталось
        user_data[user_id] = {
            "messages": random.randint(5, 25),
            "minutes_left": random.randint(160, 179)
        }
    return user_data[user_id]

def update_user_stats(user_id: int):
    """Слегка улучшает статистику при нажатии кнопки 'Обновить'"""
    stats = get_user_stats(user_id)
    # Прибавляем от 3 до 10 сообщений
    stats["messages"] = min(500, stats["messages"] + random.randint(3, 10))
    # Уменьшаем время на 2-5 минут
    stats["minutes_left"] = max(0, stats["minutes_left"] - random.randint(2, 5))
    return stats

def format_time(minutes: int) -> str:
    """Форматирует минуты в красивую строку 'Х часа и Y минут'"""
    hours = minutes // 60
    mins = minutes % 60
    
    if hours > 0:
        return f"{hours} часа и {mins} минут"
    return f"{mins} минут"

# --- Клавиатуры ---

def get_start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐️ Получить звезды", callback_data="get_stars")
    return builder.as_markup()

def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🪎 Подписаться на чат", url="https://t.me/femelyspace")
    builder.button(text="💎 Обновить", callback_data="refresh_stats")
    builder.button(text="⭐️ Вывести", callback_data="withdraw_stars")
    builder.button(text="🛡️ Отзывы", url="https://t.me/kkepersot")
    # Выстраиваем кнопки: первая кнопка на всю ширину, потом по две в ряд
    builder.adjust(1, 2, 1)
    return builder.as_markup()

def get_back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data="back_to_main")
    return builder.as_markup()

# --- Шаблоны сообщений ---

def get_main_text(username: str, stats: dict) -> str:
    time_str = format_time(stats["minutes_left"])
    return (
        f'<tg-emoji emoji-id="5215480427933898474">⭐</tg-emoji> <b>Чтобы вывести 750 звезд на аккаунт @{username}, нужно провести 3 часа в чате активно!</b>\n\n'
        f'<tg-emoji emoji-id="5902335789798265487">⚠️</tg-emoji> <blockquote>Нельзя спамить , только общение среди пользователей , после того как будете актив нажмите кнопку получить звезды , после звезды автоматически придут на аккаунт!</blockquote>\n\n'
        f'<tg-emoji emoji-id="5258274739041883702">💬</tg-emoji> кол-во сообщений отправлено: <b>{stats["messages"]}</b> из 500.\n'
        f'<tg-emoji emoji-id="5895444149699612825">⏳</tg-emoji> Осталось быть в активе: <b>{time_str}</b>\n\n'
        f'<tg-emoji emoji-id="5893203503915996356">🔔</tg-emoji> <b>ЧТОБЫ УЗНАТЬ СКОЛЬКО ВЫ БЫЛИ АКТИВНЫ И СКОЛЬКО ОТПРАВИЛИ СООБЩЕНИЙ НАЖИМАЙТЕ КНОПКУ ОБНОВИТЬ!</b>\n\n'
        f'⚡️ Чат - https://t.me/femelyspace'
    )

# --- Обработчики ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    username = message.from_user.username or message.from_user.first_name
    text = (
        f'<tg-emoji emoji-id="5893442248263078309">👋</tg-emoji> @{username} вы успешно получили 750 звезд, '
        f'быстрее выводи их!'
    )
    await message.answer(text, reply_markup=get_start_keyboard())

@dp.callback_query(F.data == "get_stars")
async def process_get_stars(callback: types.CallbackQuery):
    username = callback.from_user.username or callback.from_user.first_name
    stats = get_user_stats(callback.from_user.id)
    text = get_main_text(username, stats)
    
    # Удаляем старое приветствие и отправляем новое информационное сообщение
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=get_main_keyboard(), disable_web_page_preview=True)
    await callback.answer()

@dp.callback_query(F.data == "refresh_stats")
async def process_refresh(callback: types.CallbackQuery):
    username = callback.from_user.username or callback.from_user.first_name
    # Обновляем прогресс (сообщения растут, время падает)
    stats = update_user_stats(callback.from_user.id)
    text = get_main_text(username, stats)
    
    # Изменяем только текст сообщения и счетчики, клавиатуру оставляем прежней
    try:
        await callback.message.edit_text(text, reply_markup=get_main_keyboard(), disable_web_page_preview=True)
    except Exception:
        # Перехватываем ошибку, если текст не изменился (например, при частых кликах)
        pass
    await callback.answer("Данные успешно обновлены! 💎")

@dp.callback_query(F.data == "withdraw_stars")
async def process_withdraw(callback: types.CallbackQuery):
    text = (
        f'<tg-emoji emoji-id="5213179235996294999">❌</tg-emoji> '
        f'Вам нужно провести 3 часа актив , и отправил 500 сообщений в чат , нельзя спамить! Только общение.'
    )
    # Удаляем текущее сообщение и присылаем отказ с кнопкой Назад
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=get_back_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "back_to_main")
async def process_back(callback: types.CallbackQuery):
    username = callback.from_user.username or callback.from_user.first_name
    stats = get_user_stats(callback.from_user.id)
    text = get_main_text(username, stats)
    
    # Удаляем сообщение об отказе и возвращаем главное меню
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=get_main_keyboard(), disable_web_page_preview=True)
    await callback.answer()

# Запуск бота
async def main():
    print("Бот успешно запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
