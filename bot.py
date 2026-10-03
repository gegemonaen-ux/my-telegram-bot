import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Токен вашего бота
TOKEN = "8812919203:AAHQyxYuOfjd9zLG-GEBK_-pNN4wS4xrXd4"

bot = Bot(token=TOKEN)
dp = Dispatcher()


# Обработчик команды /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # Сообщение с анимированным/кастомным эмодзи по его ID
    text = '<tg-emoji emoji-id="5469670422305861628">👋</tg-emoji> Привет'

    # Создание красной кнопки (с красным эмодзи / кастомным значком)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛑 Пока",  # Красный акцент для кнопки
                    callback_data="action_bye",
                )
            ]
        ]
    )

    # Отправка сообщения с включенным HTML-форматированием
    await message.answer(
        text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard
    )


# Обработчик нажатия на кнопку "Пока"
@dp.callback_query(lambda c: c.data == "action_bye")
async def process_bye_button(callback: types.CallbackQuery):
    await callback.answer("Вы нажали кнопку 'Пока'")
    await callback.message.answer("До свидания! 👋")


async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот успешно запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
