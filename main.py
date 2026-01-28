from importlib.resources import files
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from scryfall import scryfall_query
from pillow import generate_grid
from get_random import get_random_color_identity, get_random_creature_type
import random 

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def get_random_card(ctx, query):
    data = None
    print(query)

    try:
        (data, site_url) = scryfall_query(query)
        print('total cards:', data.get('total_cards', 0))
        has_next_page = data.get('next_page') is not None

        if(has_next_page):
            random_page = random.randint(0, (data['total_cards']) // 175) + 1
            (data, site_url) = scryfall_query(f"{query} page:{random_page}")

        rnd = random.randint(0, 175 if has_next_page else data.get('total_cards', 1) - 1)
        data['data'] = [data['data'][rnd]]  # Keep only one random sliver
        data['total_cards'] = 1
        (_, files) = _format_response(data, site_url)
        await ctx.send(files=files) 
    except Exception as e:
        print(f"Error querying Scryfall: {e}")
        await ctx.send(f"Woah there are no cards that match `{query}`!")  
    
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    
@bot.command()
async def sq(ctx, *, query: str):
    global last_sq
    reply_query = await _get_reply_query(ctx)
    if reply_query is not None:
        query = f"{reply_query} {query}"
    
    async with ctx.typing():
        data = None
        last_sq = query
        try:
            (data, site_url) = scryfall_query(query)
            (message, files) = _format_response(data, site_url)
            # reply to the original message being replied to (if any), otherwise reply to the command message
            
            await ctx.send(message, files=files, reference=ctx.message, mention_author=False)
        except Exception as e:
            print(f"Error querying Scryfall: {e}")
            await ctx.send("An error occurred while querying Scryfall.", reference=ctx.message, mention_author=False)

@bot.command()
async def mycaptain(ctx):
    color_identity = get_random_color_identity()
    query = f"is:commander ci={color_identity}"
    async with ctx.typing():
        await get_random_card(ctx, query)

@bot.command()
async def sqrandom(ctx, *, query: str):
    async with ctx.typing():
        await get_random_card(ctx, query)
            
            
@bot.command()
async def sqadd(ctx, *, query:str):
    if not last_sq is None:           
        new_query = f"{last_sq} {query}"
    else:
        new_query = query
    await sq(ctx, query=new_query)
       
    
@bot.command()
async def sliverme(ctx):
    async with ctx.typing():
        await get_random_card(ctx, "t:sliver")

@bot.command()
async def BOO(ctx):
    await ctx.send("https://tenor.com/view/hamster-ayasan-gif-24417561")

async def _get_reply_query(ctx):
    if ctx.message.reference is None:
        return None
    message = await ctx.channel.fetch_message(ctx.message.reference.message_id) 
    query = ""
    try:
        while message is not None:
            print(message.content)
            if message.content.startswith('!sq '):
                query += message.content[4:] + " "
            if message.reference is None:
                break
            message = await ctx.channel.fetch_message(message.reference.message_id)
            
        print(query)
        return query.strip()
    
    except Exception as e:
        print(f"Error fetching replied message: {e}")
        
def _format_response(data, site_url=''):
    card_limit = 64
    response_message = ""
    if not data or 'data' not in data:
        response_message = f"No data found for query {site_url}"
        files = None
    else:
        card_count = data.get('total_cards')

        response_message = f"Scryfall found {card_count} cards: {site_url}\n"
        
        if card_count > card_limit:
            response_message += f"Displaying first {card_limit} results..."
            
        cards = data['data']
        images = []
        for card in cards[:card_limit]:  # Limit to first X results
            if card.get('card_faces', [{}])[0].get('image_uris'):
                image_uris = card['card_faces'][0].get('image_uris', {})
            else:
                image_uris = card.get('image_uris', {})
            image_uri = image_uris.get('png', "")
            images.append(image_uri)
        
        i = 0
        files = []
        while i < len(images):
            batch = images[i:i+16]
            grid_image = generate_grid(batch)
            file = discord.File(grid_image, filename='grid.png')
            files.append(file)
            i+=16
    
    return (response_message, files)

bot.run(token, log_handler=handler, log_level=logging.DEBUG)

