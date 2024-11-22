from idlelib.pyparse import trans

from aiogram import types
import sqlite3

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, \
    InputMediaPhoto
from aiogram.fsm.context import FSMContext
from pyexpat.errors import messages

from config import CHANNEL_ID, menu_text
from data import utils
from data.forms import Quiz, GetAnswer, Search, Team, TransferID
from data.utils import draw_card, sort_by_rank
from dispatcher import bot
import datetime

import time

from handlers.admin_actions import add_card
from keyboards.admin import cansel_kb, admin_menu_kb
from keyboards.general import channel_ikb, main_menu_kb, ranks_ikb, ranks_ikb_trans


# Вход в игру
async def in_game(callback: types.CallbackQuery):
    user_channel_status = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=callback.from_user.id)

    # Если пользователь подписан
    if user_channel_status.status != 'left':
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        is_exist = cursor.execute(f"SELECT id FROM users WHERE id={callback.from_user.id}").fetchone()
        if not is_exist:
            cursor.execute(f"INSERT INTO users (id, card_time, random_time, luckyshot_time, clutch_time, quiz_done, season_score, "
                           f"full_score, chances, status) VALUES ('{callback.from_user.id}', '', '', '', '', '', '', '', 6, 'active');")
            cursor.execute(f"INSERT INTO indexes (user_id)"
                           f" VALUES ('{callback.from_user.id}');")
        conn.commit()
        cursor.close()
        await callback.message.delete()
        await callback.message.answer(menu_text, reply_markup=main_menu_kb)

    # Если пользователь больше не в канале
    else:
        await callback.message.delete()
        await callback.message.answer('<b>Для продолжения игры необходимо подписаться на наш канал</b>✅', reply_markup=channel_ikb, parse_mode="HTML")

# Игра в кубик
async def random(callback: types.CallbackQuery):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    click_date = cursor.execute(f"SELECT random_time FROM users WHERE id='{callback.from_user.id}'").fetchone()[0]
    # Получение времени последнего нажатия
    if click_date != '':
        t = (list(map(int, click_date.split()[0].split("-"))), list(map(int, click_date.split()[1].split("."))))
        click_date = datetime.datetime(t[0][0], t[0][1], t[0][2], t[1][0], t[1][1], t[1][2])
    today = datetime.datetime.today()

    # Если время последнего действия больше минимального
    if click_date == '' or today - datetime.timedelta(5) > click_date:
        cursor.execute(f"UPDATE users SET random_time = '{today.strftime('%Y-%m-%d %H.%M.%S')}' WHERE id='{callback.from_user.id}'")
        conn.commit()
        data = await bot.send_dice(callback.message.chat.id, emoji='🎲')
        time.sleep(4)
        form = "попытки"
        match data.dice.value:
            case 1:
                form = "попытку"
            case 5:
                form = "попыток"

        await callback.message.answer(f"Ты получаешь {data.dice.value} {form} 🎉!!!")

        chances = cursor.execute(f"SELECT chances FROM users WHERE id='{callback.from_user.id}'").fetchone()[0]
        cursor.execute(f"UPDATE users SET chances='{chances + data.dice.value}' WHERE id={callback.from_user.id}")
        conn.commit()
        cursor.close()
    else:
        remains = str(datetime.timedelta(5) - (today - click_date)).split(", ")
        days, timee = remains[0].split()[0], remains[1].split(":")
        await callback.message.answer(f"⏳ К сожалению, не прошло достаточно времени! Ты сможешь снова сыграть в игру через {days} дн. {timee[0]} ч. {timee[1]} мин.")
        cursor.close()

# Заброс в кольцо
async def lucky_shot(callback: types.CallbackQuery):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    click_date = cursor.execute(f"SELECT luckyshot_time FROM users WHERE id='{callback.from_user.id}'").fetchone()[0]

    # Получение времени последнего нажатия
    if click_date != '':
        t = (list(map(int, click_date.split()[0].split("-"))), list(map(int, click_date.split()[1].split("."))))
        click_date = datetime.datetime(t[0][0], t[0][1], t[0][2], t[1][0], t[1][1], t[1][2])
    today = datetime.datetime.today()

    # Если время последнего действия больше минимального
    if click_date == '' or today - datetime.timedelta(1) > click_date:
        cursor.execute(f"UPDATE users SET luckyshot_time = '{today.strftime('%Y-%m-%d %H.%M.%S')}' WHERE id='{callback.from_user.id}'")
        conn.commit()
        data = await bot.send_dice(callback.message.chat.id, emoji='🏀')
        time.sleep(4.5)
        if data.dice.value < 4:
            await callback.message.answer(f'🚫 Ты промахнулся, приходи в следующий раз.')
        else:
            await callback.message.answer(f'💥 Есть попадание! Ты получаешь дополнительную попытку.')
            chances = cursor.execute(f"SELECT chances FROM users WHERE id='{callback.from_user.id}'").fetchone()[0]
            cursor.execute(f"UPDATE users SET chances='{chances + 1}' WHERE id={callback.from_user.id}")
            conn.commit()
            cursor.close()
    else:
        remains = str(datetime.timedelta(1) - (today - click_date)).split(":")
        await callback.message.answer(f"⏳ К сожалению, не прошло достаточно времени! Ты сможешь снова сыграть в игру через {remains[0]} ч. {remains[1]} мин.")
        cursor.close()

