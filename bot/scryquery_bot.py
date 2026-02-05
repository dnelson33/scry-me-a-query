from importlib.resources import files
import discord
from discord.ext import commands
from scryfall.service import card_search, ScryQueryCard, random_card
from bot.utils import format_response, get_reply_query
import bot.emojis as emojis
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
   
@bot.event
async def on_ready():
    GUILD_ID = 1462905855686082653 # Guild ID where emojis are hosted
    guild = bot.get_guild(GUILD_ID)

    emojis.EMOJIS = guild.emojis
    
    print(f'Logged in as {bot.user.name} - {bot.user.id}')

@bot.command()
async def sq(ctx, *, query: str):
    global last_sq
    reply_query = await get_reply_query(ctx, '!sq')
    query = f"{reply_query} {query}".strip()
    
    async with ctx.typing():
        last_sq = query
        try:
            card_response = card_search(query)
            bot_response = format_response(card_response["cards"], card_response["scryfall_url"])
            
            await ctx.send(bot_response["response_message"], files=bot_response["files"], reference=ctx.message, mention_author=False)
        except Exception as e:
            print(f"Error querying Scryfall: {e}")
            await ctx.send("An error occurred while querying Scryfall.", reference=ctx.message, mention_author=False)

@bot.command()
async def mycaptain(ctx):
    await sqrandom(ctx, query="is:commander")
    
@bot.command()
async def sqrandom(ctx, *, query: str):
    async with ctx.typing():
        card = random_card(query)
        bot_response = format_response([card], card['scryfall_url'])
        await ctx.send(bot_response["response_message"], files=bot_response["files"], reference=ctx.message, mention_author=False)       
            
@bot.command()
async def sliverme(ctx):
    await sqrandom(ctx, query="t:sliver")

@bot.command()
async def BOO(ctx):
    await ctx.send("https://tenor.com/view/hamster-ayasan-gif-24417561")






