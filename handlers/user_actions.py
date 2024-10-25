import datetime
import sqlite3
import time

from aiogram import Router
from aiogram.types import Message, FSInputFile
from data.utils import is_subscribed, is_active, draw_card
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import F

from handlers import callbacks
from data import utils
from keyboards.general import channel_ikb, mini_games_ikb, collection_ikb, transfer_ikb

router = Router()
scheduler = AsyncIOScheduler()
card_counter = 0


@router.message(F.text == "Получить карту")
async def get_card(message: Message):
    if await is_subscribed(message.from_user.id) and is_active(message.from_user.id):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        data = cursor.execute(f"SELECT card_time, chances FROM users WHERE id='{message.from_user.id}'").fetchone()
        click_date, chances = data[0], data[1]
        # Получение времени последнего нажатия
        if click_date != '':
            t = (list(map(int, click_date.split()[0].split("-"))), list(map(int, click_date.split()[1].split("."))))
            click_date = datetime.datetime(t[0][0], t[0][1], t[0][2], t[1][0], t[1][1], t[1][2])
        today = datetime.datetime.today()

        # Если время последнего действия больше минимального
        if click_date == '' or today - datetime.timedelta(hours=6) > click_date or chances > 0:
            if chances == 0:
                cursor.execute(
                    f"UPDATE users SET card_time = '{today.strftime('%Y-%m-%d %H.%M.%S')}' WHERE id='{message.from_user.id}'")
                conn.commit()
            else:
                cursor.execute(
                    f"UPDATE users SET chances = chances - 1 WHERE id='{message.from_user.id}'")
                conn.commit()
            card_for_user = cursor.execute("SELECT * FROM cards WHERE amount > 0 ORDER BY RANDOM() LIMIT 1").fetchall()[0]

            # Если остались карты
            if len(card_for_user) == 6:
                cursor.execute(
                    f"UPDATE cards SET amount = amount - 1 WHERE id='{card_for_user[0]}'")
                conn.commit()
                cursor.execute(
                    f"INSERT INTO collections (user_id, card_id) VALUES ('{message.from_user.id}', '{card_for_user[0]}')")
                conn.commit()
                cursor.close()
                text = (f"<b>💥 Ты получаешь новую карту!</b>\n\n\n🔤 Никнейм: <b>{card_for_user[1]}</b>\n\n🕹 Команда: "
                        f"<b>{card_for_user[2]}</b>\n\n🎖 Звание: <b>{card_for_user[3]}</b>\n\n🔢 Очки: <b>{card_for_user[5]}</b>")

                photo = FSInputFile(path=f"./cards/{card_for_user[0]}.webp")
                await message.answer_photo(photo, caption=text, parse_mode="HTML")
            else:
                await message.answer("Сейчас мы не можем выдать тебе карту из-за непредвиденной ошибки🙅‍♂️. Мы в курсе проблемы и уже исправляем ее 🗿, чтобы как можно быстрее выдать тебе карту!")
                cursor.close()

        else:
            remains = str(datetime.timedelta(hours=6) - (today - click_date)).split(":")
            await message.answer(f"К сожалению, не прошло достаточно времени с последнего открытия⏳. Приходи и получай новую карту через {remains[0]} ч : {remains[1]} мин!")
            cursor.close()
    else:
        await message.delete()
        await message.answer('<b>Для продолжения игры необходимо подписать на наш канал</b>✅',
                             reply_markup=channel_ikb, parse_mode="HTML")


@router.message(F.text == "Моя коллекция")
async def get_card(message: Message):
    if await is_subscribed(message.from_user.id) and is_active(message.from_user.id):
        callbacks.card_index = 0
        await message.answer("🗃 Здесь ты можешь посмотреть свою коллекцию карт. Воспользуйся кнопками для удобной навигации по этому разделу.")

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        user_card_id = cursor.execute(f"SELECT card_id FROM collections WHERE user_id='{message.from_user.id}'").fetchall()[::-1][0][0]
        length = cursor.execute(f"SELECT COUNT(card_id) FROM collections WHERE user_id='{message.from_user.id}'").fetchone()[0]
        card_info = cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{user_card_id}'").fetchone()
        cursor.close()
        if len(card_info) == 5:
            card = utils.Card(card_info)
            await draw_card(typ="base", tek=1, all=length, card=card, message=message)
        else:
            await message.answer("Кажется, в твоей коллекции нет карт ❌")


    else:
        await message.delete()
        await message.answer('<b>Для продолжения игры необходимо подписать на наш канал</b>✅',
                             reply_markup=channel_ikb, parse_mode="HTML")


@router.message(F.text == "Обмен")
async def get_card(message: Message):
    if await is_subscribed(message.from_user.id) and is_active(message.from_user.id):
        await message.answer("🔄 Здесь ты можешь создавать и управлять своими обменами, а также смотреть историю успешных обменов. Выбери действие из кнопок ниже:", reply_markup=transfer_ikb)
    else:
        await message.delete()
        await message.answer('<b>Для продолжения игры необходимо подписать на наш канал</b>✅',
                             reply_markup=channel_ikb, parse_mode="HTML")


@router.message(F.text == "Мини-игры")
async def get_card(message: Message):
    if await is_subscribed(message.from_user.id) and is_active(message.from_user.id):
        await message.answer("Выберите мини-игру", reply_markup=mini_games_ikb)
    else:
        await message.delete()
        await message.answer('<b>Для продолжения игры необходимо подписать на наш канал</b>✅',
                             reply_markup=channel_ikb, parse_mode="HTML")


@router.message(F.text == "Донат")
async def get_card(message: Message):
    if await is_subscribed(message.from_user.id) and is_active(message.from_user.id):
        await message.answer("В разработке")
    else:
        await message.delete()
        await message.answer('<b>Для продолжения игры необходимо подписать на наш канал</b>✅',
                             reply_markup=channel_ikb, parse_mode="HTML")