# Квиз
async def quiz(callback: types.CallbackQuery, state: FSMContext):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    quiz_status = cursor.execute(f"SELECT quiz_done FROM users WHERE id={callback.from_user.id}").fetchone()[0]
    if quiz_status != "done":
        if cursor.execute("select count(*) from quiz").fetchone()[0] != 0:
            question, answers = cursor.execute(f"SELECT question FROM quiz").fetchone()[0], cursor.execute(f"SELECT variant_a, variant_b, variant_c, variant_d FROM quiz").fetchone()
            kb = ReplyKeyboardMarkup(keyboard=[
                                [KeyboardButton(text=f"{answers[0]}"), KeyboardButton(text=f"{answers[1]}")],
                                [KeyboardButton(text=f"{answers[2]}"), KeyboardButton(text=f"{answers[3]}")],
                                [KeyboardButton(text="В меню")]], resize_keyboard=True)

            await callback.message.answer(f"<b>{question.capitalize()}</b>\n\nВыберите правильный вариант ответа:", reply_markup=kb, parse_mode="HTML")
            await state.set_state(GetAnswer.ANSWER)
            cursor.close()

        else:
            await callback.message.answer("Скоро мы добавим новый вопрос")
            cursor.close()
    else:
        await callback.message.answer("Вы уже отвечали на квиз. Скоро мы добавим новый вопрос")
        cursor.close()


# Подтверждение выхода нового вопроса для квиза
async def confirm_quiz(callback: types.CallbackQuery, state: FSMContext):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    data = await state.get_data()

    cursor.execute("DELETE FROM quiz")
    cursor.execute("UPDATE users SET quiz_done=NULL")
    conn.commit()
    cursor.execute("INSERT INTO quiz (question, variant_a, variant_b, variant_c, variant_d, correct) VALUES "
                   f"('{data['question']}', '{data['first']}', '{data['second']}', '{data['third']}', '{data['fourth']}', '{int(data['correct'])}')")
    conn.commit()
    cursor.close()
    await state.clear()
    await callback.message.answer("Квиз обновлен!", reply_markup=admin_menu_kb)


