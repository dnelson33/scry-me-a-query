from scryfall.service import ScryQueryCard
from image_utils import generate_grid
from bot.types import ScryQueryBotResponse
import bot.emojis as emojis
from typing import List
import discord
import re 
from random import randint

RESPONSE_LIMIT = 32
GRID_BATCH_SIZE = 16

def format_response(cards:List[ScryQueryCard], site_url:str='') -> ScryQueryBotResponse:
    response_message = ""
    if not cards or len(cards) == 0:
        response_message = f"No data found for query {site_url}"
        files = None
        embed = None
    else:
        card_count = len(cards)

        if card_count == 1:
            response_message = ""
            description = get_formatted_card_info(cards[0])
            embed = discord.Embed(title=cards[0]['name'], url=cards[0]['scryfall_url'], description=description, color=discord.Color.blue())
        else:
            response_message = f">>> ### ScryQuery Results: {card_count} cards"
            if card_count > RESPONSE_LIMIT:
                response_message += f"\nDisplaying first {RESPONSE_LIMIT} results..."
            response_message += f'\n{site_url}'
            embed = None
            
        i = 0
        files = []
        while i < card_count and i < RESPONSE_LIMIT:
            batch = list(card['image_uri'] for card in cards[i:i+GRID_BATCH_SIZE])
            grid_image = generate_grid(batch)
            file = discord.File(grid_image, filename=f'cards_{i}.png')
            files.append(file)
            i+=GRID_BATCH_SIZE
            
        if len(cards) == 1:
            embed.set_image(url=files[0].uri)
            
    return {
        'response_message': response_message,
        'files': files,
        'embed': embed
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

async def get_reply_card_name(ctx) -> str | None:
    if ctx.message.reference is None:
        return None
    message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    
    if message.author.id != ctx.bot.user.id:
        return None
    
    if 'scryfall.com' not in message.content:
        return None
    match = None
    while message is not None:
        match = re.search(r'\[(.*)\]\(<.*scryfall.com.*>\)', message.content)
    
        if not match:
            message = await ctx.channel.fetch_message(message.reference.message_id)
        else:
            return match.group(1).strip()
    return None

    
def get_formatted_card_info(card: ScryQueryCard) -> str:
    price = f'${float(card["price"]):.2f}' if card.get('price') else 'N/A'
    price_foil = f'${float(card["price_foil"]):.2f}' if card.get('price_foil') else 'N/A'
    card_emoji = _get_emoji('card')
    card_foil_emoji = _get_emoji('cardfoil')
    type_and_cost = replace_emojis(f'*{card['type_line']} {card["mana_cost"]}*')
    description = replace_emojis(card['oracle_text'])
    price_info = f"Price: {card_emoji} {price}\t{card_foil_emoji} {price_foil}"
    
    return f"\n{type_and_cost}\n{description}\n\n{price_info}"

def replace_emojis(text: str) -> str:
    return re.sub(r'\{(.*?)\}', _replace_emoji_match, text)

def get_card_name_with_link(card: ScryQueryCard) -> str:
    return f"**[{card['name']}](<{card['scryfall_url']}>)**"
    
def _get_emoji(name:str, fallback:str = "")->str:
    emoji_id = [e for e in emojis.EMOJIS if e.name == name]
    if not emoji_id:
        return fallback
    emoji_id = emoji_id[0].id
    return f'<:{name}:{emoji_id}>'

def _replace_emoji_match(match):
    symbol = match.group(1).lower()
    emoji_name = f'mana{symbol}'
    
    return _get_emoji(emoji_name, f'{{{symbol.upper()}}}')


