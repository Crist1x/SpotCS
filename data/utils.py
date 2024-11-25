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


async def draw_card(typ, tek, all, card: Card, is_transfer=False, callback:types.CallbackQuery = False, message:Message = False, send=None, usr_id=None):
    conn = sqlite3.connect('./database.db')
    cursor = conn.cursor()
    if message:
        if usr_id:
            score = cursor.execute(f"SELECT season_score FROM users WHERE id='{usr_id}'").fetchone()[0]
        else:
            score = cursor.execute(f"SELECT season_score FROM users WHERE id='{message.from_user.id}'").fetchone()[0]
    if callback:
        score = cursor.execute(f"SELECT season_score FROM users WHERE id='{callback.from_user.id}'").fetchone()[0]
    text = f"""🔤 Никнейм: <b>{card.name}</b> 
    
🕹 Команда: <b>{card.team}</b>

🎖 Звание: <b>{card.rank}</b>

🔢 Очки: <b>{card.score}</b>

🧮 Общее количество очков: <b>{score}</b>"""

    photo = FSInputFile(path=f"./cards/{card.id}.jpg")

    if typ == "base":
        if is_transfer:
            if callback:
                cursor.execute(f"UPDATE indexes SET card_transfer_index='{card.id}' WHERE user_id='{callback.from_user.id}'")
                conn.commit()
            else:
                cursor.execute(f"UPDATE indexes SET card_transfer_index='{card.id}' WHERE user_id='{message.from_user.id}'")
                conn.commit()
            cursor.close()
            collection_ikb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⏪",
                        callback_data="first_card_trans"
                    ), InlineKeyboardButton(
                    text="⬅️",
                    callback_data="prev_card_trans"
                ), InlineKeyboardButton(
                    text=f"➕",
                    callback_data=f"add_card"
                ), InlineKeyboardButton(
                    text="➡️",
                    callback_data="next_card_trans"
                ), InlineKeyboardButton(
                    text="⏩",
                    callback_data="last_card_trans"
                )
                ], [InlineKeyboardButton(
                    text="🔍 Поиск",
                    callback_data="search_trans"
                )], [InlineKeyboardButton(
                    text="🎖 По званию",
                    callback_data="by_rank_trans"
                )], [InlineKeyboardButton(
                    text="🕹 По команде",
                    callback_data="by_team_trans"
                )]
            ], resize_keyboard=True)
        else:
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
    else:
        if is_transfer:
            if callback:
                cursor.execute(f"UPDATE indexes SET card_transfer_index='{card.id}' WHERE user_id='{callback.from_user.id}'")
            else:
                cursor.execute(f"UPDATE indexes SET card_transfer_index='{card.id}' WHERE user_id='{message.from_user.id}'")
            conn.commit()
            collection_ikb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⏪",
                        callback_data=f"first_card_trans_{typ}"
                    ), InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"prev_card_trans_{typ}"
                ), InlineKeyboardButton(
                    text=f"➕",
                    callback_data=f"add_card"
                ), InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"next_card_trans_{typ}"
                ), InlineKeyboardButton(
                    text="⏩",
                    callback_data=f"last_card_trans_{typ}"
                )
                ], [InlineKeyboardButton(
                    text="В коллекцию",
                    callback_data="to_collection"
                )]
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

    conn.commit()
    cursor.close()
    if message:
        return await message.answer_photo(photo, caption=text, parse_mode="HTML", reply_markup=collection_ikb)
    if callback:
        if send:
            await callback.message.answer_photo(photo, caption=text, parse_mode="HTML", reply_markup=collection_ikb)
        else:
            if callback.data != "to_collection":
                try:
                    await callback.message.edit_media(InputMediaPhoto(media=photo, caption=text), parse_mode="HTML", reply_markup=collection_ikb)
                except Exception as e:
                    print(e)
                    await callback.answer("")

            else:
                await callback.message.answer_photo(photo, caption=text, parse_mode="HTML", reply_markup=collection_ikb)


async def sort_by_rank(rank, callback: types.CallbackQuery, trans=False):
    conn = sqlite3.connect('./database.db')
    cursor = conn.cursor()
    length = cursor.execute(f"SELECT COUNT(cards.id) FROM cards, collections WHERE cards.id = collections.card_id AND cards.rank = '{rank}' AND collections.user_id='{callback.from_user.id}'").fetchone()[0]
    cursor.execute(f"UPDATE indexes SET rank='{rank}' WHERE user_id='{callback.from_user.id}'")
    conn.commit()
    cards = cursor.execute(f"SELECT cards.id, cards.player, cards.team, cards.rank, cards.score FROM cards, collections WHERE cards.id = collections.card_id AND cards.rank = '{rank}' AND collections.user_id='{callback.from_user.id}'").fetchall()[::-1]
    cursor.close()
    if len(cards) >= 1:
        if len(cards[0]) == 5:
            card = Card(cards[0])
            if trans:
                await draw_card(typ="rank", tek=1, all=length, is_transfer=True, card=card, message=callback.message, usr_id=callback.from_user.id)
            else:
                await draw_card(typ="rank", tek=1, all=length, card=card, message=callback.message, usr_id=callback.from_user.id)
        else:
            await callback.message.answer(" ❌ Кажется, в твоей коллекции нет таких карт...")
    else:
        await callback.message.answer(" ❌ Кажется, в твоей коллекции нет таких карт...")
