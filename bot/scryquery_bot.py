import discord
from discord.ext import commands
from scryfall.service import card_search, ScryQueryCard, random_card, get_random_card_ruling
from bot.utils import format_response, get_reply_query, replace_emojis
import bot.emojis as emojis
from edhrec.service import get_edhrec_stats
from random import randint
from image_utils import generate_grid

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, case_insensitive=True)
   
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
            
@bot.command(aliases=["slivermetimbers"])
async def sliverme(ctx):
    await sqrandom(ctx, query="t:sliver")

@bot.command()
async def BOO(ctx):
    await ctx.send("https://tenor.com/view/hamster-ayasan-gif-24417561")

@bot.command(aliases=["quoteme"])
async def flavortown(ctx):
    async with ctx.typing():
        card = random_card("has:flavor")
        flavor_text = card.get('flavor_text')
        card_name_with_link = f'[{card['name']}](<{card['scryfall_url']}>)'
        bot_message=f"{flavor_text}\n\n— {card_name_with_link}"
        await ctx.send(bot_message)

@bot.command()
async def edhrec(ctx, *, query: str):
    async with ctx.typing():
        commander_stats = get_edhrec_stats(query)
        if commander_stats:
            rank = commander_stats.get('rank')
            commander_decks = commander_stats.get('commander_deck_count')
            salt_score = round(commander_stats.get('salt', 0), 3)
            bot_message = f"EDHRec Stats for {query}:\n>>> Rank: #{rank}\nCommander decks: {commander_decks:,}\nSalt score: {salt_score}"
        else:
            bot_message = f"No EDHRec data found for {query}."
        await ctx.send(bot_message, reference=ctx.message, mention_author=False)

@bot.command(aliases=["randnum", "random"])
async def gamble(ctx, *, query: str = '7'):
    async with ctx.typing():
        input = 0
        message = ""
        try:
            input = int(query)
            if input <= 1:
                message = "Please provide a positive integer > 1"
            elif input > 250:
                message = "What game are you even playing?!?"
            else:
                number = randint(1, input)
                message = f"🎲 You rolled: {number}"
                
        except:
            message = "Please provide a positive integer > 1"
        
        await ctx.send(message, reference=ctx.message, mention_author=False)

@bot.command(aliases=["datapriest", "edhtrack"])
async def arcaneoculus(ctx):
    async with ctx.typing():
        await ctx.send('https://arcane-oculus-edh.base44.app/')
        
@bot.command()
async def asktheoracle(ctx, *, query:str = ''):
    async with ctx.typing():
        ruling_response = get_random_card_ruling(query)
        if ruling_response and ruling_response.get('ruling'):
            card = ruling_response['card']
            bot_response = format_response([ruling_response["card"]])
            name_with_link = f"**[{card['name']}](<{card['scryfall_url']}>)**"
            ruling = ruling_response['ruling'].get('ruling_text')
            await ctx.send(f'The Oracle has spoken!\n\n>>> {name_with_link}\n{ruling}', files=bot_response["files"], reference=ctx.message, mention_author=False)
        else:
            oracle_img_path = 'assets/oracle_pondering_orb.jpg'
            oracle = discord.File(oracle_img_path)
            await ctx.send('The Oracle is pondering the orb and cannot respond', file=oracle, reference=ctx.message)

@bot.command(aliases=['thoughtclash'])
async def clash(ctx):   
    async with ctx.typing():
        contestants = [ m.mention for m in ctx.message.mentions]
        contestants.append(ctx.author.mention)
        
        if len(contestants) == 1:
            initial_message = 'You need friends to play ThoughtClash, nerd!'
        elif len(contestants) > 16:
            initial_message = 'You have too many friends. Pick your 16 closest'
        else:
            initial_message = f'Highest CMC wins. Good luck!'
            for contestant in contestants:
                initial_message += f' {contestant}'
        
        await ctx.send(initial_message)
    if len(contestants) == 1:
        return
     
    async with ctx.typing():                  
        entries = []
        cmcs = []
        
        entry_message = ''
        for contestant in contestants:
            cmc_filter = ' '.join([ f'mv!={int(c)}' for c in cmcs])
            card = random_card(f'{cmc_filter}')
            cmcs.append(card.get('cmc', 0))
            entries.append({ 'user': contestant, 'card_name': card['name'], 'card_image_url': card['image_uri'], 'cmc': card.get('cmc', 0) })
            name_with_link = f"**[{card['name']}](<{card['scryfall_url']}>)**"
            
            entry_message += f'{contestant}: {name_with_link} ({card['mana_cost']})\n'
        
        highest_cmc = max([e['cmc'] for e in entries])
        winning_entry = [e for e in entries if e['cmc'] == highest_cmc][0]
        card_image = generate_grid([e['card_image_url'] for e in entries])
        message = replace_emojis(f'>>> {entry_message}\n\nCongrats {winning_entry['user']}!!')
        
        await ctx.send(message, file=discord.File(card_image, filename="grid.png"))
        
        
        
            
        