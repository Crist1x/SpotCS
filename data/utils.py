import sqlite3

import aiogram
from aiogram import types
from aiogram.types import Message, FSInputFile, InputMedia, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton

from config import CHANNEL_ID
from dispatcher import bot
from keyboards.general import collection_ikb


def remove_prefix(text, prefix):
    if text.lower().startswith(prefix.lower()):
        return text[len(prefix):]
    return text


async def is_subscribed(user_id):
    user_channel_status = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
    if user_channel_status.status != 'left':
        return True
    else:
        return False


def is_active(user_id):
    conn = sqlite3.connect('./database.db')
    cursor = conn.cursor()
    status = cursor.execute(f"SELECT status FROM users WHERE id={user_id}").fetchone()[0]
    cursor.close()
    if status == "active":
        return True
    else:
        return False


class Card:
    def __init__(self, card_info):
        self.id = card_info[0]
        self.name = card_info[1]
        self.team = card_info[2]
        self.rank = card_info[3]
        self.score = card_info[4]


async def draw_card(typ, tek, all, card: Card, callback:types.CallbackQuery = False, message:Message = False):
    text = f"""🔤 Никнейм: <b>{card.name}</b> 
    
🕹 Команда: <b>{card.team}</b>

🎖 Звание: <b>{card.rank}</b>

🔢 Очки: <b>{card.score}</b>"""

    photo = FSInputFile(path=f"./cards/{card.id}.webp")

    if typ == "base":
        collection_ikb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏪",
                    callback_data="first_card"
                ), InlineKeyboardButton(
                    text="⬅️",
                    callback_data="prev_card"
                ), InlineKeyboardButton(
                    text=f"{tek}/{all}",
                    callback_data="nothing"
                ), InlineKeyboardButton(
                    text="➡️",
                    callback_data="next_card"
                ), InlineKeyboardButton(
                    text="⏩",
                    callback_data="last_card"
                )
            ], [InlineKeyboardButton(
                    text="🔍 Поиск",
                    callback_data="search"
                )], [InlineKeyboardButton(
                    text="🎖 По званию",
                    callback_data="by_rank"
                )], [InlineKeyboardButton(
                    text="🕹 По команде",
                    callback_data="by_team"
                )]
        ], resize_keyboard=True)
    elif typ == "transfer":
        collection_ikb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏪",
                    callback_data=f"first_card_{typ}"
                ), InlineKeyboardButton(
                text="⬅️",
                callback_data=f"prev_card_{typ}"
                ), InlineKeyboardButton(
                    text=f"➕",
                    callback_data=f"add_card"
                ), InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"next_card_{typ}"
                ), InlineKeyboardButton(
                    text="⏩",
                    callback_data=f"last_card_{typ}"
                )
            ]
        ], resize_keyboard=True)
    else:
        collection_ikb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏪",
                    callback_data=f"first_card_{typ}"
                ), InlineKeyboardButton(
                text="⬅️",
                callback_data=f"prev_card_{typ}"
            ), InlineKeyboardButton(
                text=f"{tek}/{all}",
                callback_data=f"nothing_{typ}"
            ), InlineKeyboardButton(
                text="➡️",
                callback_data=f"next_card_{typ}"
            ), InlineKeyboardButton(
                text="⏩",
                callback_data=f"last_card_{typ}"
            )
            ], [InlineKeyboardButton(
                text="В коллекцию",
                callback_data="to_collection"
            )]
        ], resize_keyboard=True)

    if message:
        return await message.answer_photo(photo, caption=text, parse_mode="HTML", reply_markup=collection_ikb)
    if callback:
        if callback.data != "to_collection":
            try:
                await callback.message.edit_media(InputMediaPhoto(media=photo, caption=text), parse_mode="HTML", reply_markup=collection_ikb)
            except Exception as e:
                await callback.message.answer_photo(photo, caption=text, parse_mode="HTML", reply_markup=collection_ikb)
        else:
            await callback.message.answer_photo(photo, caption=text, parse_mode="HTML", reply_markup=collection_ikb)

search_cards = []

async def sort_by_rank(rank, callback: types.CallbackQuery):
    global search_cards
    conn = sqlite3.connect('./database.db')
    cursor = conn.cursor()
    length = cursor.execute(
        f"SELECT COUNT(cards.id) FROM cards, collections WHERE cards.id = collections.card_id AND cards.rank = '{rank}' AND collections.user_id='{callback.from_user.id}'").fetchone()[
        0]
    cards = cursor.execute(
        f"SELECT cards.id, cards.player, cards.team, cards.rank, cards.score FROM cards, collections WHERE cards.id = collections.card_id AND cards.rank = '{rank}' AND collections.user_id='{callback.from_user.id}'").fetchall()[::-1]
    search_cards = cards
    if len(cards) >= 1:
        if len(cards[0]) == 5:
            card = Card(cards[0])
            await draw_card(typ="rank", tek=1, all=length, card=card, callback=callback)
        else:
            await callback.message.answer(" ❌ Кажется, в твоей коллекции нет таких карт...")
    else:
        await callback.message.answer(" ❌ Кажется, в твоей коллекции нет таких карт...")
