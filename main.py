from bot import bot
from dotenv import load_dotenv
import logging
import os

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

bot.run(token, log_handler=handler, log_level=logging.DEBUG)

