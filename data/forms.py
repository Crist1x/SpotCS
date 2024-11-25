import sqlite3
from cgitb import handler
from idlelib.pyparse import trans
from logging import exception
from xml.sax import parse

from aiogram import types, Bot
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton

from data import utils
from data.utils import draw_card
from dispatcher import bot
from keyboards.admin import admin_menu_kb, confirm_quiz, currency_ikb
from keyboards.general import main_menu_kb
from os import listdir


class Quiz(StatesGroup):
    QUESTION = State()
    FIRST_V = State()
    SECOND_V = State()
    THIRD_V = State()
    FOURTH_V = State()
    CORRECT = State()

async def get_question(message: Message, state: FSMContext):
    await state.update_data(question=message.text)
    data = await state.get_data()
    if data["question"] != "Отмена":
        await message.answer("Напишите первый вариант ответа:")
        await state.set_state(Quiz.FIRST_V)
    else:
        await message.answer("Вы вернулись в меню", reply_markup=admin_menu_kb)
        await state.clear()

async def get_first(message: Message, state: FSMContext):
    await state.update_data(first=message.text)
    data = await state.get_data()
    if data["first"] != "Отмена":
        await message.answer("Напишите второй вариант ответа:")
        await state.set_state(Quiz.SECOND_V)
    else:
        await message.answer("Вы вернулись в меню", reply_markup=admin_menu_kb)
        await state.clear()

async def get_second(message: Message, state: FSMContext):
    await state.update_data(second=message.text)
    data = await state.get_data()
    if data["second"] != "Отмена":
        await message.answer("Напишите третий вариант ответа:")
        await state.set_state(Quiz.THIRD_V)
    else:
        await message.answer("Вы вернулись в меню", reply_markup=admin_menu_kb)
        await state.clear()

async def get_third(message: Message, state: FSMContext):
    await state.update_data(third=message.text)
    data = await state.get_data()
    if data["third"] != "Отмена":
        await message.answer("Напишите четвертый вариант ответа:")
        await state.set_state(Quiz.FOURTH_V)
    else:
        await message.answer("Вы вернулись в меню", reply_markup=admin_menu_kb)
        await state.clear()

async def get_fourth(message: Message, state: FSMContext):
    await state.update_data(fourth=message.text)
    data = await state.get_data()
    if data["fourth"] != "Отмена":
        await message.answer("Напишите правильный вариант ответа одной цифрой (1/2/3/4):")
        await state.set_state(Quiz.CORRECT)
    else:
        await message.answer("Вы вернулись в меню", reply_markup=admin_menu_kb)
        await state.clear()

async def get_correct(message: Message, state: FSMContext):
    await state.update_data(correct=message.text)
    data = await state.get_data()
    if data["correct"] != "Отмена":
        try:
            if 1 <= int(data["correct"]) <= 4:
                text = (f"Все верно?\n\n{data['question']}\nA) {data['first']}\nB) {data['second']}\nC) {data['third']}"
                        f"\nD) {data['fourth']}\nПравильный ответ: {data['correct']}")
                await message.answer(text, reply_markup=confirm_quiz)
            else:
                raise TypeError
        except exception as e:
            await message.answer("Напишите правильный вариант ответа одной цифрой (1/2/3/4):")
            await state.set_state(Quiz.CORRECT)
    else:
        await message.answer("Вы вернулись в меню", reply_markup=admin_menu_kb)
        await state.clear()


class GetAnswer(StatesGroup):
    ANSWER = State()

