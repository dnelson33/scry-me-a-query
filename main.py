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
            (message, files) = _format_response(data, site_url)
            await ctx.send(message, files=files) 
        except Exception as e:
            print(f"Error querying Scryfall: {e}")
            await ctx.send("An error occurred while querying Scryfall.")
            
            
        

def _format_response(data, site_url=''):
    response_message = ""
    if not data or 'data' not in data:
        response_message = f"No data found for query {site_url}"
        files = None
    else:
        card_count = data.get('total_cards')
        response_message = f"Scryfall found {card_count} cards: {site_url}\n"
        
        if card_count > 160:
            response_message += "Displaying first 160 results..."
            
        cards = data['data']
        images = []
        for card in cards[:160]:  # Limit to first 160 results
            if card.get('card_faces', [{}])[0].get('image_uris'):
                image_uris = card['card_faces'][0].get('image_uris', {})
            else:
                image_uris = card.get('image_uris', {})
            image_uri = image_uris.get('small', "")
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

