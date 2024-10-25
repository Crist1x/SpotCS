import sqlite3
from cgitb import handler
from logging import exception

from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import handlers.callbacks
from data import utils
from data.utils import draw_card
from keyboards.admin import admin_menu_kb, confirm_quiz
from keyboards.general import main_menu_kb


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
            await message.answer("Правильный ответ! Вы получаете 1 дополнительную попытку", reply_markup=main_menu_kb)
            cursor.execute(f"UPDATE users SET chances = chances + 1 WHERE id={message.from_user.id}")
            conn.commit()
            cursor.close()
        else:
            await message.answer(f"<b>Вы ошиблись</b>\n\nПравильный ответ: {answers[correct-1]}", reply_markup=main_menu_kb)
            conn.commit()
            cursor.close()

    else:
        await message.answer("Вы вернулись в меню", reply_markup=main_menu_kb)
        cursor.close()
        await state.clear()


class Search(StatesGroup):
    NICKNAME = State()


search_cards = []

async def get_nickname(message: Message, state: FSMContext):
    global search_cards
    handlers.callbacks.card_index = 0
    await state.update_data(nickname=message.text.strip())
    data = await state.get_data()
    nickname = data['nickname']
    await state.clear()
    print(nickname)

    conn = sqlite3.connect('./database.db')
    cursor = conn.cursor()
    length = cursor.execute(f"SELECT COUNT(cards.id) FROM cards, collections WHERE cards.id = collections.card_id AND cards.player = '{nickname}' AND collections.user_id='{message.from_user.id}'").fetchone()[0]
    cards = cursor.execute(f"SELECT cards.id, cards.player, cards.team, cards.rank, cards.score FROM cards, collections WHERE cards.id = collections.card_id AND cards.player = '{nickname}' AND collections.user_id='{message.from_user.id}'").fetchall()[::-1]
    search_cards = cards

    if len(cards) >= 1:
        if len(cards[0]) == 5:
            card = utils.Card(cards[0])
            await draw_card(typ="search", tek=1, all=length, card=card, message=message)
        else:
            await message.answer(" ❌ Кажется, в твоей коллекции нет таких карт...")
    else:
        await message.answer(" ❌ Кажется, в твоей коллекции нет таких карт...")


class Team(StatesGroup):
    TEAM = State()

team_cards = []

async def get_team(message: Message, state: FSMContext):
    global team_cards
    handlers.callbacks.card_index = 0
    await state.update_data(team=message.text.strip())
    data = await state.get_data()
    team = data['team']
    await state.clear()

    conn = sqlite3.connect('./database.db')
    cursor = conn.cursor()
    length = cursor.execute(f"SELECT COUNT(cards.id) FROM cards, collections WHERE cards.id = collections.card_id AND cards.team = '{team}' AND collections.user_id='{message.from_user.id}'").fetchone()[0]
    cards = cursor.execute(f"SELECT cards.id, cards.player, cards.team, cards.rank, cards.score FROM cards, collections WHERE cards.id = collections.card_id AND cards.team = '{team}' AND collections.user_id='{message.from_user.id}'").fetchall()[::-1]
    team_cards = cards

    if len(cards) >= 1:
        if len(cards[0]) == 5:
            card = utils.Card(cards[0])
            await draw_card(typ="team", tek=1, all=length, card=card, message=message)
        else:
            await message.answer(" ❌ Кажется, в твоей коллекции нет таких карт...")
    else:
        await message.answer(" ❌ Кажется, в твоей коллекции нет таких карт...")