async def get_answer(message: Message, state: FSMContext):
    await state.update_data(answer=message.text)
    data = await state.get_data()
    await state.clear()
    conn = sqlite3.connect('./database.db')
    cursor = conn.cursor()
    answers = [str(i) for i in list(cursor.execute(f"SELECT variant_a, variant_b, variant_c, variant_d FROM quiz").fetchone())]

    if data["answer"] in answers:
        correct = cursor.execute(f"SELECT correct FROM quiz").fetchone()[0]
        cursor.execute(f"UPDATE users SET quiz_done='done' WHERE id={message.from_user.id}")

        if answers.index(data["answer"]) == correct - 1:
            await message.answer("✅ Поздравляем, ты дал верный ответ! Ты получаешь дополнительную попытку.", reply_markup=main_menu_kb)
            cursor.execute(f"UPDATE users SET chances = chances + 1 WHERE id={message.from_user.id}")
            conn.commit()
            cursor.close()
        else:
            await message.answer(f"<b>❌ К сожалению, ответ неверный.</b>\n\nПравильный ответ: {answers[correct-1]}", reply_markup=main_menu_kb, parse_mode="HTML")
            conn.commit()
            cursor.close()

    else:
        await message.answer("Вы вернулись в меню", reply_markup=main_menu_kb)
        cursor.close()
        await state.clear()


class Search(StatesGroup):
    NICKNAME = State()
    NICKNAME_TRANS = State()


async def get_nickname_temp(message: Message, state: FSMContext, is_trans=False):
    await state.update_data(nickname=message.text.strip())
    data = await state.get_data()
    nickname = data['nickname']
    await state.clear()

    conn = sqlite3.connect('./database.db')
    cursor = conn.cursor()
    length = cursor.execute(
        f"SELECT COUNT(cards.id) FROM cards, collections WHERE cards.id = collections.card_id AND LOWER(cards.player) = '{nickname.lower()}' AND collections.user_id='{message.from_user.id}'").fetchone()[0]
    cards = cursor.execute(
        f"SELECT cards.id, cards.player, cards.team, cards.rank, cards.score FROM cards, collections WHERE cards.id = collections.card_id AND LOWER(cards.player) = '{nickname.lower()}' AND collections.user_id='{message.from_user.id}'").fetchall()[::-1]
    cursor.execute(f"UPDATE indexes SET nickname='{nickname}', card_search_index='0' WHERE user_id='{message.from_user.id}'")
    conn.commit()
    if len(cards) >= 1:
        if len(cards[0]) == 5:
            card = utils.Card(cards[0])
            if is_trans:
                await draw_card(typ="search", tek=1, all=length, is_transfer=True, card=card, message=message)
            else:
                await draw_card(typ="search", tek=1, all=length, card=card, message=message)
        else:
            await message.answer(" ❌ Кажется, в твоей коллекции нет таких карт...")
    else:
        await message.answer(" ❌ Кажется, в твоей коллекции нет таких карт...")

async def get_nickname(message: Message, state: FSMContext):
    await get_nickname_temp(message, state)

async def get_nickname_trans(message: Message, state: FSMContext):
    await get_nickname_temp(message, state, is_trans=True)


class Team(StatesGroup):
    TEAM = State()
    TEAM_TRANS = State()

async def get_team_temp(message: Message, state: FSMContext, is_trans=False):
    await state.update_data(team=message.text.strip())
    data = await state.get_data()
    team = data['team']
    await state.clear()

    conn = sqlite3.connect('./database.db')
    cursor = conn.cursor()
    length = cursor.execute(f"SELECT COUNT(cards.id) FROM cards, collections WHERE cards.id = collections.card_id AND LOWER(cards.team) = '{team.lower()}' AND collections.user_id='{message.from_user.id}'").fetchone()[0]
    cards = cursor.execute(f"SELECT cards.id, cards.player, cards.team, cards.rank, cards.score FROM cards, collections WHERE cards.id = collections.card_id AND LOWER(cards.team) = '{team.lower()}' AND collections.user_id='{message.from_user.id}'").fetchall()[::-1]
    cursor.execute(f"UPDATE indexes SET team='{team}', card_team_index='0' WHERE user_id='{message.from_user.id}'")
    conn.commit()
    if len(cards) >= 1:
        if len(cards[0]) == 5:
            card = utils.Card(cards[0])
            if is_trans:
                await draw_card(typ="team", tek=1, all=length, is_transfer=True, card=card, message=message)
            else:
                await draw_card(typ="team", tek=1, all=length, card=card, message=message)
        else:
            await message.answer(" ❌ Кажется, в твоей коллекции нет таких карт...")
    else:
        await message.answer(" ❌ Кажется, в твоей коллекции нет таких карт...")

