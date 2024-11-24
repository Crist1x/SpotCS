import asyncio

from aiogram.filters import CommandStart, Command
from aiogram import F

import data.forms
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
dp.callback_query.register(handlers.callbacks.tek_transfers, F.data == "tek_transfers")
dp.callback_query.register(handlers.callbacks.finished_transfers, F.data == "my_transfers")
dp.callback_query.register(handlers.callbacks.add_card1, F.data == "add_card")
dp.callback_query.register(handlers.callbacks.donate, F.data == "donate")
dp.callback_query.register(handlers.callbacks.purchases, F.data == "purchases")

dp.callback_query.register(handlers.callbacks.sort_rank, F.data.startswith("rank_"))
dp.callback_query.register(handlers.callbacks.accept_transfer, F.data.startswith("accept_transfer"))
dp.callback_query.register(handlers.callbacks.decline_transfer, F.data.startswith("decline_transfer"))
dp.callback_query.register(handlers.callbacks.last_accept, F.data.startswith("last_accept"))
dp.callback_query.register(handlers.callbacks.last_decline, F.data.startswith("last_decline"))
dp.callback_query.register(handlers.callbacks.tek_next, F.data == "tek_next")
dp.callback_query.register(handlers.callbacks.tek_prev, F.data == "tek_prev")
dp.callback_query.register(handlers.callbacks.tek_decline, F.data == "tek_decline")
dp.callback_query.register(data.forms.add_currency, F.data.startswith("currency"))
dp.callback_query.register(handlers.callbacks.want_currency, F.data == "want_currency")
dp.callback_query.register(handlers.callbacks.buy_open_card, F.data == "buy_open_card")
dp.callback_query.register(handlers.callbacks.buy_random, F.data == "buy_random")
dp.callback_query.register(handlers.callbacks.buy_lucky_shot, F.data == "buy_lucky_shot")
dp.callback_query.register(handlers.callbacks.confirm_buy, F.data.startswith("confirm_"))
dp.callback_query.register(handlers.callbacks.buy_conf, F.data.startswith("buy_conf_"))
dp.callback_query.register(handlers.callbacks.buy_cansel, F.data == "buy_cansel")

dp.message.register(get_question, Quiz.QUESTION)
dp.message.register(get_first, Quiz.FIRST_V)
dp.message.register(get_second, Quiz.SECOND_V)
dp.message.register(get_third, Quiz.THIRD_V)
dp.message.register(get_fourth, Quiz.FOURTH_V)
dp.message.register(get_correct, Quiz.CORRECT)

dp.message.register(get_answer, GetAnswer.ANSWER)

dp.message.register(get_card_photo, AddCard.PHOTO)
dp.message.register(get_card_nickname, AddCard.NICKNAME)
dp.message.register(get_card_team, AddCard.TEAM)
dp.message.register(get_card_rank, AddCard.RANK)

dp.message.register(get_nickname, Search.NICKNAME)
dp.message.register(get_nickname_trans, Search.NICKNAME_TRANS)
dp.message.register(get_team, Team.TEAM)
dp.message.register(get_transfer_id, TransferID.ID)

dp.message.register(get_trancfer_cur_id, TransferCur.ID)

@dp.message(Command("help"))
async def help_func(message: Message):
    await message.answer(help_text, parse_mode="HTML")


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(config.start_text, reply_markup=keyboards.general.in_game_ikb, parse_mode="HTML")

@dp.message(Command("admin_panel"))
async def admin_panel(message: Message):
    if message.from_user.id in BOT_OWNERS:
        await message.answer("<b>Добро пожаловать в панель администратора</b>", reply_markup=keyboards.admin.admin_menu_kb,parse_mode="HTML")

async def main():
    await dp.start_polling(bot, skip_updates=False)


if __name__ == "__main__":
    asyncio.run(main())
