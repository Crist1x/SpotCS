from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from data.forms import Quiz, AddCard, TransferCur
from dispatcher import dp

from aiogram import F
from data.filters import IsOwnerFilter
from keyboards.admin import cansel_kb

router = Router()

@dp.message(IsOwnerFilter(is_owner=True), F.text == "Добавить карту")
async def add_card(message: Message, state: FSMContext):
    await message.answer("Пришлите фотографию карточки: ", reply_markup=cansel_kb)
    await state.set_state(AddCard.PHOTO)

@dp.message(IsOwnerFilter(is_owner=True), F.text == "Перевести валюту")
async def transfer_currency(message: Message, state: FSMContext):
    await message.answer("Введите ID пользователя", reply_markup=cansel_kb)
    await state.set_state(TransferCur.ID)


@dp.message(IsOwnerFilter(is_owner=True), F.text == "Квиз")
async def quiz(message: Message, state: FSMContext):
    await message.answer("Введите вопрос, который будет на следующем квизе:", reply_markup=cansel_kb)
    await state.set_state(Quiz.QUESTION)