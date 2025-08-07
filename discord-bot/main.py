# ==== Start of imports ===== 
import discord
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timezone

from sqlmodel import SQLModel, Session, select

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))  # adds project root

from database.schema import *
from database.db import engine

# ==== End of imports ====

# ==== Start of bot's logic ====
class MyClient(discord.Client):
    async def on_ready(self):
        
        # Setting things up
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
        with Session(engine) as session:
            for member in all_members_gen:
                member_instance = Member(
                    id= member.id,
                    name= member.name,
                    global_name=member.global_name,
                    avatar_url=str(member.avatar),
                    roles_json=json.dumps([role.id for role in member.roles]),
                    created_at=member.created_at
                )
                
                existing = session.get(Member, member_instance.id)
                if existing:
                    continue
                
                session.add(member_instance)
                session.commit()
        print("Saved all members")
        
        # Save all channels
        print("Saving all channels...")
        all_channels_gen = client.get_all_channels()
        with Session(engine) as session:
            for channel in all_channels_gen:
                channel_instance = Channel(
                    id=channel.id,
                    name=channel.name,
                    ch_type=str(channel.type)
                )
                
                existing = session.get(Channel, channel_instance.id)
                if existing:
                    continue
    
                session.add(channel_instance)
                session.commit()
        print("Saved all channels")                   
            
        # Save all roles in the Guild.
        print("Save all roles in the Guild...")
        all_roles = client.guilds[0].roles
        
        with Session(engine) as session:
            for role in all_roles:
                role_instance = Role(
                    id=role.id,
                    name=role.name,
                    color=f"#{role.color.value:06x}",
                    permissions=role.permissions.value,
                    created_at=role.created_at,
                )
                
                existing = session.get(Role, role_instance.id)
                if existing:
                    continue
    
                session.add(role_instance)
                session.commit()
        
        
        # ==== Set Log Channels ====        
        log_to_discord = os.getenv("LOG_TO_DISCORD", "false").lower()
        if log_to_discord != "true":
            return
        
        json_path = "discord-bot/log_channels.json"
        with open(json_path, "r") as f:
            log_data = json.load(f)
        
        guild = client.guilds[0]
        updated = False

        # Step 1: Create or fetch the log category
        log_category_id = log_data.get("log_category_id")
        log_category = None

        if log_category_id is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.owner: discord.PermissionOverwrite(read_messages=True)
            }
            log_category = await guild.create_category("Logs", overwrites=overwrites)
            log_data["log_category_id"] = log_category.id
            updated = True
        else:
            log_category = discord.utils.get(guild.categories, id=log_category_id)

        # Step 2: Create missing channels
        channel_map = {
            "deleted_messages_channel_id": "deleted-messages",
            "edited_messages_channel_id": "edited-messages",
            "voice_activity_channel_id": "voice-activity",
            "guild_activity_channel_id": "guild-activity",
            "members_activity_channel_id": "member-activity"
        }

        for key, name in channel_map.items():
            if log_data.get(key) is None:
                existing_channel = discord.utils.get(guild.text_channels, name=name)
                if existing_channel:
                    log_data[key] = existing_channel.id
                else:
                    new_channel = await guild.create_text_channel(name, category=log_category)
                    log_data[key] = new_channel.id
                updated = True

        # Step 3: Save changes
        if updated:
            with open(json_path, "w") as f:
                json.dump(log_data, f, indent=4)

        print("Log channels verified/created successfully.")

        

    async def on_message(self, message: discord.Message):
        
        if message.author == self.user:
            return
        if message.guild is None:
            return
        
        message_instance = Message(
            id=message.id,
            member_id=message.author.id,
            channel_id=message.channel.id,
            content=message.clean_content,
            created_at=message.created_at
        )
        with Session(engine) as session:
            session.add(message_instance)
            session.commit()
        
    # Logging deleted messages
    async def on_message_delete(self, message: discord.Message):
        """
        This event is called when a message is deleted.
        """
        # Ignore messages from the bot itself to prevent infinite loops if the bot deletes its own messages
        if message.author == self.user:
            return

        # Ignore DMs, as messages can only be deleted in guilds for this purpose
        if message.guild is None:
            return
        
        # Get the current time when the message was deleted
        deleted_at = datetime.utcnow()
                
        deleted_message_instance = DeletedMessage(
        message_id=message.id,
        deleted_at=deleted_at
        )
        with Session(engine) as session:
            session.add(deleted_message_instance)
            session.commit()
                
        log_to_discord = os.getenv("LOG_TO_DISCORD", "false").lower()
        if log_to_discord != "true":
            return
        # Find the log channel
        log_channels_json = get_log_channel_json()
        log_channel = self.get_channel(log_channels_json.get("deleted_messages_channel_id"))
        if not log_channel:
            print(f"Log channel with ID {log_channel} not found.")
            return

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
            # print(f"Sent deleted message log to Discord channel {log_channel.name}")
        except discord.Forbidden:
            print(f"Bot does not have permissions to send messages in log channel {log_channel.name}")
        except discord.HTTPException as e:
            print(f"Failed to send deleted message log to Discord: {e}")
    
    # Logging edited messages
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """
        This event is called when a message is edited.
        """
        # Ignore messages from the bot itself
        if after.author == self.user:
            return

        # Ignore DMs
        if after.guild is None:
            return

        # Ignore if the content hasn't actually changed (e.g., embed added/removed, pinned state changed)
        if before.content == after.content:
            return
        
        # Get the current time when the message was edited
        edited_at = datetime.utcnow()

        edited_message_instance = EditedMessage(
            message_id=after.id,
            content_before=before.clean_content,
            content_after=after.clean_content,
            edited_at=edited_at
        )

        # Update the message content and is_edited flag in Message table
        with Session(engine) as session:
            statement = select(Message).where(Message.id == after.id)
            message_to_update = session.exec(statement).first()
            if message_to_update:
                message_to_update.content = after.clean_content
                message_to_update.is_edited = True
                session.add(message_to_update)
            
            session.add(edited_message_instance)
            session.commit()
        
        log_to_discord = os.getenv("LOG_TO_DISCORD", "false").lower()
        if log_to_discord != "true":
            return
        # Get the log channel
        log_channels_json = get_log_channel_json()
        log_channel = self.get_channel(log_channels_json.get("edited_messages_channel_id"))
        if not log_channel:
            print(f"Log channel with ID {log_channel} not found for edited messages.")
            return

        # Create an embed for Discord channel logging
        embed = discord.Embed(
            title="Message Edited",
            color=discord.Color.blue() # A common color for edit events
        )

        embed.set_author(name=f"{after.author.display_name} ({after.author})", icon_url=after.author.avatar)
        embed.add_field(name="Channel", value=after.channel.mention, inline=True)
        embed.add_field(name="Message ID", value=after.id, inline=True)
        embed.add_field(name="Author ID", value=after.author.id, inline=True)

        # Add "Before" and "After" content
        embed.add_field(name="Before", value=f"```{before.content}```" if before.content else "*(No content)*", inline=False)
        embed.add_field(name="After", value=f"```{after.content}```" if after.content else "*(No content)*", inline=False)

        embed.add_field(name="Sent at", value=after.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'), inline=False)
        embed.add_field(name="Edited at", value=edited_at.strftime('%Y-%m-%d %H:%M:%S UTC'), inline=False)

        # Add the "Jump to Message" link
        embed.add_field(name="Jump to Message", value=f"[Click Here]({after.jump_url})", inline=False)

        try:
            await log_channel.send(embed=embed)
            print(f"Sent edited message log to Discord channel {log_channel.name}")
        except discord.Forbidden:
            print(f"Bot does not have permissions to send messages in log channel {log_channel.name}")
        except discord.HTTPException as e:
            print(f"Failed to send edited message log to Discord: {e}")

    # Logging Voice channels
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """
        This event is called when a member's voice state changes.
        (e.g., joining, leaving, moving, muting, deafening voice channels)
        """
        # Ignore bots
        if member.bot:
            return

        # Ensure we are only logging within guilds
        if member.guild is None:
            return
        
        log_type = ""
        from_channel_id = None
        to_channel_id = None
        details = {}
        
        # Channel join/leave/move events
        if before.channel is None and after.channel is not None:
            log_type = "voice_join"
            to_channel_id = after.channel.id
        elif before.channel is not None and after.channel is None:
            log_type = "voice_leave"
            from_channel_id = before.channel.id
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            log_type = "voice_move"
            from_channel_id = before.channel.id
            to_channel_id = after.channel.id
        
        # Check for other voice state changes only if no channel change was detected
        if not log_type:
            # Server mute/unmute events
            if before.mute != after.mute:
                log_type = "voice_mute" if after.mute else "voice_unmute"
                details['mute_status'] = after.mute
            
            # Server deafen/undeafen events
            elif before.deaf != after.deaf:
                log_type = "voice_deafen" if after.deaf else "voice_undeafen"
                details['deafen_status'] = after.deaf
            
            # Self-deafen/self-undeafen events (check before self-mute to prioritize)
            elif before.self_deaf != after.self_deaf:
                log_type = "voice_self_deafen" if after.self_deaf else "voice_self_undeafen"
                details['self_deafen_status'] = after.self_deaf
            
            # Self-mute/self-unmute events
            elif before.self_mute != after.self_mute:
                # Only log self-mute if self-deafen is not also changing
                if before.self_deaf == after.self_deaf:
                    log_type = "voice_self_mute" if after.self_mute else "voice_self_unmute"
                    details['self_mute_status'] = after.self_mute
            
            # Video start/stop events
            elif before.self_video != after.self_video:
                log_type = "video_start" if after.self_video else "video_stop"
                details['video_status'] = after.self_video
            
            # Streaming start/stop events
            elif before.self_stream != after.self_stream:
                log_type = "streaming_start" if after.self_stream else "streaming_stop"
                details['streaming_status'] = after.self_stream
        
        # If no voice state change was detected, return
        if not log_type:
            return

        current_time_utc = datetime.utcnow()
        
        # Convert details to JSON for storage
        details_json = json.dumps(details) if details else None
        
        voice_activity_instance = VoiceActivity(
            action=log_type,
            member_id=member.id,
            from_channel_id=from_channel_id,
            to_channel_id=to_channel_id,
            timestamp=current_time_utc,
            details=details_json
        )
        
        with Session(engine) as session:
            session.add(voice_activity_instance)
            session.commit()

        # Get the log channel
        log_to_discord = os.getenv("LOG_TO_DISCORD", "false").lower()
        if log_to_discord != "true":
            return
        # Get the log channel
        log_channels_json = get_log_channel_json()
        log_channel = self.get_channel(log_channels_json.get("voice_activity_channel_id"))
        if not log_channel:
            print(f"Log channel with ID {log_channel} not found for voice state updates.")
            return

        embed = None
        color = None

        # Handle different voice activity types
        if log_type == "voice_join":
            embed = discord.Embed(
                title=f"{member.display_name} joined voice channel",
                description=f"**Channel:** {after.channel.mention}",
                color=discord.Color.green()
            )
            color = discord.Color.green
            
        elif log_type == "voice_leave":
            embed = discord.Embed(
                title=f"{member.display_name} left voice channel",
                description=f"**Channel:** {before.channel.mention}",
                color=discord.Color.red()
            )
            color = discord.Color.red
            
        elif log_type == "voice_move":
            embed = discord.Embed(
                title=f"{member.display_name} moved voice channels",
                description=f"**From:** {before.channel.mention}\n**To:** {after.channel.mention}",
                color=discord.Color.blue()
            )
            color = discord.Color.blue
            
        elif log_type == "voice_mute":
            embed = discord.Embed(
                title=f"{member.display_name} was server muted",
                description=f"**Channel:** {before.channel.mention if before.channel else 'N/A'}",
                color=discord.Color.orange()
            )
            color = discord.Color.orange
            
        elif log_type == "voice_unmute":
            embed = discord.Embed(
                title=f"{member.display_name} was server unmuted",
                description=f"**Channel:** {before.channel.mention if before.channel else 'N/A'}",
                color=discord.Color.dark_green()
            )
            color = discord.Color.dark_green
            
        elif log_type == "voice_deafen":
            embed = discord.Embed(
                title=f"{member.display_name} was server deafened",
                description=f"**Channel:** {before.channel.mention if before.channel else 'N/A'}",
                color=discord.Color.dark_red()
            )
            color = discord.Color.dark_red
            
        elif log_type == "voice_undeafen":
            embed = discord.Embed(
                title=f"{member.display_name} was server undeafened",
                description=f"**Channel:** {before.channel.mention if before.channel else 'N/A'}",
                color=discord.Color.purple()
            )
            color = discord.Color.purple
            
        elif log_type == "voice_self_mute":
            embed = discord.Embed(
                title=f"{member.display_name} self-muted",
                description=f"**Channel:** {before.channel.mention if before.channel else 'N/A'}",
                color=discord.Color.gold()
            )
            color = discord.Color.gold
            
        elif log_type == "voice_self_unmute":
            embed = discord.Embed(
                title=f"{member.display_name} self-unmuted",
                description=f"**Channel:** {before.channel.mention if before.channel else 'N/A'}",
                color=discord.Color.magenta()
            )
            color = discord.Color.magenta
            
        elif log_type == "voice_self_deafen":
            embed = discord.Embed(
                title=f"{member.display_name} self-deafened",
                description=f"**Channel:** {before.channel.mention if before.channel else 'N/A'}",
                color=discord.Color.dark_grey()
            )
            color = discord.Color.dark_grey
            
        elif log_type == "voice_self_undeafen":
            embed = discord.Embed(
                title=f"{member.display_name} self-undeafened",
                description=f"**Channel:** {before.channel.mention if before.channel else 'N/A'}",
                color=discord.Color.light_grey()
            )
            color = discord.Color.light_grey
            
        elif log_type == "video_start":
            embed = discord.Embed(
                title=f"{member.display_name} started video",
                description=f"**Channel:** {before.channel.mention if before.channel else 'N/A'}",
                color=discord.Color.teal()
            )
            color = discord.Color.teal
            
        elif log_type == "video_stop":
            embed = discord.Embed(
                title=f"{member.display_name} stopped video",
                description=f"**Channel:** {before.channel.mention if before.channel else 'N/A'}",
                color=discord.Color.dark_teal()
            )
            color = discord.Color.dark_teal
            
        elif log_type == "streaming_start":
            embed = discord.Embed(
                title=f"{member.display_name} started streaming",
                description=f"**Channel:** {before.channel.mention if before.channel else 'N/A'}",
                color=discord.Color.red()
            )
            color = discord.Color.red
            
        elif log_type == "streaming_stop":
            embed = discord.Embed(
                title=f"{member.display_name} stopped streaming",
                description=f"**Channel:** {before.channel.mention if before.channel else 'N/A'}",
                color=discord.Color.dark_red()
            )
            color = discord.Color.dark_red

        if embed:
            embed.set_author(name=f"{member.display_name} ({member})", icon_url=member.avatar)
            embed.add_field(name="User ID", value=member.id, inline=True)
            embed.set_footer(text=f"ID: {member.id} • {current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")

            try:
                await log_channel.send(embed=embed)
                print(f"Sent {log_type} log to Discord channel {log_channel.name}")
            except discord.Forbidden:
                print(f"Bot does not have permissions to send messages in log channel {log_channel.name}")
            except discord.HTTPException as e:
                print(f"Failed to send {log_type} log to Discord: {e}")

# Public function
def get_log_channel_json():
    json_path = "discord-bot/log_channels.json"
    with open(json_path, "r") as f:
        log_data = json.load(f)
        return log_data
    
# ==== End of bot's logic ====

# ==== Start of Intents, permissions, and tokens ====
intents = discord.Intents.all()

client = MyClient(intents=intents)
load_dotenv()
# ==== End of Intents, permissions, and tokens ====

# ==== Start of main logic ====

SQLModel.metadata.create_all(engine)

client.run(os.getenv("BOT_TOKEN"))

# ==== End of main logic ====
