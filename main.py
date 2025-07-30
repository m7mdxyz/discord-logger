# ==== Start of imports ===== 
import discord
from dotenv import load_dotenv
import os
# ==== End of imports ====

# ==== Start of bot's logic ====
class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

        # Make sure the bot is logging one server only
        if client.guilds.__len__() > 1:
            print(f"The bot have joined {client.guilds.__len__()} guilds. Multiple guilds logging is not supported")
            client.close()

        # TODO: Store the guild, members, and all dat shit.

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')
        # TODO: Store the message
# ==== End of bot's logic ====

# ==== Start of Intents, permissions, and tokens ====
intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
load_dotenv()
token = os.getenv("BOT_TOKEN")
# ==== End of Intents, permissions, and tokens ====

# ==== Start of main logic ====
client.run(token)

# ==== End of main logic ====