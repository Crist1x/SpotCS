from aiogram import types
import sqlite3

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from pyexpat.errors import messages

from config import CHANNEL_ID, menu_text
from data import utils
from data.forms import Quiz, GetAnswer, Search, Team
from data.utils import draw_card, sort_by_rank
from dispatcher import bot
import datetime

import time

from handlers.admin_actions import add_card
from keyboards.admin import cansel_kb, admin_menu_kb
from keyboards.general import channel_ikb, main_menu_kb, ranks_ikb

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

        await callback.message.answer(f"Вы полчаете {data.dice.value} {form}")

        chances = cursor.execute(f"SELECT chances FROM users WHERE id='{callback.from_user.id}'").fetchone()[0]
        cursor.execute(f"UPDATE users SET chances='{chances + data.dice.value}' WHERE id={callback.from_user.id}")
        conn.commit()
        cursor.close()
    else:
        remains = str(datetime.timedelta(5) - (today - click_date)).split(", ")
        days, timee = remains[0].split()[0], remains[1].split(":")
        await callback.message.answer(f"До следующей попытки осталось {days} дн. {timee[0]} ч. {timee[1]} мин.")
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
            await callback.message.answer(f'Вы не получаете попытку. Попробуйте завтра')
        else:
            await callback.message.answer(f'Поздравляю, вы получаете 1 дополнительную попытку')
            chances = cursor.execute(f"SELECT chances FROM users WHERE id='{callback.from_user.id}'").fetchone()[0]
            cursor.execute(f"UPDATE users SET chances='{chances + 1}' WHERE id={callback.from_user.id}")
            conn.commit()
            cursor.close()
    else:
        remains = str(datetime.timedelta(1) - (today - click_date)).split(":")
        await callback.message.answer(f"До следующей попытки осталось {remains[0]} ч. {remains[1]} мин.")
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


card_index = 0
card_search_index = 0
card_rank_index = 0
card_team_index = 0

async def next_card(callback: types.CallbackQuery):
    #TODO: поменять технологию получения списка всех кард
    if callback.data.split("_")[-1] == "card":
        global card_index
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        user_card_ids = [i[0] for i in cursor.execute(f"SELECT card_id FROM collections WHERE user_id='{callback.from_user.id}'").fetchall()[::-1]]
        if card_index + 1 < len(user_card_ids):
            card_index += 1
            card_info = cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{user_card_ids[card_index]}'").fetchone()
            cursor.close()
            card = utils.Card(card_info)
            await draw_card(typ="base", tek=card_index + 1, all=len(user_card_ids), card=card, callback=callback)
        else:
            await callback.answer("Это последняя карточка в коллекции")
            cursor.close()

    elif callback.data.split("_")[-1] == "search":
        from data.forms import search_cards
        global card_search_index

        if card_search_index + 1 < len(search_cards):
            card_search_index += 1
            card = utils.Card(search_cards[card_search_index])
            await draw_card(typ="search", tek=card_search_index + 1, all=len(search_cards), card=card, callback=callback)
        else:
            await callback.answer("Это последняя карточка")

    elif callback.data.split("_")[-1] == "rank":
        from data.utils import search_cards
        global card_rank_index
        if card_rank_index + 1 < len(search_cards):
            card_rank_index += 1
            card = utils.Card(search_cards[card_rank_index])
            await draw_card(typ="rank", tek=card_rank_index + 1, all=len(search_cards), card=card,
                            callback=callback)
        else:
            await callback.answer("Это последняя карточка")

    elif callback.data.split("_")[-1] == "team":
        from data.forms import team_cards
        global card_team_index
        if card_team_index + 1 < len(team_cards):
            card_team_index += 1
            card = utils.Card(team_cards[card_team_index])
            await draw_card(typ="team", tek=card_team_index + 1, all=len(team_cards), card=card,
                            callback=callback)
        else:
            await callback.answer("Это последняя карточка")


