from scryfall.service import ScryQueryCard
from image_utils.card_grid import generate_grid
from bot.types import ScryQueryBotResponse
from typing import List
import discord

RESPONSE_LIMIT = 64
GRID_BATCH_SIZE = 16

def format_response(cards:List[ScryQueryCard], site_url:str='') -> ScryQueryBotResponse:
    response_message = ""
    if not cards or len(cards) == 0:
        response_message = f"No data found for query {site_url}"
        files = None
    else:
        card_count = len(cards)

        response_message = f"Scryfall found {card_count} cards: {site_url}\n"
        
        if card_count > RESPONSE_LIMIT:
            response_message += f"Displaying first {RESPONSE_LIMIT} results..."
        
        i = 0
        files = []
        while i < card_count and i < RESPONSE_LIMIT:
            batch = list(card['image_uri'] for card in cards[i:i+GRID_BATCH_SIZE])
            grid_image = generate_grid(batch)
            file = discord.File(grid_image, filename=f'cards_{i}.png')
            files.append(file)
            i+=GRID_BATCH_SIZE
    
    return {
        'response_message': response_message,
        'files': files
    } 
    

async def get_reply_query(ctx, command_prefix: str) -> str:
    if ctx.message.reference is None:
        return ''
    message = await ctx.channel.fetch_message(ctx.message.reference.message_id) 
    query = ""
    try:
        while message is not None:
            if message.content.startswith(f'{command_prefix} '):
                query += message.content[len(command_prefix) + 1:] + " "
            if message.reference is None:
                break
            message = await ctx.channel.fetch_message(message.reference.message_id)
            
        return query.strip()

    except Exception as e:
        print(f"Error fetching replied message: {e}")
        raise e