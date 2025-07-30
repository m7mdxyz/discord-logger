# ==== Start of imports ===== 
import discord
from dotenv import load_dotenv
import os
import json
# ==== End of imports ====

# ==== Start of bot's logic ====
class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

        # Make sure the bot is logging one server only
        if client.guilds.__len__() > 1:
            print(f"The bot have joined {client.guilds.__len__()} guilds. Multiple guilds logging is not supported")
            client.close()

        # Save all members
        print("Saving all members...")
        all_members_gen = client.get_all_members()
        all_members = []
        for member in all_members_gen:
            member_obj = {
                "id": member.id,
                "user_name": member.name,
                "global_name": member.global_name,
                # "avatar_url": member.avatar.url, # TODO: Fix this: AttributeError: 'NoneType' object has no attribute 'url'
                # "banner_url": member.banner.url,
                "created_at": str(member.created_at)
            }
            all_members.append(member_obj)
        try:
            with open('data/members.json', 'w', encoding='utf-8') as f:
                json.dump(all_members, f, ensure_ascii=False, indent=4)
                print("Members data saved to data/members.json successfully!")
        except Exception as e:
            print(f"Error saving members data: {e}")
        
        # Save all channels
        print("Saving all channels...")
        all_channels_gen = client.get_all_channels()
        all_channels = []
        for channel in all_channels_gen:
            channel_obj = {
                "id": channel.id,
                "name": channel.name,
            }
            all_channels.append(channel_obj)
        try:
            with open('data/channels.json', 'w', encoding='utf-8') as f:
                json.dump(all_channels, f, ensure_ascii=False, indent=4)
                print("Channels data saved to data/channels.json successfully!")
        except Exception as e:
            print(f"Error saving channels data: {e}")

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')
        # TODO: Store the message
# ==== End of bot's logic ====

# ==== Start of Intents, permissions, and tokens ====
intents = discord.Intents.all()

client = MyClient(intents=intents)
load_dotenv()
token = os.getenv("BOT_TOKEN")
# ==== End of Intents, permissions, and tokens ====

# ==== Start of main logic ====
client.run(token)

# ==== End of main logic ====