async def prev_card(callback: types.CallbackQuery):
    if callback.data.split("_")[-1] == "card":
        global card_index
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        user_card_ids = [i[0] for i in cursor.execute(
            f"SELECT card_id FROM collections WHERE user_id='{callback.from_user.id}'").fetchall()[::-1]]
        if card_index - 1 >= 0:
            card_index -= 1
            card_info = cursor.execute(
                f"SELECT id, player, team, rank, score FROM cards WHERE id='{user_card_ids[card_index]}'").fetchone()
            card = utils.Card(card_info)
            cursor.close()
            await draw_card(typ="base", tek=card_index + 1, all=len(user_card_ids), card=card, callback=callback)
        else:
            cursor.close()
            await callback.answer("Это первая карточка в коллекции")

    elif callback.data.split("_")[-1] == "search":
        from data.forms import search_cards
        global card_search_index

        if card_search_index - 1 >= 0:
            card_search_index -= 1
            card = utils.Card(search_cards[card_search_index])
            await draw_card(typ="search", tek=card_search_index + 1, all=len(search_cards), card=card, callback=callback)
        else:
            await callback.answer("Это первая карточка")

    elif callback.data.split("_")[-1] == "rank":
        from data.utils import search_cards
        global card_rank_index

        if card_rank_index - 1 >= 0:
            card_rank_index -= 1
            card = utils.Card(search_cards[card_rank_index])
            await draw_card(typ="rank", tek=card_rank_index + 1, all=len(search_cards), card=card,
                            callback=callback)
        else:
            await callback.answer("Это первая карточка")

    elif callback.data.split("_")[-1] == "team":
        from data.forms import team_cards
        global card_team_index
        if card_team_index - 1 >= 0:
            card_team_index -= 1
            card = utils.Card(team_cards[card_team_index])
            await draw_card(typ="team", tek=card_team_index + 1, all=len(team_cards), card=card,
                            callback=callback)
        else:
            await callback.answer("Это первая карточка")


async def first_card(callback: types.CallbackQuery):
    if callback.data.split("_")[-1] == "card":
        global card_index
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        if card_index != 0:
            card_index = 0
            user_card_id = cursor.execute(f"SELECT card_id FROM collections WHERE user_id='{callback.from_user.id}'").fetchall()[::-1][0][0]
            length = cursor.execute(f"SELECT COUNT(card_id) FROM collections WHERE user_id='{callback.from_user.id}'").fetchone()[0]
            card_info = cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{user_card_id}'").fetchone()
            cursor.close()
            card = utils.Card(card_info)
            await draw_card(typ="base", tek=1, all=length, card=card, callback=callback)
        else:
            cursor.close()
            await callback.answer("Это последняя карта, добавленная в вашу коллекцию")

    elif callback.data.split("_")[-1] == "search":
        from data.forms import search_cards
        global card_search_index

        if card_search_index != 0:
            card_search_index = 0
            card = utils.Card(search_cards[card_search_index])
            await draw_card(typ="search", tek=card_search_index + 1, all=len(search_cards), card=card, callback=callback)
        else:
            await callback.answer("Это последняя карта, добавленная в вашу коллекцию")

    elif callback.data.split("_")[-1] == "rank":
        from data.utils import search_cards
        global card_rank_index

        if card_rank_index != 0:
            card_rank_index = 0
            card = utils.Card(search_cards[card_rank_index])
            await draw_card(typ="rank", tek=card_rank_index + 1, all=len(search_cards), card=card,
                            callback=callback)
        else:
            await callback.answer("Это последняя карта, добавленная в вашу коллекцию")

    elif callback.data.split("_")[-1] == "team":
        from data.forms import team_cards
        global card_team_index
        if card_team_index != 0:
            card_team_index = 0
            card = utils.Card(team_cards[card_team_index])
            await draw_card(typ="team", tek=card_team_index + 1, all=len(team_cards), card=card,
                            callback=callback)
        else:
            await callback.answer("Это последняя карта, добавленная в вашу коллекцию")

