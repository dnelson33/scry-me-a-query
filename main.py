import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from scryfall import scryfall_query
from pillow import generate_grid

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
    
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    
@bot.command()
async def squery(ctx, *, query: str):
    async with ctx.typing():
        data = None
        try:
            (data, site_url) = scryfall_query(query)
        except Exception as e:
            print(f"Error querying Scryfall: {e}")
            
        (message, _, files) = _format_response(data, site_url)
        
        await ctx.send(message, files=files) 

def _format_response(data, site_url=''):
    response_message = ""
    if not data or 'data' not in data:
        response_message = "No data found."
    
    response_message = f"Scryfall results: {site_url}\n"
    cards = data['data']
    image_uris = []
    for card in cards:  # Limit to first 5 results
        image_uri = card.get('image_uris', {}).get('small', None)
        image_uris.append(image_uri)
    
    i = 0
    embeds = []
    files = []
    while i < len(image_uris):
        batch = image_uris[i:i+16]
        grid_image = generate_grid(batch)
        file = discord.File(grid_image, filename='grid.png')
        # embed = discord.Embed()
        # embed.set_image(url="attachment://grid.png")
        # embeds.append(embed)
        files.append(file)
        i+=16
    
    return (response_message, embeds, files)

bot.run(token, log_handler=handler, log_level=logging.DEBUG)

