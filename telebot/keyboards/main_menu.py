from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():

    kb = [
        [KeyboardButton(text="🔍 Новый поиск")],
        [KeyboardButton(text="🔎 Поиск по навыкам")],
        [KeyboardButton(text="ℹ️ О боте")]
    ]

    menu = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True,
        input_field_placeholder="Выберите действие..."
    )

    return menu