async def last_card(callback: types.CallbackQuery):
    if callback.data.split("_")[-1] == "card":
        global card_index
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        user_card_id = cursor.execute(
            f"SELECT card_id FROM collections WHERE user_id='{callback.from_user.id}'").fetchall()[::-1]
        if card_index != len(user_card_id) - 1:
            card_index = len(user_card_id) - 1
            length = cursor.execute(f"SELECT COUNT(card_id) FROM collections WHERE user_id='{callback.from_user.id}'").fetchone()[0]
            card_info = cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{user_card_id[card_index][0]}'").fetchone()
            cursor.close()
            card = utils.Card(card_info)
            await draw_card(typ="base", tek=card_index+1, all=length, card=card, callback=callback)
        else:
            cursor.close()
            await callback.answer("Это первая карта, добавленная в вашу коллекцию")

    elif callback.data.split("_")[-1] == "search":
        from data.forms import search_cards
        global card_search_index
        if (card_search_index != len(search_cards) - 1) and len(search_cards) != 1:
            card_search_index = len(search_cards) - 1
            card = utils.Card(search_cards[card_search_index])
            await draw_card(typ="search", tek=card_search_index + 1, all=len(search_cards), card=card, callback=callback)
        else:
            await callback.answer("Это первая карта, добавленная в вашу коллекцию")

    elif callback.data.split("_")[-1] == "rank":
        from data.utils import search_cards
        global card_rank_index

        if (card_rank_index != len(search_cards) - 1) and len(search_cards) != 1:
            card_rank_index = len(search_cards) - 1
            card = utils.Card(search_cards[card_rank_index])
            await draw_card(typ="rank", tek=card_rank_index + 1, all=len(search_cards), card=card,
                            callback=callback)
        else:
            await callback.answer("Это первая карта, добавленная в вашу коллекцию")

    elif callback.data.split("_")[-1] == "team":
        from data.forms import team_cards
        global card_team_index
        if (card_team_index != len(team_cards) - 1) and len(team_cards) != 1:
            card_team_index = len(team_cards) - 1
            card = utils.Card(team_cards[card_team_index])
            print(card_team_index + 1)
            await draw_card(typ="team", tek=card_team_index + 1, all=len(team_cards), card=card,
                            callback=callback)
        else:
            await callback.answer("Это первая карта, добавленная в вашу коллекцию")


async def to_collection(callback: types.CallbackQuery):
    global card_index
    card_index = 0

    await callback.message.delete()

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    user_card_id = cursor.execute(f"SELECT card_id FROM collections WHERE user_id='{callback.from_user.id}'").fetchall()[::-1][0][0]
    length = cursor.execute(f"SELECT COUNT(card_id) FROM collections WHERE user_id='{callback.from_user.id}'").fetchone()[0]
    card_info = cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{user_card_id}'").fetchone()
    cursor.close()
    card = utils.Card(card_info)
    await draw_card(typ="base", tek=1, all=length, card=card, callback=callback)

async def search(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📝 Введи никнейм игрока, которого ты хочешь найти в своей коллекции:")
    await state.set_state(Search.NICKNAME)


async def by_rank(callback: types.CallbackQuery):
    await callback.message.answer(
        "⚜️ Здесь ты можешь отфильтровать карты из своей коллекции по званию. Выбери интересующее звание из списка ниже:",
        reply_markup=ranks_ikb)

async def sort_rank(callback: types.CallbackQuery):
    total = ""
    await callback.message.delete()
    match callback.data:
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

    await sort_by_rank(total, callback)


async def by_team(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "👥 Здесь ты можешь отфильтровать карты из своей коллекции по команде. Введи название команды ниже:")
    await state.set_state(Team.TEAM)

async def create_transfer(callback: types.CallbackQuery):
    global card_index
    await callback.message.answer("♻️ Здесь ты можешь обменяться картами с другими игроками! "
                                  "Выбери карту, которую хочешь обменять. Для удобства можешь "
                                  "отфильтровать свои карты по определенному критерию.")
    card_index = 0

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    user_card_id = \
    cursor.execute(f"SELECT card_id FROM collections WHERE user_id='{callback.from_user.id}'").fetchall()[::-1][0][0]
    length = \
    cursor.execute(f"SELECT COUNT(card_id) FROM collections WHERE user_id='{callback.from_user.id}'").fetchone()[0]
    card_info = cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{user_card_id}'").fetchone()
    cursor.close()
    if len(card_info) == 5:
        card = utils.Card(card_info)
        await draw_card(typ="transfer", tek=1, all=length, card=card, callback=callback)
    else:
        await callback.message.answer("Кажется, в твоей коллекции нет карт ❌")