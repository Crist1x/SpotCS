from dotenv import load_dotenv
import os

# Find .env file with os variables
load_dotenv("dev.env")

# retrieve config variables
try:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    BOT_OWNERS = [int(x) for x in os.getenv('BOT_OWNERS').split(",")]
    CHANNEL_ID = os.getenv('CHANNEL_ID')
except (TypeError, ValueError) as ex:
    print("Error while reading config:", ex)

start_text = """<b>Приветствую, фанаты Counter-Strike и коллекционеры карточек!</b> 🎮✨

Рады приветствовать вас в нашем чат-боте, посвященном миру карточек киберспортсменов! Здесь вы сможете не только узнать о лучших игроках и их достижениях, но и обмениваться карточками, участвовать в конкурсах и находить единомышленников.

Не стесняйтесь задавать вопросы, делиться своим опытом и рассказывать о своих коллекциях. Мы здесь, чтобы помочь вам в этом увлекательном путешествии!

Готовы к новым открытиям? Давайте начнем! 🚀

<b>Для продолжения игры необходимо подписаться на наш канал</b>✅"""

menu_text= "Текст меню"

help_text = "Помощь"