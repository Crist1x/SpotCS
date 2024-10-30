import asyncio

from aiogram.filters import CommandStart, Command
from aiogram import F
import handlers.callbacks, handlers.user_actions, handlers.admin_actions
import keyboards.general, keyboards.admin
import config
from config import help_text, BOT_OWNERS
from data.forms import *
from dispatcher import dp, bot

dp.include_router(handlers.user_actions.router)
dp.include_router(handlers.admin_actions.router)

dp.callback_query.register(handlers.callbacks.in_game, F.data == "in_game")
dp.callback_query.register(handlers.callbacks.random, F.data == "random")
dp.callback_query.register(handlers.callbacks.lucky_shot, F.data == "lucky_shot")
dp.callback_query.register(handlers.callbacks.quiz, F.data == "quiz")
dp.callback_query.register(handlers.callbacks.confirm_quiz, F.data == "confirm_quiz")
dp.callback_query.register(handlers.callbacks.disclaim_quiz, F.data == "disclaim_quiz")
dp.callback_query.register(handlers.callbacks.prev_card, F.data.startswith("prev_card"))
dp.callback_query.register(handlers.callbacks.next_card, F.data.startswith("next_card"))
dp.callback_query.register(handlers.callbacks.first_card, F.data.startswith("first_card"))
dp.callback_query.register(handlers.callbacks.last_card, F.data.startswith("last_card"))
dp.callback_query.register(handlers.callbacks.to_collection, F.data == "to_collection")
dp.callback_query.register(handlers.callbacks.search, F.data.startswith("search"))
dp.callback_query.register(handlers.callbacks.by_rank, F.data.startswith("by_rank"))
dp.callback_query.register(handlers.callbacks.by_team, F.data.startswith("by_team"))
dp.callback_query.register(handlers.callbacks.create_transfer, F.data == "create_transfer")

dp.callback_query.register(handlers.callbacks.sort_rank, F.data.startswith("rank_"))

dp.message.register(get_question, Quiz.QUESTION)
dp.message.register(get_first, Quiz.FIRST_V)
dp.message.register(get_second, Quiz.SECOND_V)
dp.message.register(get_third, Quiz.THIRD_V)
dp.message.register(get_fourth, Quiz.FOURTH_V)
dp.message.register(get_correct, Quiz.CORRECT)

dp.message.register(get_answer, GetAnswer.ANSWER)

dp.message.register(get_nickname, Search.NICKNAME)
dp.message.register(get_nickname_trans, Search.NICKNAME_TRANS)
dp.message.register(get_team, Team.TEAM)

@dp.message(Command("help"))
async def help_func(message: Message):
    await message.answer(help_text, parse_mode="HTML")


@dp.message(CommandStart())
async def start(message: Message):
    if message.from_user.id not in BOT_OWNERS:
        await message.answer(config.start_text, reply_markup=keyboards.general.in_game_ikb, parse_mode="HTML")
    else:
        await message.answer("<b>Добро пожаловать в панель администратора</b>", reply_markup=keyboards.admin.admin_menu_kb,
                             parse_mode="HTML")


async def main():
    await dp.start_polling(bot, skip_updates=False)


if __name__ == "__main__":
    asyncio.run(main())
