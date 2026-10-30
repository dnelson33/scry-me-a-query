from typing import TypedDict, List
from discord import Embed, File

class ScryQueryBotResponse(TypedDict):
    response_message: str
    files: List[File]
    embed: Embed