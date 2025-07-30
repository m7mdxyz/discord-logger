# ==== Start of imports ===== 
import discord
from dotenv import load_dotenv
import os
import json
from datetime import datetime
# ==== End of imports ====

# ==== Start of bot's logic ====
class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        print(f'Bot ID: {self.user.id}')
        activity = discord.Activity(type=discord.ActivityType.listening, name="Logging..")
        await self.change_presence(status=discord.Status.dnd, activity=activity)
        print("Bot presence set to: Watching 'for deleted messages'")
    
        # Make sure the bot is logging one server only
        if client.guilds.__len__() > 1:
            print(f"The bot have joined {client.guilds.__len__()} guilds. Multiple guilds logging is not supported")
            await client.close()
            
        # ========================================================

        # Save all members
        print("Saving all members...")
        all_members_gen = client.get_all_members()
        all_members = []
        for member in all_members_gen:
            member_obj = {
                "id": member.id,
                "user_name": member.name,
                "global_name": member.global_name,
                "avatar_url": str(member.avatar),
                "banner_url": str(member.banner),
                "created_at": str(member.created_at),
                "joined_at": member.joined_at.isoformat(),
                "roles": [role.id for role in member.roles]
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
            
            
        # Save all roles in the Guild.
        print("Save all roles in the Guild...")
        all_roles = client.guilds[0].roles
        roles_data = []
        for role in all_roles:
            roles_data.append({
                "role_id": role.id,
                "name": role.name,
                "permissions": role.permissions.value,
                "color": f"#{role.color.value:06x}",
                "created_at": role.created_at.isoformat(),
            })
        
        try:
            with open('data/roles.json', 'w', encoding='utf-8') as f:
                json.dump(roles_data, f, ensure_ascii=False, indent=4)
                print("Roles data saved to data/roles.json successfully!")
        except Exception as e:
            print(f"Error saving roles data: {e}")


    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')
        # TODO: Store the message
        
    # Logging deleted messages
    async def on_message_delete(self, message):
        """
        This event is called when a message is deleted.
        """
        # Ignore messages from the bot itself to prevent infinite loops if the bot deletes its own messages
        if message.author == self.user:
            return

        # Ignore DMs, as messages can only be deleted in guilds for this purpose
        if message.guild is None:
            return

        # Find the log channel
        # log_channel = self.get_channel(self.log_channel_id)
        # log_channel = message.channel
        # set channel to 1400089569537298453
        log_channel = self.get_channel(1400089569537298453)
        print(type(log_channel))
        if not log_channel:
            print(f"Log channel with ID {log_channel} not found.")
            return

        # Get the current time when the message was deleted
        deleted_at = datetime.utcnow()

        # Prepare data for JSON logging
        deleted_message_data = {
            "message_id": message.id,
            "guild_id": message.guild.id,
            "guild_name": message.guild.name,
            "channel_id": message.channel.id,
            "channel_name": message.channel.name,
            "author_id": message.author.id,
            "author_name": str(message.author), # Use str(message.author) for "Name#Discriminator" or just "Name"
            "author_display_name": message.author.display_name,
            "message_content": message.content,
            "sent_at_utc": message.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "deleted_at_utc": deleted_at.strftime('%Y-%m-%d %H:%M:%S UTC')
        }

        # Define the filename for deleted message logs
        deleted_messages_filename = "data/deleted_messages_log.json"

        # Load existing data or create an empty list
        try:
            with open(deleted_messages_filename, 'r', encoding='utf-8') as f:
                log_entries = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            log_entries = [] # File doesn't exist or is empty/corrupted, start with an empty list

        # Append the new deleted message data
        log_entries.append(deleted_message_data)

        # Save the updated data back to the JSON file
        try:
            with open(deleted_messages_filename, 'w', encoding='utf-8') as f:
                json.dump(log_entries, f, ensure_ascii=False, indent=4)
            print(f"Successfully logged deleted message to {deleted_messages_filename}")
        except IOError as e:
            print(f"Error saving deleted message log to file: {e}")


        # Create an embed for a cleaner look (for Discord channel logging)
        embed = discord.Embed(
            title="Message Deleted",
            description=f"**Content:**\n```\n{message.content}\n```",
            color=discord.Color.red() # A common color for deletion events
        )

        embed.set_author(name=f"{message.author.display_name} ({message.author})", icon_url=message.author.avatar)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Message ID", value=message.id, inline=True)
        embed.add_field(name="Author ID", value=message.author.id, inline=True)
        embed.add_field(name="Sent at", value=message.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'), inline=False) # Changed to inline=False for better layout
        embed.add_field(name="Deleted at", value=deleted_at.strftime('%Y-%m-%d %H:%M:%S UTC'), inline=False) # Add this new field

        try:
            await log_channel.send(embed=embed)
            print(f"Sent deleted message log to Discord channel {log_channel.name}")
        except discord.Forbidden:
            print(f"Bot does not have permissions to send messages in log channel {log_channel.name}")
        except discord.HTTPException as e:
            print(f"Failed to send deleted message log to Discord: {e}")
        
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