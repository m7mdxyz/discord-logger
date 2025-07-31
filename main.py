# ==== Start of imports ===== 
import discord
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field, create_engine, Session, Relationship, select
from typing import Optional, List
from sqlalchemy import JSON as SQLAlchemyJSON
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
            content=message.clean_content,
            deleted_at=deleted_at
        )
        with Session(engine) as session:
            session.add(deleted_message_instance)
            session.commit()


        # Find the log channel
        # log_channel = self.get_channel(self.log_channel_id)
        # log_channel = message.channel
        # set channel to 1400089569537298453
        log_channel = self.get_channel(1400089569537298453)
        # print(type(log_channel))
        if not log_channel:
            print(f"Log channel with ID {log_channel} not found.")
            return


        # Prepare data for JSON logging
        # deleted_message_data = {
        #     "message_id": message.id,
        #     "guild_id": message.guild.id,
        #     "guild_name": message.guild.name,
        #     "channel_id": message.channel.id,
        #     "channel_name": message.channel.name,
        #     "author_id": message.author.id,
        #     "author_name": str(message.author), # Use str(message.author) for "Name#Discriminator" or just "Name"
        #     "author_display_name": message.author.display_name,
        #     "message_content": message.content,
        #     "sent_at_utc": message.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
        #     "deleted_at_utc": deleted_at.strftime('%Y-%m-%d %H:%M:%S UTC')
        # }

        # # Define the filename for deleted message logs
        # deleted_messages_filename = "data/deleted_messages_log.json"

        # # Load existing data or create an empty list
        # try:
        #     with open(deleted_messages_filename, 'r', encoding='utf-8') as f:
        #         log_entries = json.load(f)
        # except (FileNotFoundError, json.JSONDecodeError):
        #     log_entries = [] # File doesn't exist or is empty/corrupted, start with an empty list

        # # Append the new deleted message data
        # log_entries.append(deleted_message_data)

        # # Save the updated data back to the JSON file
        # try:
        #     with open(deleted_messages_filename, 'w', encoding='utf-8') as f:
        #         json.dump(log_entries, f, ensure_ascii=False, indent=4)
        #     print(f"Successfully logged deleted message to {deleted_messages_filename}")
        # except IOError as e:
        #     print(f"Error saving deleted message log to file: {e}")


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
        
        with Session(engine) as session:
            session.add(edited_message_instance)
            session.commit()

        # Get the log channel
        # log_channel = self.get_channel(self.log_channel_id) # Use your defined log channel ID
        log_channel = self.get_channel(1400105881617567845)
        if not log_channel:
            print(f"Log channel with ID {self.log_channel_id} not found for edited messages.")
            return

        # # Prepare data for JSON logging
        # edited_message_data = {
        #     "message_id": after.id,
        #     "guild_id": after.guild.id,
        #     "guild_name": after.guild.name,
        #     "channel_id": after.channel.id,
        #     "channel_name": after.channel.name,
        #     "author_id": after.author.id,
        #     "author_name": str(after.author),
        #     "author_display_name": after.author.display_name,
        #     "content_before": before.content,
        #     "content_after": after.content,
        #     "sent_at_utc": after.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
        #     "edited_at_utc": edited_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
        #     "jump_url": after.jump_url
        # }

        # # Define the filename for edited message logs
        # edited_messages_filename = "data/edited_messages_log.json"

        # # Load existing data or create an empty list
        # try:
        #     with open(edited_messages_filename, 'r', encoding='utf-8') as f:
        #         log_entries = json.load(f)
        # except (FileNotFoundError, json.JSONDecodeError):
        #     log_entries = []

        # # Append the new edited message data
        # log_entries.append(edited_message_data)

        # # Save the updated data back to the JSON file
        # try:
        #     with open(edited_messages_filename, 'w', encoding='utf-8') as f:
        #         json.dump(log_entries, f, ensure_ascii=False, indent=4)
        #     print(f"Successfully logged edited message to {edited_messages_filename}")
        # except IOError as e:
        #     print(f"Error saving edited message log to file: {e}")


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
            

        current_time_utc = datetime.utcnow()
        
        voice_activity_instance = voiceActivity(
            action=log_type,
            member_id=member.id,
            from_channel_id=from_channel_id,
            to_channel_id=to_channel_id,
            timestamp=current_time_utc
        )
        
        with Session(engine) as session:
            session.add(voice_activity_instance)
            session.commit()

            

        # Get the log channel
        log_channel = self.get_channel(1400106801562914889)
        if not log_channel:
            print(f"Log channel with ID {self.log_channel_id} not found for voice state updates.")
            return

        embed = None
        log_data = {}
        log_type = "" # To identify join/leave/move for JSON logging

        # Member joined a voice channel
        if before.channel is None and after.channel is not None:
            log_type = "voice_join"
            embed = discord.Embed(
                title=f"{member.display_name} joined voice channel",
                description=f"**Channel:** {after.channel.mention}",
                color=discord.Color.green() # Green for join
            )
            embed.set_author(name=f"{member.display_name} ({member})", icon_url=member.avatar)
            embed.add_field(name="User ID", value=member.id, inline=True)
            embed.add_field(name="Channel ID", value=after.channel.id, inline=True)
            embed.set_footer(text=f"Joined at: {current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")

            log_data = {
                "event_type": log_type,
                "timestamp_utc": current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
                "user_id": member.id,
                "user_name": str(member),
                "guild_id": member.guild.id,
                "guild_name": member.guild.name,
                "channel_id": after.channel.id,
                "channel_name": after.channel.name
            }

        # Member left a voice channel
        elif before.channel is not None and after.channel is None:
            log_type = "voice_leave"
            embed = discord.Embed(
                title=f"{member.display_name} left voice channel",
                description=f"**Channel:** {before.channel.mention}",
                color=discord.Color.red() # Red for leave
            )
            embed.set_author(name=f"{member.display_name} ({member})", icon_url=member.avatar)
            embed.add_field(name="User ID", value=member.id, inline=True)
            embed.add_field(name="Channel ID", value=before.channel.id, inline=True)
            embed.set_footer(text=f"Left at: {current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")

            log_data = {
                "event_type": log_type,
                "timestamp_utc": current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
                "user_id": member.id,
                "user_name": str(member),
                "guild_id": member.guild.id,
                "guild_name": member.guild.name,
                "channel_id": before.channel.id,
                "channel_name": before.channel.name
            }

        # Member moved voice channels
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            log_type = "voice_move"
            embed = discord.Embed(
                title=f"{member.display_name} moved voice channels",
                description=f"**From:** {before.channel.mention}\n**To:** {after.channel.mention}",
                color=discord.Color.blue() # Blue for move (or orange)
            )
            embed.set_author(name=f"{member.display_name} ({member})", icon_url=member.avatar)
            embed.add_field(name="User ID", value=member.id, inline=True)
            embed.add_field(name="From Channel ID", value=before.channel.id, inline=True)
            embed.add_field(name="To Channel ID", value=after.channel.id, inline=True)
            embed.set_footer(text=f"Moved at: {current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")

            log_data = {
                "event_type": log_type,
                "timestamp_utc": current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
                "user_id": member.id,
                "user_name": str(member),
                "guild_id": member.guild.id,
                "guild_name": member.guild.name,
                "from_channel_id": before.channel.id,
                "from_channel_name": before.channel.name,
                "to_channel_id": after.channel.id,
                "to_channel_name": after.channel.name
            }
        # You could add more conditions here for mute/deafen/stream changes if desired

        # If an embed was created, send it to Discord and log to JSON
        if embed:
            # Save to JSON file
            # voice_log_filename = "data/voice_channel_log.json"
            # try:
            #     with open(voice_log_filename, 'r', encoding='utf-8') as f:
            #         log_entries = json.load(f)
            # except (FileNotFoundError, json.JSONDecodeError):
            #     log_entries = []

            # log_entries.append(log_data)

            # try:
            #     with open(voice_log_filename, 'w', encoding='utf-8') as f:
            #         json.dump(log_entries, f, ensure_ascii=False, indent=4)
            #     print(f"Successfully logged {log_type} event to {voice_log_filename}")
            # except IOError as e:
            #     print(f"Error saving {log_type} log to file: {e}")

            # Send to Discord channel
            try:
                await log_channel.send(embed=embed)
                print(f"Sent {log_type} log to Discord channel {log_channel.name}")
            except discord.Forbidden:
                print(f"Bot does not have permissions to send messages in log channel {log_channel.name}")
            except discord.HTTPException as e:
                print(f"Failed to send {log_type} log to Discord: {e}")

    # Logging joining the guild
    async def on_member_join(self, member):
        """
        Logs when a new member joins the guild.
        """
        if member.bot:
            return

        log_channel = self.get_channel(1400109597712318464)
        if not log_channel:
            print(f"Log channel with ID {self.log_channel_id} not found for member join.")
            return

        # --- FIX STARTS HERE ---
        # Get the current time as a timezone-aware UTC datetime object
        current_time_utc = datetime.now(timezone.utc)
        
        # member.created_at is already a timezone-aware UTC datetime object from discord.py
        # Now, both datetimes are timezone-aware and in the same timezone (UTC),
        # so subtraction will work correctly.
        account_age = current_time_utc - member.created_at
        # --- FIX ENDS HERE ---

        embed = discord.Embed(
            title="Member Joined",
            description=f"{member.mention} {member}",
            color=discord.Color.green() # Green for join
        )
        embed.set_thumbnail(url=member.avatar)
        embed.add_field(name="Account Age", value=f"{account_age.days // 365} years, {(account_age.days % 365) // 30} months, {account_age.days % 30} days", inline=False)
        embed.set_footer(text=f"ID: {member.id} • Joined at: {current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        # JSON Logging
        log_data = {
            "event_type": "member_join",
            "timestamp_utc": current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "user_id": member.id,
            "user_name": str(member),
            "guild_id": member.guild.id,
            "guild_name": member.guild.name,
            "account_created_at_utc": member.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "account_age_days": account_age.days
        }
        self._save_log_to_json("data/members_log.json", log_data) # Helper function to save JSON

        try:
            await log_channel.send(embed=embed)
            print(f"Logged member join: {member} in {member.guild.name}")
        except discord.Forbidden:
            print(f"Bot does not have permissions to send messages in log channel {log_channel.name}")
        except discord.HTTPException as e:
            print(f"Failed to send member join log: {e}")
    
    # Logging leaving the guild
    async def on_member_remove(self, member):
        """
        Logs when a member leaves or is kicked from the guild.
        (Note: Doesn't differentiate between leave and kick directly, use audit logs for that)
        """
        if member.bot:
            return

        log_channel = self.get_channel(1400109636211834973)
        if not log_channel:
            print(f"Log channel with ID {self.log_channel_id} not found for member leave.")
            return

        current_time_utc = datetime.utcnow()

        embed = discord.Embed(
            title="Member Left",
            description=f"{member.mention} {member}",
            color=discord.Color.red() # Red for leave
        )
        embed.set_thumbnail(url=member.avatar)
        embed.set_footer(text=f"ID: {member.id} • Left at: {current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        # JSON Logging
        log_data = {
            "event_type": "member_leave",
            "timestamp_utc": current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "user_id": member.id,
            "user_name": str(member),
            "guild_id": member.guild.id,
            "guild_name": member.guild.name
        }
        self._save_log_to_json("data/members_log.json", log_data)

        try:
            await log_channel.send(embed=embed)
            print(f"Logged member leave: {member} from {member.guild.name}")
        except discord.Forbidden:
            print(f"Bot does not have permissions to send messages in log channel {log_channel.name}")
        except discord.HTTPException as e:
            print(f"Failed to send member leave log: {e}")

    # Logging member update
    async def on_member_update(self, before, after):
        """
        Logs when a member's roles are changed or when they are timed out.
        """
        if after.bot:
            return

        log_channel = self.get_channel(1400109675667525743)
        if not log_channel:
            print(f"Log channel with ID {self.log_channel_id} not found for member updates.")
            return

        current_time_utc = datetime.now(timezone.utc) # Ensure this is timezone-aware UTC

        # --- Role Changes Logging (Existing) ---
        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]

            if added_roles:
                for role in added_roles:
                    embed = discord.Embed(
                        title=f"{after.display_name} was given a role",
                        description=f"{after.mention} was given the {role.mention} role",
                        color=discord.Color.blue()
                    )
                    embed.set_author(name=f"{after.display_name} ({after})", icon_url=after.avatar.url if after.avatar else discord.Embed.Empty)
                    embed.set_footer(text=f"ID: {after.id} • {current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")

                    log_data = {
                        "event_type": "role_added",
                        "timestamp_utc": current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
                        "user_id": after.id,
                        "user_name": str(after),
                        "guild_id": after.guild.id,
                        "guild_name": after.guild.name,
                        "role_id": role.id,
                        "role_name": role.name
                    }
                    self._save_log_to_json("data/members_log.json", log_data)

                    try:
                        await log_channel.send(embed=embed)
                        print(f"Logged role added: {role.name} to {after}")
                    except discord.Forbidden:
                        print(f"Bot does noß have permissions to send messages in log channel {log_channel.name}")
                    except discord.HTTPException as e:
                        print(f"Failed to send role add log: {e}")

            if removed_roles:
                for role in removed_roles:
                    embed = discord.Embed(
                        title=f"{after.display_name} was removed from a role",
                        description=f"{after.mention} was removed from the {role.mention} role",
                        color=discord.Color.orange()
                    )
                    embed.set_author(name=f"{after.display_name} ({after})", icon_url=after.avatar.url if after.avatar else discord.Embed.Empty)
                    embed.set_footer(text=f"ID: {after.id} • {current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")

                    log_data = {
                        "event_type": "role_removed",
                        "timestamp_utc": current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
                        "user_id": after.id,
                        "user_name": str(after),
                        "guild_id": after.guild.id,
                        "guild_name": after.guild.name,
                        "role_id": role.id,
                        "role_name": role.name
                    }
                    self._save_log_to_json("data/members_log.json", log_data)

                    try:
                        await log_channel.send(embed=embed)
                        print(f"Logged role removed: {role.name} from {after}")
                    except discord.Forbidden:
                        print(f"Bot does not have permissions to send messages in log channel {log_channel.name}")
                    except discord.HTTPException as e:
                        print(f"Failed to send role remove log: {e}")

        # --- Timeout Logging ---
        if before.timed_out_until != after.timed_out_until:
            # Member was put in timeout
            if after.timed_out_until is not None:
                # Calculate duration if possible (only if it's a new timeout, not just an update to an existing one)
                timeout_duration = after.timed_out_until - current_time_utc
                
                embed = discord.Embed(
                    title="Member Timed Out",
                    description=f"{after.mention} {after} was put in timeout.",
                    color=discord.Color.dark_purple() # A color for timeout
                )
                embed.set_author(name=f"{after.display_name} ({after})", icon_url=after.avatar.url if after.avatar else discord.Embed.Empty)
                embed.add_field(name="Timeout Ends", value=f"<t:{int(after.timed_out_until.timestamp())}:F>", inline=False) # Discord timestamp format
                embed.add_field(name="Duration", value=f"{timeout_duration.days} days, {timeout_duration.seconds // 3600} hours, {(timeout_duration.seconds % 3600) // 60} minutes, {timeout_duration.seconds % 60} seconds", inline=False)
                embed.set_footer(text=f"ID: {after.id} • Timed out at: {current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")

                log_data = {
                    "event_type": "member_timed_out",
                    "timestamp_utc": current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
                    "user_id": after.id,
                    "user_name": str(after),
                    "guild_id": after.guild.id,
                    "guild_name": after.guild.name,
                    "timeout_ends_utc": after.timed_out_until.strftime('%Y-%m-%d %H:%M:%S UTC'),
                    "timeout_duration_seconds": timeout_duration.total_seconds()
                }
                self._save_log_to_json("data/members_log.json", log_data) # Using the same member_log for consistency

                try:
                    await log_channel.send(embed=embed)
                    print(f"Logged member timed out: {after} in {after.guild.name}")
                except discord.Forbidden:
                    print(f"Bot does not have permissions to send messages in log channel {log_channel.name}")
                except discord.HTTPException as e:
                    print(f"Failed to send member timeout log: {e}")

            # Member's timeout ended or was removed
            elif before.timed_out_until is not None and after.timed_out_until is None:
                embed = discord.Embed(
                    title="Member Timeout Removed",
                    description=f"{after.mention} {after}'s timeout was removed.",
                    color=discord.Color.dark_green() # A different color for timeout removal
                )
                embed.set_author(name=f"{after.display_name} ({after})", icon_url=after.avatar.url if after.avatar else discord.Embed.Empty)
                embed.set_footer(text=f"ID: {after.id} • Timeout removed at: {current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")

                log_data = {
                    "event_type": "member_timeout_removed",
                    "timestamp_utc": current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
                    "user_id": after.id,
                    "user_name": str(after),
                    "guild_id": after.guild.id,
                    "guild_name": after.guild.name,
                    "previous_timeout_ends_utc": before.timed_out_until.strftime('%Y-%m-%d %H:%M:%S UTC') if before.timed_out_until else "N/A"
                }
                self._save_log_to_json("data/members_log.json", log_data)

                try:
                    await log_channel.send(embed=embed)
                    print(f"Logged member timeout removed: {after} in {after.guild.name}")
                except discord.Forbidden:
                    print(f"Bot does not have permissions to send messages in log channel {log_channel.name}")
                except discord.HTTPException as e:
                    print(f"Failed to send member timeout removal log: {e}")
    # Logging member ban from guild
    async def on_member_ban(self, guild, user):
        """
        Logs when a member is banned from the guild.
        """
        log_channel = self.get_channel(1400109675667525743)
        if not log_channel:
            print(f"Log channel with ID {self.log_channel_id} not found for member ban.")
            return

        current_time_utc = datetime.utcnow()

        embed = discord.Embed(
            title="Member Banned",
            description=f"{user.mention} {user} was banned.",
            color=discord.Color.dark_red() # Dark red for ban
        )
        embed.set_author(name=f"{user.display_name} ({user})", icon_url=user.avatar)
        embed.set_footer(text=f"ID: {user.id} • Banned at: {current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        # JSON Logging
        log_data = {
            "event_type": "member_banned",
            "timestamp_utc": current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "user_id": user.id,
            "user_name": str(user),
            "guild_id": guild.id,
            "guild_name": guild.name
        }
        self._save_log_to_json("data/members_log.json", log_data)

        try:
            await log_channel.send(embed=embed)
            print(f"Logged member ban: {user} in {guild.name}")
        except discord.Forbidden:
            print(f"Bot does not have permissions to send messages in log channel {log_channel.name}")
        except discord.HTTPException as e:
            print(f"Failed to send member ban log: {e}")

    # Logging member unban
    async def on_member_unban(self, guild, user):
        """
        Logs when a member is unbanned from the guild.
        """
        log_channel = self.get_channel(1400109675667525743)
        if not log_channel:
            print(f"Log channel with ID {self.log_channel_id} not found for member unban.")
            return

        current_time_utc = datetime.utcnow()

        embed = discord.Embed(
            title="Member Unbanned",
            description=f"{user.mention} {user} was unbanned.",
            color=discord.Color.green() # Green for unban
        )
        embed.set_author(name=f"{user.display_name} ({user})", icon_url=user.avatar)
        embed.set_footer(text=f"ID: {user.id} • Unbanned at: {current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        # JSON Logging
        log_data = {
            "event_type": "member_unbanned",
            "timestamp_utc": current_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "user_id": user.id,
            "user_name": str(user),
            "guild_id": guild.id,
            "guild_name": guild.name
        }
        self._save_log_to_json("data/members_log.json", log_data)

        try:
            await log_channel.send(embed=embed)
            print(f"Logged member unban: {user} in {guild.name}")
        except discord.Forbidden:
            print(f"Bot does not have permissions to send messages in log channel {log_channel.name}")
        except discord.HTTPException as e:
            print(f"Failed to send member unban log: {e}")

    # Helper function to save logs to JSON (add this to your MyClient class)
    def _save_log_to_json(self, filename, new_entry):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                log_entries = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            log_entries = []

        log_entries.append(new_entry)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(log_entries, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Error saving log to {filename}: {e}")

# ==== End of bot's logic ====

# ==== Start of SQL Schema ====
class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    member_id: Optional[int] = Field(foreign_key="member.id")
    channel_id: Optional[int] = Field(foreign_key="channel.id")
    content: Optional[str] = Field(max_length=2000)
    created_at: Optional[datetime]
    
    member: "Member" = Relationship(back_populates="messages")
    channel: "Channel" = Relationship(back_populates="messages")

class Member(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(max_length=256)
    global_name: Optional[str] = Field(max_length=256)
    avatar_url: Optional[str] = Field(max_length=256)
    created_at: Optional[datetime]
    roles_json: Optional[str] = Field()
    
    messages: List[Message] = Relationship(back_populates="member")

class Channel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(max_length=256)
    ch_type: Optional[str] = Field(max_length=256)
    
    messages: List[Message] = Relationship(back_populates="channel")
    
class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(max_length=256)
    color: Optional[str] = Field(max_length=256)
    permissions: Optional[int] = Field()
    created_at: Optional[datetime]

class DeletedMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    message_id: Optional[int] = Field(default=None) # Use this to find user_id, content, and all dat shit
    content: Optional[str] = Field(max_length=256)
    deleted_at: Optional[datetime]
    
class EditedMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    message_id: Optional[int] = Field(default=None) # Use this to find user_id, content, and all dat shit
    content_before: Optional[str] = Field(max_length=2000)
    content_after: Optional[str] = Field(max_length=2000)
    edited_at: Optional[datetime]
    
class voiceActivity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    member_id: Optional[int] = Field()
    action: Optional[str] = Field(max_length=256)
    from_channel_id: Optional[int] = Field()
    to_channel_id: Optional[int] = Field()
    timestamp: Optional[datetime]

# ==== End of SQL Schema ====

# ==== Start of Intents, permissions, and tokens ====
intents = discord.Intents.all()

client = MyClient(intents=intents)
load_dotenv()
token = os.getenv("BOT_TOKEN")
# ==== End of Intents, permissions, and tokens ====

# ==== Start of main logic ====

engine = create_engine("sqlite:///database/orm.db")
SQLModel.metadata.create_all(engine)



client.run(token)


# ==== End of main logic ====