# Scry Me a Query (Discord Bot)
This bot provides additional Scryfall functionality to discord like returning multiple items from a query.

## Commands
- **`!sq <query>`**: Search Scryfall for cards matching `<query>` and return results (images/embeds).
	- Example: `!sq t:elf otag:manadork` — search for cards with type Elf and tagged with manadork.

- **`!sqrandom <query>`**: Return a random card matching `<query>` with an image, link and full description.
	- Example: `!sqrandom t:artifact` — a random artifact card.

- **`!mycaptain`**: Return a random commander with an image, link and full description.

- **`!sliverme`** (alias: `!slivermetimbers`): Returns a random Sliver with an image, link and full description.

- **`!BOO`**: Go for the Eyes!

- **`!flavortown`** (alias: `!quoteme`): Sends a random card flavor text and a link to the card.

- **`!edhrec <commander name>`**: Fetch EDHRec stats for the given commander and print rank, deck count, and salt score.
	- Example: `!edhrec Atraxa, Praetors' Voice`

- **`!gamble <n>`** (aliases: `!randnum`, `!random`): Roll a random number from 1 to `n`. `n` defaults to `7`.
	- Example: `!gamble 20` — roll 1..20.

- **`!arcaneoculus`** (aliases: `!datapriest`, `!edhtrack`): Sends a link to the Arcane Oculus EDH tracking site.

- **`!asktheoracle <optional query>`**: Consults The Oracle for a random card ruling (and card image) or a fallback image if unavailable.
	- Example: `!asktheoracle`

- **`!clash`** (alias: `!thoughtclash`): Play ThoughtClash with mentioned users. The bot draws a random card for each contestant and the highest CMC wins. Displays an image of the drawn cards and announces the winner.
	- Usage: Mention up to 16 users in the message; the command automatically includes the command author.
    - Example: `!ThoughtClash @friendlyhandle`

### Notes
- The bot uses `!` as the command prefix and is case-insensitive.
- Emojis loaded from a configured guild on startup are used by some responses.
- Many commands use Scryfall and EDHRec services; network access is required.

