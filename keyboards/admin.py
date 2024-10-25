from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

admin_menu_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Добавить карту")],
        [KeyboardButton(text="Забанить"), KeyboardButton(text="Разбанить")],
        [KeyboardButton(text="Квиз")]
    ], resize_keyboard=True)

cansel_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Отмена")],
    ], resize_keyboard=True)

confirm_quiz = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="Да",
            callback_data="confirm_quiz"
        )
    ], [InlineKeyboardButton(
            text="Нет",
            callback_data="disclaim_quiz"
        )]
], resize_keyboard=True)