# Не подтверждение выхода нового вопоса для квиза
async def disclaim_quiz(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Поробуем заново. Введите вопрос, который будет на следующем квизе:", reply_markup=cansel_kb)
    await state.set_state(Quiz.QUESTION)

async def next_card(callback: types.CallbackQuery):
    #TODO: поменять технологию получения списка всех кард
    if callback.data.split("_")[-1] == "card" or callback.data.split("_")[-1] == "trans":
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        user_card_ids = [i[0] for i in cursor.execute(f"SELECT card_id FROM collections WHERE user_id='{callback.from_user.id}'").fetchall()[::-1]]
        card_index = cursor.execute(f"SELECT card_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]
        if card_index + 1 < len(user_card_ids):
            cursor.execute(f"UPDATE indexes SET card_index=card_index+1 WHERE user_id='{callback.from_user.id}'")
            conn.commit()
            card_index += 1
            card_info = cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{user_card_ids[card_index]}'").fetchone()
            card = utils.Card(card_info)
            if callback.data.split("_")[-1] == "trans":
                cursor.execute(f"UPDATE indexes SET card_transfer_index={card.id} WHERE user_id='{callback.from_user.id}'")
                conn.commit()
                cursor.close()
                await draw_card(typ="base", tek=card_index + 1, all=len(user_card_ids), is_transfer=True, card=card, callback=callback)
            else:
                cursor.close()
                await draw_card(typ="base", tek=card_index + 1, all=len(user_card_ids), card=card, callback=callback)
        else:
            await callback.answer("Это последняя карточка в коллекции")
            cursor.close()

    elif callback.data.split("_")[-1] == "search":
        from data.forms import search_cards

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        card_search_index = cursor.execute(f"SELECT card_search_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]
        if card_search_index + 1 < len(search_cards):
            cursor.execute(f"UPDATE indexes SET card_search_index=card_search_index+1 WHERE user_id='{callback.from_user.id}'")
            conn.commit()
            card_search_index += 1
            card = utils.Card(search_cards[card_search_index])
            if callback.data.split("_")[-2] == "trans":
                cursor.execute(f"UPDATE indexes SET card_transfer_index={card.id} WHERE user_id='{callback.from_user.id}'")
                conn.commit()
                cursor.close()
                await draw_card(typ="search", tek=card_search_index + 1, is_transfer=True, all=len(search_cards), card=card, callback=callback)
            else:
                cursor.close()
                await draw_card(typ="search", tek=card_search_index + 1, all=len(search_cards), card=card, callback=callback)
        else:
            cursor.close()
            await callback.answer("Это последняя карточка")

    elif callback.data.split("_")[-1] == "rank":
        from data.utils import search_cards
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        card_rank_index = cursor.execute(f"SELECT card_rank_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]
        if card_rank_index + 1 < len(search_cards):
            cursor.execute(f"UPDATE indexes SET card_rank_index=card_rank_index+1 WHERE user_id='{callback.from_user.id}'")
            conn.commit()
            cursor.close()
            card_rank_index += 1
            card = utils.Card(search_cards[card_rank_index])
            if callback.data.split("_")[-2] == "trans":
                cursor.execute(f"UPDATE indexes SET card_transfer_index={card.id} WHERE user_id='{callback.from_user.id}'")
                conn.commit()
                cursor.close()
                await draw_card(typ="rank", tek=card_rank_index + 1, all=len(search_cards), is_transfer=True, card=card,
                                callback=callback)
            else:
                cursor.close()
                await draw_card(typ="rank", tek=card_rank_index + 1, all=len(search_cards), card=card,
                                callback=callback)
        else:
            cursor.close()
            await callback.answer("Это последняя карточка")

    elif callback.data.split("_")[-1] == "team":
        from data.forms import team_cards
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        card_team_index = cursor.execute(f"SELECT card_team_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]

        if card_team_index + 1 < len(team_cards):
            cursor.execute(f"UPDATE indexes SET card_team_index=card_team_index+1 WHERE user_id='{callback.from_user.id}'")
            conn.commit()
            cursor.close()
            card_team_index += 1
            card = utils.Card(team_cards[card_team_index])
            await draw_card(typ="team", tek=card_team_index + 1, all=len(team_cards), card=card,
                            callback=callback)
        else:
            cursor.close()
            await callback.answer("Это последняя карточка")


async def prev_card(callback: types.CallbackQuery):
    if callback.data.split("_")[-1] == "card" or callback.data.split("_")[-1] == "trans":
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        user_card_ids = [i[0] for i in cursor.execute(f"SELECT card_id FROM collections WHERE user_id='{callback.from_user.id}'").fetchall()[::-1]]
        card_index = cursor.execute(f"SELECT card_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]
        if card_index - 1 >= 0:
            cursor.execute(f"UPDATE indexes SET card_index=card_index-1 WHERE user_id='{callback.from_user.id}'")
            conn.commit()
            card_index -= 1
            card_info = cursor.execute(
                f"SELECT id, player, team, rank, score FROM cards WHERE id='{user_card_ids[card_index]}'").fetchone()
            card = utils.Card(card_info)
            if callback.data.split("_")[-1] == "trans":
                cursor.execute(
                    f"UPDATE indexes SET card_transfer_index={card.id} WHERE user_id='{callback.from_user.id}'")
                conn.commit()
                cursor.close()
                await draw_card(typ="base", tek=card_index + 1, all=len(user_card_ids), is_transfer=True, card=card, callback=callback)
            else:
                cursor.close()
                await draw_card(typ="base", tek=card_index + 1, all=len(user_card_ids), card=card, callback=callback)
        else:
            cursor.close()
            await callback.answer("Это первая карточка в коллекции")

    elif callback.data.split("_")[-1] == "search":
        from data.forms import search_cards
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        card_search_index = cursor.execute(f"SELECT card_search_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]
        if card_search_index - 1 >= 0:
            cursor.execute(f"UPDATE indexes SET card_search_index=card_search_index-1 WHERE user_id='{callback.from_user.id}'")
            conn.commit()
            card_search_index -= 1
            card = utils.Card(search_cards[card_search_index])
            if callback.data.split("_")[-2] == "trans":
                cursor.execute(f"UPDATE indexes SET card_transfer_index={card.id} WHERE user_id='{callback.from_user.id}'")
                conn.commit()
                cursor.close()
                await draw_card(typ="search", tek=card_search_index + 1, is_transfer=True, all=len(search_cards), card=card, callback=callback)
            else:
                cursor.close()
                await draw_card(typ="search", tek=card_search_index + 1, all=len(search_cards), card=card, callback=callback)
        else:
            cursor.close()
            await callback.answer("Это первая карточка")

    elif callback.data.split("_")[-1] == "rank":
        from data.utils import search_cards
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        card_rank_index = cursor.execute(f"SELECT card_rank_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]
        if card_rank_index - 1 >= 0:
            cursor.execute(f"UPDATE indexes SET card_rank_index=card_rank_index-1 WHERE user_id='{callback.from_user.id}'")
            conn.commit()
            card_rank_index -= 1
            card = utils.Card(search_cards[card_rank_index])
            if callback.data.split("_")[-2] == "trans":
                cursor.execute(f"UPDATE indexes SET card_transfer_index={card.id} WHERE user_id='{callback.from_user.id}'")
                conn.commit()
                cursor.close()
                await draw_card(typ="rank", tek=card_rank_index + 1, all=len(search_cards), is_transfer=True, card=card,
                                callback=callback)
            else:
                cursor.close()
                await draw_card(typ="rank", tek=card_rank_index + 1, all=len(search_cards), card=card,
                                callback=callback)
        else:
            cursor.close()
            await callback.answer("Это первая карточка")

    elif callback.data.split("_")[-1] == "team":
        from data.forms import team_cards
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        card_team_index = cursor.execute(f"SELECT card_team_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]
        if card_team_index - 1 >= 0:
            cursor.execute(f"UPDATE indexes SET card_team_index=card_team_index-1 WHERE user_id='{callback.from_user.id}'")
            conn.commit()
            cursor.close()
            card_team_index -= 1
            card = utils.Card(team_cards[card_team_index])
            await draw_card(typ="team", tek=card_team_index + 1, all=len(team_cards), card=card,
                            callback=callback)
        else:
            cursor.close()
            await callback.answer("Это первая карточка")


async def first_card(callback: types.CallbackQuery):
    if callback.data.split("_")[-1] == "card" or callback.data.split("_")[-1] == "trans":
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        card_index = cursor.execute(f"SELECT card_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]
        if card_index != 0:
            cursor.execute(f"UPDATE indexes SET card_index=0 WHERE user_id='{callback.from_user.id}'")
            conn.commit()
            user_card_id = cursor.execute(f"SELECT card_id FROM collections WHERE user_id='{callback.from_user.id}'").fetchall()[::-1][0][0]
            length = cursor.execute(f"SELECT COUNT(card_id) FROM collections WHERE user_id='{callback.from_user.id}'").fetchone()[0]
            card_info = cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{user_card_id}'").fetchone()
            card = utils.Card(card_info)
            if callback.data.split("_")[-1] == "trans":
                cursor.execute(f"UPDATE indexes SET card_transfer_index={card.id} WHERE user_id='{callback.from_user.id}'")
                conn.commit()
                cursor.close()
                await draw_card(typ="base", tek=1, all=length, is_transfer=True, card=card, callback=callback)
            else:
                cursor.close()
                await draw_card(typ="base", tek=1, all=length, card=card, callback=callback)
        else:
            cursor.close()
            await callback.answer("Это последняя карта, добавленная в вашу коллекцию")

    elif callback.data.split("_")[-1] == "search":
        from data.forms import search_cards
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        card_search_index = cursor.execute(f"SELECT card_search_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]
        if card_search_index != 0:
            cursor.execute(f"UPDATE indexes SET card_search_index=0 WHERE user_id='{callback.from_user.id}'")
            conn.commit()
            card_search_index = 0
            card = utils.Card(search_cards[card_search_index])
            if callback.data.split("_")[-2] == "trans":
                cursor.execute(
                    f"UPDATE indexes SET card_transfer_index={card.id} WHERE user_id='{callback.from_user.id}'")
                conn.commit()
                cursor.close()
                await draw_card(typ="search", tek=card_search_index + 1, is_transfer=True, all=len(search_cards), card=card, callback=callback)
            else:
                cursor.close()
                await draw_card(typ="search", tek=card_search_index + 1, all=len(search_cards), card=card, callback=callback)
        else:
            cursor.close()
            await callback.answer("Это последняя карта, добавленная в вашу коллекцию")

    elif callback.data.split("_")[-1] == "rank":
        from data.utils import search_cards
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        card_rank_index = cursor.execute(f"SELECT card_rank_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]
        if card_rank_index != 0:
            cursor.execute(f"UPDATE indexes SET card_rank_index=0 WHERE user_id='{callback.from_user.id}'")
            conn.commit()
            card_rank_index = 0
            card = utils.Card(search_cards[card_rank_index])
            if callback.data.split("_")[-2] == "trans":
                cursor.execute(f"UPDATE indexes SET card_transfer_index={card.id} WHERE user_id='{callback.from_user.id}'")
                conn.commit()
                cursor.close()
                await draw_card(typ="rank", tek=card_rank_index + 1, all=len(search_cards), is_transfer=True, card=card,
                                callback=callback)
            else:
                cursor.close()
                await draw_card(typ="rank", tek=card_rank_index + 1, all=len(search_cards), card=card,
                                callback=callback)
        else:
            cursor.close()
            await callback.answer("Это последняя карта, добавленная в вашу коллекцию")

    elif callback.data.split("_")[-1] == "team":
        from data.forms import team_cards
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        card_team_index = cursor.execute(f"SELECT card_team_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]
        if card_team_index != 0:
            cursor.execute(f"UPDATE indexes SET card_team_index=0 WHERE user_id='{callback.from_user.id}'")
            conn.commit()
            cursor.close()
            card_team_index = 0
            card = utils.Card(team_cards[card_team_index])
            await draw_card(typ="team", tek=card_team_index + 1, all=len(team_cards), card=card,
                            callback=callback)
        else:
            cursor.close()
            await callback.answer("Это последняя карта, добавленная в вашу коллекцию")

async def last_card(callback: types.CallbackQuery):
    if callback.data.split("_")[-1] == "card" or callback.data.split("_")[-1] == "trans":
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        user_card_id = cursor.execute(f"SELECT card_id FROM collections WHERE user_id='{callback.from_user.id}'").fetchall()[::-1]
        card_index = cursor.execute(f"SELECT card_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]
        if card_index != len(user_card_id) - 1:
            cursor.execute(f"UPDATE indexes SET card_index='{len(user_card_id) - 1}' WHERE user_id='{callback.from_user.id}'")
            conn.commit()
            card_index = len(user_card_id) - 1
            length = cursor.execute(f"SELECT COUNT(card_id) FROM collections WHERE user_id='{callback.from_user.id}'").fetchone()[0]
            card_info = cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{user_card_id[card_index][0]}'").fetchone()
            card = utils.Card(card_info)
            if callback.data.split("_")[-1] == "trans":
                cursor.execute(f"UPDATE indexes SET card_transfer_index={card.id} WHERE user_id='{callback.from_user.id}'")
                conn.commit()
                cursor.close()
                await draw_card(typ="base", tek=card_index + 1, is_transfer=True, all=length, card=card, callback=callback)
            else:
                cursor.close()
                await draw_card(typ="base", tek=card_index+1, all=length, card=card, callback=callback)
        else:
            cursor.close()
            await callback.answer("Это первая карта, добавленная в вашу коллекцию")

    elif callback.data.split("_")[-1] == "search":
        from data.forms import search_cards
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        card_search_index = cursor.execute(f"SELECT card_search_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]

        if (card_search_index != len(search_cards) - 1) and len(search_cards) != 1:
            cursor.execute(f"UPDATE indexes SET card_search_index='{len(search_cards) - 1}' WHERE user_id='{callback.from_user.id}'")
            conn.commit()
            card_search_index = len(search_cards) - 1
            card = utils.Card(search_cards[card_search_index])
            if callback.data.split("_")[-2] == "trans":
                cursor.execute(f"UPDATE indexes SET card_transfer_index={card.id} WHERE user_id='{callback.from_user.id}'")
                conn.commit()
                cursor.close()
                await draw_card(typ="search", tek=card_search_index + 1, is_transfer=True, all=len(search_cards), card=card, callback=callback)
            else:
                cursor.close()
                await draw_card(typ="search", tek=card_search_index + 1, all=len(search_cards), card=card, callback=callback)
        else:
            cursor.close()
            await callback.answer("Это первая карта, добавленная в вашу коллекцию")

    elif callback.data.split("_")[-1] == "rank":
        from data.utils import search_cards
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        card_rank_index = cursor.execute(f"SELECT card_rank_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]

        if (card_rank_index != len(search_cards) - 1) and len(search_cards) != 1:
            cursor.execute(f"UPDATE indexes SET card_rank_index='{len(search_cards) - 1}' WHERE user_id='{callback.from_user.id}'")
            conn.commit()
            card_rank_index = len(search_cards) - 1
            card = utils.Card(search_cards[card_rank_index])
            if callback.data.split("_")[-2] == "trans":
                cursor.execute(f"UPDATE indexes SET card_transfer_index={card.id} WHERE user_id='{callback.from_user.id}'")
                conn.commit()
                cursor.close()
                await draw_card(typ="rank", tek=card_rank_index + 1, all=len(search_cards), is_transfer=True, card=card,
                                callback=callback)
            else:
                cursor.close()
                await draw_card(typ="rank", tek=card_rank_index + 1, all=len(search_cards), card=card,
                                callback=callback)
        else:
            cursor.close()
            await callback.answer("Это первая карта, добавленная в вашу коллекцию")

    elif callback.data.split("_")[-1] == "team":
        from data.forms import team_cards
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        card_team_index = cursor.execute(f"SELECT card_team_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]

        if (card_team_index != len(team_cards) - 1) and len(team_cards) != 1:
            cursor.execute(f"UPDATE indexes SET card_team_index='{len(team_cards) - 1}' WHERE user_id='{callback.from_user.id}'")
            conn.commit()
            cursor.close()
            card_team_index = len(team_cards) - 1
            card = utils.Card(team_cards[card_team_index])
            print(card_team_index + 1)
            await draw_card(typ="team", tek=card_team_index + 1, all=len(team_cards), card=card,
                            callback=callback)
        else:
            await callback.answer("Это первая карта, добавленная в вашу коллекцию")


async def to_collection(callback: types.CallbackQuery):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(f"UPDATE indexes SET card_index=0 WHERE user_id='{callback.from_user.id}'")
    conn.commit()
    await callback.message.delete()
    user_card_id = cursor.execute(f"SELECT card_id FROM collections WHERE user_id='{callback.from_user.id}'").fetchall()[::-1][0][0]
    length = cursor.execute(f"SELECT COUNT(card_id) FROM collections WHERE user_id='{callback.from_user.id}'").fetchone()[0]
    card_info = cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{user_card_id}'").fetchone()
    cursor.close()
    card = utils.Card(card_info)
    await draw_card(typ="base", tek=1, all=length, card=card, callback=callback)

async def search(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📝 Введи никнейм игрока, которого ты хочешь найти в своей коллекции:")
    if callback.data.split("_")[-1] != "trans":
        await state.set_state(Search.NICKNAME)
    else:
        await state.set_state(Search.NICKNAME_TRANS)


async def by_rank(callback: types.CallbackQuery):
    if callback.data.split("_")[-1] == "trans":
        await callback.message.answer(
            "⚜️ Здесь ты можешь отфильтровать карты из своей коллекции по званию. Выбери интересующее звание из списка ниже:",
            reply_markup=ranks_ikb_trans)
    else:
        await callback.message.answer(
            "⚜️ Здесь ты можешь отфильтровать карты из своей коллекции по званию. Выбери интересующее звание из списка ниже:",
            reply_markup=ranks_ikb)

async def sort_rank(callback: types.CallbackQuery):
    total = ""
    await callback.message.delete()
    t = False
    if callback.data.split("_")[-1] == "trans":
        c = callback.data[:-6]
        t = True
    else:
        c = callback.data

    match c:
        case "rank_silver":
            total = "Сильвер"
        case "rank_gold_nova":
            total = "Звезда"
        case "rank_ak":
            total = "Калаш"
        case "rank_ak_wreaths":
            total = "Калаш с венками"
        case "rank_two_ak":
            total = "Два калаша"
        case "rank_big_star":
            total = "Биг стар"
        case "rank_berkut":
            total = "Беркут"
        case "rank_lem":
            total = "Лем"
        case "rank_suprim":
            total = "Суприм"
        case "rank_global":
            total = "Глобал"
    await sort_by_rank(total, callback, trans=t)


async def by_team(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "👥 Здесь ты можешь отфильтровать карты из своей коллекции по команде. Введи название команды ниже:")
    await state.set_state(Team.TEAM)

async def create_transfer(callback: types.CallbackQuery):
    await callback.message.answer(f"♻️ Здесь ты можешь обменяться картами с другими игроками! "
                                  f"Выбери карту, которую хочешь обменять. Для удобства можешь "
                                  "отфильтровать свои карты по определенному критерию.")

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(f"UPDATE indexes SET card_index=0 WHERE user_id='{callback.from_user.id}'")
    conn.commit()
    try:
        user_card_id = cursor.execute(f"SELECT card_id FROM collections WHERE user_id='{callback.from_user.id}'").fetchall()[::-1][0][0]
        length = cursor.execute(f"SELECT COUNT(card_id) FROM collections WHERE user_id='{callback.from_user.id}'").fetchone()[0]
        card_info = cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{user_card_id}'").fetchone()
        cursor.execute(f"UPDATE indexes SET card_transfer_index='{card_info[0]}' WHERE user_id='{callback.from_user.id}'")
        conn.commit()
        cursor.close()
        if len(card_info) == 5:
            card = utils.Card(card_info)
            await draw_card(typ="base", tek=1, is_transfer=True, all=length, card=card, message=callback.message)
        else:
            await callback.message.answer("Кажется, в твоей коллекции нет карт ❌")
    except IndexError as e:
        await callback.message.answer("Кажется, в твоей коллекции нет карт ❌")


async def add_card(callback: types.CallbackQuery, state: FSMContext):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    is_answer = cursor.execute(f"SELECT status FROM transfers WHERE user_id_2='{callback.from_user.id}' AND status='answer'").fetchone()
    if not is_answer:
        cursor.close()
        await callback.message.answer("📝 Карта выбрана, укажи ID игрока, с которым ты бы хотел совершить обмен")
        await state.set_state(TransferID.ID)
    else:
        id = cursor.execute(f"SELECT user_id_1 FROM transfers WHERE user_id_2='{callback.from_user.id}' AND status='answer'").fetchone()[0]
        # Вторая карта
        card_id = cursor.execute(f"SELECT card_transfer_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]
        print(card_id)
        cursor.execute(f"UPDATE transfers SET card_id_2='{card_id}' WHERE user_id_2='{callback.from_user.id}' AND status='answer'").fetchone()

        card_info = cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{card_id}'").fetchone()
        print(card_info)
        transfer_card = utils.Card(card_info)

        text = f"""🔤 Никнейм: <b>{transfer_card.name}</b> 

🕹 Команда: <b>{transfer_card.team}</b>

🎖 Звание: <b>{transfer_card.rank}</b>

🔢 Очки: <b>{transfer_card.score}</b>"""

        photo = FSInputFile(path=f"./cards/{transfer_card.id}.webp")
        text = f"<b>👀 Игрок {callback.from_user.id} прислал ответ на твой запрос на обмен. Посмотри, что он предлагает:</b>\n\n{text}"

        rowid = cursor.execute(f"SELECT id FROM collections WHERE user_id='{callback.from_user.id}' AND card_id='{transfer_card.id}'").fetchall()[::-1][0]
        cursor.execute(f"DELETE FROM collections WHERE id='{rowid[0]}'")
        conn.commit()
        cursor.close()

        accept_transfer_ikb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять",
                    callback_data=f"last_accept_{callback.from_user.id}_{card_id}"
                )],
            [InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"last_decline_{callback.from_user.id}_{card_id}"
            )]
        ], resize_keyboard=True)

        await bot.send_photo(chat_id=int(id), photo=photo, caption=text, parse_mode="HTML", reply_markup=accept_transfer_ikb)
        await callback.message.answer("✅ Ответный запрос на обмен игроку никнейм отправлен")


async def accept_transfer(callback: types.CallbackQuery):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    await callback.message.answer("♻️ Выбери карту, которую хочешь обменять. Для удобства можешь отфильтровать свои карты по определенному критерию.")

    user_card_id = cursor.execute(f"SELECT card_id FROM collections WHERE user_id='{callback.from_user.id}'").fetchall()[::-1][0][0]
    print(user_card_id)
    card_info = cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{user_card_id}'").fetchone()
    cursor.execute(f"UPDATE transfers SET status='answer' WHERE user_id_1='{callback.message.caption.split()[2]}' AND user_id_2='{callback.from_user.id}' AND status='active'").fetchone()
    conn.commit()
    cursor.close()
    card = utils.Card(card_info)
    await draw_card(typ="base", tek=1, is_transfer=True, all=1, card=card, callback=callback, send=True)


async def decline_transfer(callback: types.CallbackQuery):
    card_id = int(callback.data.split("_")[-1])
    user_id = callback.message.caption.split()[2]
    conn = sqlite3.connect('./database.db')
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO collections ('user_id', 'card_id') VALUES ('{user_id}', '{card_id}')")
    conn.commit()
    cursor.execute(f"UPDATE transfers SET status='decline' WHERE user_id_2='{callback.from_user.id}' AND user_id_1='{user_id}' AND card_id_1='{card_id}' AND status='active'")
    conn.commit()
    await callback.message.answer(f"❌ Ты отклонил запрос на обмен от игрока c ID {user_id}")
    await bot.send_message(chat_id=int(user_id), text=f"❌ Игрок c ID {callback.from_user.id} отклонил твой запрос на обмен")
    cursor.close()


async def last_accept(callback: types.CallbackQuery):
    user_id_2, card_id_2 = callback.data.split("_")[-2], callback.data.split("_")[-1]
    conn = sqlite3.connect('./database.db')
    cursor = conn.cursor()
    card_id_1 = cursor.execute(f"SELECT card_id_1 FROM transfers WHERE user_id_2='{user_id_2}' AND user_id_1='{callback.from_user.id}' AND card_id_2='{int(card_id_2)}' AND status='answer'").fetchone()[0]
    cursor.execute(f"INSERT INTO collections (user_id, card_id) VALUES ('{callback.from_user.id}', '{card_id_2}')")
    conn.commit()
    cursor.execute(f"INSERT INTO collections (user_id, card_id) VALUES ('{user_id_2}', '{card_id_1}')")
    conn.commit()
    cursor.execute(f"UPDATE transfers SET status='finished' WHERE user_id_2='{user_id_2}' AND user_id_1='{callback.from_user.id}' AND card_id_2='{card_id_2}' AND status='answer'")
    conn.commit()
    cursor.close()
    await bot.send_message(chat_id=int(user_id_2), text=f"🎉 Поздравляем тебя с успешным обменом с игроком {callback.from_user.id}! Наслаждайся своей новой картой!", parse_mode="HTML")
    await callback.message.answer(f"🎉 Поздравляем тебя с успешным обменом с игроком {user_id_2}! Наслаждайся своей новой картой!")


async def last_decline(callback: types.CallbackQuery):
    user_id_2, card_id_2 = callback.data.split("_")[-2], callback.data.split("_")[-1]
    conn = sqlite3.connect('./database.db')
    cursor = conn.cursor()
    card_id_1 = cursor.execute(f"SELECT card_id_1 FROM transfers WHERE user_id_2='{user_id_2}' AND user_id_1='{callback.from_user.id}' AND card_id_2='{int(card_id_2)}' AND status='answer'").fetchone()[0]
    cursor.execute(f"INSERT INTO collections ('user_id', 'card_id') VALUES ('{callback.from_user.id}', '{card_id_1}')")
    conn.commit()
    cursor.execute(f"INSERT INTO collections ('user_id', 'card_id') VALUES ('{user_id_2}', '{card_id_2}')")
    conn.commit()
    cursor.execute(f"UPDATE transfers SET status='decline' WHERE user_id_2='{user_id_2}' AND user_id_1='{callback.from_user.id}' AND card_id_1='{card_id_1}' AND card_id_2='{card_id_2}' AND status='answer'")
    conn.commit()
    await callback.message.answer(f"❌ Ты отклонил запрос на обмен от игрока c ID {user_id_2}")
    await bot.send_message(chat_id=int(user_id_2), text=f"❌ Игрок c ID {callback.from_user.id} отклонил твое предложение на обмен")
    cursor.close()

async def tek_transfers(callback: types.CallbackQuery):
    # TODO
    conn = sqlite3.connect('./database.db')
    cursor = conn.cursor()
    has_transfer = cursor.execute(f"SELECT * FROM transfers WHERE user_id_1='{callback.from_user.id}' AND status='active'").fetchone()

    if has_transfer:
        await callback.message.answer("🔜 Здесь ты можешь посмотреть свои текущие обмены!")
        tek_transfer_ikb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"tek_prev"
                ), InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"tek_next"
                )],
            [InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=f"tek_decline"
            )]
        ], resize_keyboard=True)
        cursor.execute(f"UPDATE indexes SET card_transfer_index='0' WHERE user_id={callback.from_user.id}")
        conn.commit()
        card = utils.Card(cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{has_transfer[2]}'").fetchone())
        cursor.close()

        text = f"""<b>ОБМЕН C ИГРОКОМ <code>{has_transfer[1]}</code></b>
        
🔤 Никнейм: <b>{card.name}</b> 

🕹 Команда: <b>{card.team}</b>

🎖 Звание: <b>{card.rank}</b>

🔢 Очки: <b>{card.score}</b>"""

        photo = FSInputFile(path=f"./cards/{card.id}.webp")

        await callback.message.answer_photo(photo, caption=text, parse_mode="HTML", reply_markup=tek_transfer_ikb)


    else:
        await callback.message.answer(f"🗿 У тебя нет текущих обменов")
        cursor.close()

async def tek_next(callback: types.CallbackQuery):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    transfer_card_ids = cursor.execute(f"SELECT card_id_1, user_id_2 FROM transfers WHERE user_id_1='{callback.from_user.id}' AND status='active'").fetchall()
    card_index = cursor.execute(f"SELECT card_transfer_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]
    if card_index + 1 < len(transfer_card_ids):
        cursor.execute(f"UPDATE indexes SET card_transfer_index=card_transfer_index+1 WHERE user_id='{callback.from_user.id}'")
        conn.commit()
        card_index += 1
        tek_transfer_ikb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"tek_prev"
                ), InlineKeyboardButton(
                text="➡️",
                callback_data=f"tek_next"
            )],
            [InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=f"tek_decline"
            )]
        ], resize_keyboard=True)
        card = utils.Card(cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{transfer_card_ids[card_index][0]}'").fetchone())
        cursor.close()

        text = f"""<b>ОБМЕН C ИГРОКОМ <code>{transfer_card_ids[card_index][1]}</code></b>

🔤 Никнейм: <b>{card.name}</b> 

🕹 Команда: <b>{card.team}</b>

🎖 Звание: <b>{card.rank}</b>

🔢 Очки: <b>{card.score}</b>"""

        photo = FSInputFile(path=f"./cards/{card.id}.webp")

        await callback.message.edit_media(InputMediaPhoto(media=photo, caption=text), parse_mode="HTML", reply_markup=tek_transfer_ikb)
    else:
        cursor.close()
        await callback.answer("Это последний обмен, ожидающий встречного предложения.")

async def tek_prev(callback: types.CallbackQuery):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    transfer_card_ids = cursor.execute(f"SELECT card_id_1, user_id_2 FROM transfers WHERE user_id_1='{callback.from_user.id}' AND status='active'").fetchall()
    card_index = cursor.execute(f"SELECT card_transfer_index FROM indexes WHERE user_id='{callback.from_user.id}'").fetchone()[0]
    if card_index - 1 >= 0:
        cursor.execute(f"UPDATE indexes SET card_transfer_index=card_transfer_index-1 WHERE user_id='{callback.from_user.id}'")
        conn.commit()
        card_index -= 1
        tek_transfer_ikb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"tek_prev"
                ), InlineKeyboardButton(
                text="➡️",
                callback_data=f"tek_next"
            )],
            [InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=f"tek_decline"
            )]
        ], resize_keyboard=True)
        card = utils.Card(cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{transfer_card_ids[card_index][0]}'").fetchone())
        cursor.close()

        text = f"""<b>ОБМЕН C ИГРОКОМ <code>{transfer_card_ids[card_index][1]}</code></b>

🔤 Никнейм: <b>{card.name}</b> 

🕹 Команда: <b>{card.team}</b>

🎖 Звание: <b>{card.rank}</b>

🔢 Очки: <b>{card.score}</b>"""

        photo = FSInputFile(path=f"./cards/{card.id}.webp")

        await callback.message.edit_media(InputMediaPhoto(media=photo, caption=text), parse_mode="HTML", reply_markup=tek_transfer_ikb)
    else:
        cursor.close()
        await callback.answer("Это первый обмен, ожидающий встречного предложения.")


async def tek_decline(callback: types.CallbackQuery):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    user_id = callback.message.caption.split()[3]
    try:
        id = cursor.execute(f"SELECT card_id_1 FROM transfers WHERE user_id_1='{callback.from_user.id}' AND user_id_2='{user_id}' AND status='active'").fetchone()[0]
        cursor.execute(f"UPDATE transfers SET status='decline' WHERE user_id_1='{callback.from_user.id}' AND user_id_2='{user_id}' AND status='active'").fetchone()
        conn.commit()
        cursor.execute(f"INSERT INTO collections ('user_id', 'card_id') VALUES ('{callback.from_user.id}', '{id}')")
        conn.commit()
        cursor.close()
        await callback.message.delete()
        await callback.message.answer(f"🗑 Обмен с игроком {user_id} успешно отменен")
    except Exception as e:
        print(e)
        await callback.answer(f"Что-то пошло не так")


async def finished_transfers(callback: types.CallbackQuery):
    conn = sqlite3.connect('./database.db')
    cursor = conn.cursor()
    has_transfer = cursor.execute(f"SELECT * FROM transfers WHERE user_id_1='{callback.from_user.id}' AND status='finished'").fetchone()

    if has_transfer:
        text = "🆗 Здесь ты можешь посмотреть свои завершенные обмены."
        all_transfers = cursor.execute(f"SELECT user_id_2, card_id_1, card_id_2 FROM transfers WHERE user_id_1='{callback.from_user.id}' AND status='finished'").fetchall()
        data_1 = [cursor.execute(f"SELECT player, rank FROM cards WHERE id='{i[1]}'").fetchone() for i in all_transfers]
        data_2 = [cursor.execute(f"SELECT player, rank FROM cards WHERE id='{i[2]}'").fetchone() for i in all_transfers]
        for i in range(len(all_transfers)):
            text += f"\n\n{i + 1}. Ты получил <b>{data_2[i][0]} | {data_2[i][1]}</b> от игрока с ID <b><code>{all_transfers[i][0]}</code></b> в обмен на <b>{data_1[i][0]} | {data_1[i][1]}</b>"

        await callback.message.answer(text)
        cursor.close()

    else:
        await callback.message.answer(f"🗿 Ты еще не совершил ни одного обмена.")

async def donate(callback: types.CallbackQuery):
    await callback.message.answer('🌐 Выбери из списка необходимое количество внутриигровой валюты:')