async def get_team(message: Message, state: FSMContext):
    await get_team_temp(message, state)

async def get_team_trans(message: Message, state: FSMContext):
    await get_team_temp(message, state, is_trans=True)


class TransferID(StatesGroup):
    ID = State()

async def get_transfer_id(message: Message, state: FSMContext):
    await state.update_data(id=message.text.strip())
    data = await state.get_data()
    id = data['id']
    await state.clear()
    conn = sqlite3.connect('./database.db')
    cursor = conn.cursor()

    user_exist = cursor.execute(f"SELECT status FROM users WHERE id='{id}'").fetchone()
    is_active = cursor.execute(f"SELECT status FROM transfers WHERE user_id_1='{message.from_user.id}' AND user_id_2='{id}' AND status='active'").fetchone()
    has_card = cursor.execute(f"SELECT card_id FROM collections WHERE user_id='{id}'").fetchone()
    if user_exist == ("active",) and not is_active and has_card:
        card_id = cursor.execute(f"SELECT card_transfer_index FROM indexes WHERE user_id='{message.from_user.id}'").fetchone()[0]
        card_info = cursor.execute(f"SELECT id, player, team, rank, score FROM cards WHERE id='{card_id}'").fetchone()
        transfer_card = utils.Card(card_info)
        try:
            text = f"""🔤 Никнейм: <b>{transfer_card.name}</b> 

🕹 Команда: <b>{transfer_card.team}</b>

🎖 Звание: <b>{transfer_card.rank}</b>

🔢 Очки: <b>{transfer_card.score}</b>"""

            photo = FSInputFile(path=f"./cards/{transfer_card.id}.jpg")
            text = f"<b>👀 Игрок {message.from_user.id} отправляет тебе запрос на обмен. Посмотри, что он предлагает:</b>\n\n{text}"

            cursor.execute(f"INSERT INTO transfers ('user_id_1', 'user_id_2', 'card_id_1', 'card_id_2', 'status') VALUES ('{message.from_user.id}', '{id}', '{transfer_card.id}', '', 'active')")
            conn.commit()
            rowid = cursor.execute(f"SELECT id FROM collections WHERE user_id='{message.from_user.id}' AND card_id='{transfer_card.id}'").fetchall()[::-1][0]
            cursor.execute(f"DELETE FROM collections WHERE id='{rowid[0]}'")
            conn.commit()
            accept_transfer_ikb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Принять и выбрать карту",
                        callback_data=f"accept_transfer_{transfer_card.id}"
                    )],
                [InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"decline_transfer_{transfer_card.id}"
                )]
            ], resize_keyboard=True)
            await bot.send_photo(chat_id=int(id), photo=photo, caption=text, parse_mode="HTML", reply_markup=accept_transfer_ikb)
            await message.answer(f"✅ Запрос на обмен игроку <b>{id}</b> отправлен", parse_mode="HTML")
            cursor.close()
        except Exception as e:
            print(e)
            cursor.execute(f"INSERT INTO collections ('user_id', 'card_id') VALUES ('{message.from_user.id}', '{card_id}')")
            conn.commit()
            await message.answer("❌ Похоже, что-то пошло не так")
            cursor.close()
    else:
        if not user_exist:
            await message.answer("❌ Похоже, игрока с таким ID не существует")
            cursor.close()
        elif is_active:
            await message.answer("❌ Вы уже отправили запрос на обмен этому пользователю. Дождитесь ответа, чтобы продолжить обмениваться")
            cursor.close()
        elif not has_card:
            await message.answer("❌ У игрока нет карт для обмена на данный момент.")
            cursor.close()


class AddCard(StatesGroup):
    PHOTO = State()
    NICKNAME = State()
    TEAM = State()
    RANK = State()


