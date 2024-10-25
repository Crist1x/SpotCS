from aiogram import types
from dispatcher import dp

from aiogram import F


@dp.message(F.content_type.in_({'new_chat_members', 'left_chat_member'}))
async def on_user_join_or_left(message: types.Message):

    await message.delete()
