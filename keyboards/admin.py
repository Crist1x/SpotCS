from locale import currency

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

admin_menu_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Добавить карту")],
        [KeyboardButton(text="Перевести валюту")],
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

currency_ikb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="15 💰", callback_data="currency_15"), InlineKeyboardButton(text="30 💰", callback_data="currency_30")],
    [InlineKeyboardButton(text="60 💰", callback_data="currency_60"), InlineKeyboardButton(text="100 💰", callback_data="currency_100")],
    [InlineKeyboardButton(text="200 💰", callback_data="currency_200"), InlineKeyboardButton(text="500 💰", callback_data="currency_500")]
], resize_keyboard=True)