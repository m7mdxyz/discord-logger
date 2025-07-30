# ==== Start of imports ===== 
import discord
from dotenv import load_dotenv
import os
# ==== End of imports ====

# ==== Start of logic ====
class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')
# ==== End of logic ====

# ==== Start of Intents, permissions, and tokens ====
intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
load_dotenv()
token = os.getenv("BOT_TOKEN")
client.run(token)
# ==== End of Intents, permissions, and tokens ====