async def get_card_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.text)
    data = await state.get_data()
    try:
        if data["photo"] != "Отмена":
            files = [int(f.split(".")[0]) for f in listdir("./cards/")]
            await state.update_data(id=max(files) + 1)
            await message.bot.download(file=message.photo[-1].file_id, destination=f"./cards/{max(files) + 1}.jpg")
            await message.answer("Напиши ник игрока: ")
            await state.set_state(AddCard.NICKNAME)
        else:
            await message.answer("Вы вернулись в меню", reply_markup=admin_menu_kb)
            await state.clear()
    except Exception as e:
        await message.answer(f"Не удалось добавить карту: {e}", reply_markup=admin_menu_kb)

async def get_card_nickname(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    data = await state.get_data()
    if data["nickname"] != "Отмена":
        await message.answer("Напиши команду игрока: ")
        await state.set_state(AddCard.TEAM)
    else:
        await message.answer("Вы вернулись в меню", reply_markup=admin_menu_kb)
        await state.clear()

async def get_card_team(message: Message, state: FSMContext):
    await state.update_data(team=message.text)
    data = await state.get_data()
    if data["team"] != "Отмена":
        await message.answer("Напиши ранг игрока: ")
        await state.set_state(AddCard.RANK)
    else:
        await message.answer("Вы вернулись в меню", reply_markup=admin_menu_kb)
        await state.clear()

async def get_card_rank(message: Message, state: FSMContext):
    await state.update_data(rank=message.text)
    data = await state.get_data()
    await state.clear()
    if data["rank"] != "Отмена":
        match data["rank"].lower():
            case "сильвер":
                score = 500
            case "звезда":
                score = 1000
            case "калаш":
                score = 1500
            case "калаш с венками":
                score = 2000
            case "два калаша":
                score = 2500
            case "биг стар":
                score = 3000
            case "беркут":
                score = 3500
            case "лем":
                score = 4000
            case "суприм":
                score = 4500
            case "глобал":
                score = 5000

        conn = sqlite3.connect('./database.db')
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO cards ('id', 'player', 'team', 'rank', 'amount', 'score') VALUES ('{data['id']}', '{data['nickname']}', '{data['team']}', '{data['rank']}', 50, '{score}')")
        conn.commit()
        cursor.close()
        await message.answer("Карта успешно добавлена", reply_markup=admin_menu_kb)
    else:
        await message.answer("Вы вернулись в меню", reply_markup=admin_menu_kb)

class TransferCur(StatesGroup):
    ID = State()
    AMOUNT = State()

async def get_trancfer_cur_id(message: Message, state: FSMContext):
    await state.update_data(id=message.text)
    data = await state.get_data()
    if data["id"] != "Отмена":
        conn = sqlite3.connect('./database.db')
        cursor = conn.cursor()
        is_exist = cursor.execute(f"SELECT status FROM users WHERE id='{data['id']}'").fetchone()
        cursor.close()
        if is_exist:
            await message.answer("Выбери количество валюты, начисляемое пользователю ", reply_markup=currency_ikb)
            await state.set_state(TransferCur.AMOUNT)
        else:
            await message.answer("Нельзя перевести валюту данному пользователю, так как указан некорректный ID", reply_markup=admin_menu_kb)
            await state.clear()
    else:
        await message.answer("Вы вернулись в меню", reply_markup=admin_menu_kb)
        await state.clear()

async def add_currency(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(amount=callback.data.split("_")[-1])
    data = await state.get_data()
    await state.clear()

    try:
        conn = sqlite3.connect('./database.db')
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET credits='{int(data['amount'])}' WHERE id='{data['id']}'").fetchone()
        conn.commit()
        cursor.close()
        await callback.message.answer(f"<b>{data['amount']} валюты успешно начислено пользователю {data['id']}</b> 🎉", parse_mode="HTML", reply_markup=admin_menu_kb)
    except Exception as e:
        print(e)
        await callback.message.answer(f"Не удалось начислить валюту. Попробуйте еще раз", reply_markup=admin_menu_kb)


