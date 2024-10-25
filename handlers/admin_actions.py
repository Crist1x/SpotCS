from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from data.forms import Quiz
from dispatcher import dp

from aiogram import F
from data.filters import IsOwnerFilter
from keyboards.admin import cansel_kb

router = Router()

@dp.message(IsOwnerFilter(is_owner=True), F.text == "Добавить карту")
async def add_card(message: Message):
    await message.answer("В разработке")

@dp.message(IsOwnerFilter(is_owner=True), F.text == "Забанить")
async def ban(message: Message):
    await message.answer("В разработке")


@dp.message(IsOwnerFilter(is_owner=True), F.text == "Разбанить")
async def unban(message: Message):
    await message.answer("В разработке")


@dp.message(IsOwnerFilter(is_owner=True), F.text == "Квиз")
async def quiz(message: Message, state: FSMContext):
    await message.answer("Введите вопрос, который будет на следующем квизе:", reply_markup=cansel_kb)
    await state.set_state(Quiz.QUESTION)