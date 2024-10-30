from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

in_game_ikb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="Наш канал",
            url="https://t.me/cscardss"
        )
    ], [InlineKeyboardButton(
            text="В игру",
            callback_data="in_game"
        )]
], resize_keyboard=True)

channel_ikb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="Подписаться",
            url="https://t.me/cscardss"
        )
    ], [InlineKeyboardButton(
            text="В игру",
            callback_data="in_game"
        )]
], resize_keyboard=True)

main_menu_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Получить карту")],
        [KeyboardButton(text="Моя коллекция"), KeyboardButton(text="Обмен")],
        [KeyboardButton(text="Мини-игры"), KeyboardButton(text="Донат")]
    ], resize_keyboard=True)

mini_games_ikb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="Рандом 🎲",
            callback_data="random"
        ), InlineKeyboardButton(
            text="Лаки Шот 🏀",
            callback_data="lucky_shot"
        )
    ], [InlineKeyboardButton(
            text="Квиз 🔍",
            callback_data="quiz"
        )
    ]
], resize_keyboard=True)

collection_ikb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="⬅️",
            callback_data="prev_card"
        ), InlineKeyboardButton(
            text="➡️",
            callback_data="next_card"
        )
    ]
], resize_keyboard=True)

ranks_ikb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="Сильвер",
            callback_data="rank_silver"
        ), InlineKeyboardButton(
            text="Звезда",
            callback_data="rank_gold_nova"
        )
    ], [
        InlineKeyboardButton(
            text="Калаш",
            callback_data="rank_ak"
        ),InlineKeyboardButton(
            text="Калаш с венками",
            callback_data="rank_ak_wreaths"
        )
    ], [InlineKeyboardButton(
            text="Два калаша",
            callback_data="rank_two_ak"
        ), InlineKeyboardButton(
            text="Биг стар",
            callback_data="rank_big_star"
        )
    ], [InlineKeyboardButton(
            text="Беркут",
            callback_data="rank_berkut"
        ), InlineKeyboardButton(
            text="Лем",
            callback_data="rank_lem"
        )
    ], [InlineKeyboardButton(
            text="Суприм",
            callback_data="rank_suprim"
        ), InlineKeyboardButton(
            text="Глобал",
            callback_data="rank_global"
        )
    ]
], resize_keyboard=True)

ranks_ikb_trans = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="Сильвер",
            callback_data="rank_silver_trans"
        ), InlineKeyboardButton(
            text="Звезда",
            callback_data="rank_gold_nova_trans"
        )
    ], [
        InlineKeyboardButton(
            text="Калаш",
            callback_data="rank_ak_trans"
        ),InlineKeyboardButton(
            text="Калаш с венками",
            callback_data="rank_ak_wreaths_trans"
        )
    ], [InlineKeyboardButton(
            text="Два калаша",
            callback_data="rank_two_ak_trans"
        ), InlineKeyboardButton(
            text="Биг стар",
            callback_data="rank_big_star_trans"
        )
    ], [InlineKeyboardButton(
            text="Беркут",
            callback_data="rank_berkut_trans"
        ), InlineKeyboardButton(
            text="Лем",
            callback_data="rank_lem_trans"
        )
    ], [InlineKeyboardButton(
            text="Суприм",
            callback_data="rank_suprim_trans"
        ), InlineKeyboardButton(
            text="Глобал",
            callback_data="rank_global_trans"
        )
    ]
], resize_keyboard=True)

transfer_ikb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="🔁 Создать обмен",
            callback_data="create_transfer"
    )],
    [InlineKeyboardButton(
            text="🕰 Текущие обмены",
            callback_data="tek_transfers"
    )],
    [InlineKeyboardButton(
            text="✅ Завершенные обмены",
            callback_data="my_transfers"
    )]
], resize_keyboard=True)