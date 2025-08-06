import os
import json
from datetime import datetime
from flask import Flask, render_template
from sqlmodel import SQLModel, create_engine, Session, select, Field
from typing import List, Optional
from dotenv import load_dotenv


app = Flask(__name__)

# Add database connection
engine = create_engine("sqlite:///discord-bot/database/orm.db")


# Add a context processor to make the current year available to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Helper function to get deleted messages from database
def get_deleted_messages():
    """
    Get deleted messages from the database.
    
    Returns:
        list: List of deleted message records
    """
    with Session(engine) as session:
        statement = select(DeletedMessage, Message, Member, Channel).join(Message, DeletedMessage.message_id == Message.id).join(Member, Message.member_id == Member.id).join(Channel, Message.channel_id == Channel.id)
        results = session.exec(statement).all()
        
        messages = []
        for deleted_msg, message, member, channel in results:
            msg_data = {
                'id': deleted_msg.id,
                'message_id': deleted_msg.message_id,
                'content': message.content,
                'author_name': f"{member.name} ({member.global_name})",
                'author_id': member.id,
                'avatar_url': member.avatar_url,
                'channel_id': channel.id,
                'channel_name': channel.name,
                'timestamp': deleted_msg.deleted_at.isoformat(),
                'original_sent_at': message.created_at.isoformat() if message.created_at else None
            }
            messages.append(msg_data)
        
        return messages


# Helper function to get edited messages from database
def get_edited_messages():
    """
    Get edited messages from the database.
    
    Returns:
        list: List of edited message records
    """
    with Session(engine) as session:
        statement = select(EditedMessage, Message, Member, Channel).join(Message, EditedMessage.message_id == Message.id).join(Member, Message.member_id == Member.id).join(Channel, Message.channel_id == Channel.id)
        results = session.exec(statement).all()
        
        messages = []
        for edited_msg, message, member, channel in results:
            msg_data = {
                'id': edited_msg.id,
                'message_id': edited_msg.message_id,
                'content_before': edited_msg.content_before,
                'content_after': edited_msg.content_after,
                'author_name': f"{member.name} ({member.global_name})",
                'author_id': member.id,
                'avatar_url': member.avatar_url,
                'channel_id': channel.id,
                'channel_name': channel.name,
                'timestamp': edited_msg.edited_at.isoformat(),
                'original_sent_at': message.created_at.isoformat() if message.created_at else None
            }
            messages.append(msg_data)
        
        return messages


# Helper function to get voice activity from database
def get_voice_activity():
    """
    Get voice activity from the database.
    
    Returns:
        list: List of voice activity records
    """
    with Session(engine) as session:
        # Get voice activities with member info
        voice_statement = select(VoiceActivity, Member).join(Member, VoiceActivity.member_id == Member.id)
        voice_results = session.exec(voice_statement).all()
        
        activities = []
        for voice_act, member in voice_results:
            # Get channel names if channel IDs exist
            from_channel_name = None
            to_channel_name = None
            
            if voice_act.from_channel_id:
                from_channel = session.exec(select(Channel).where(Channel.id == voice_act.from_channel_id)).first()
                from_channel_name = from_channel.name if from_channel else None
                
            if voice_act.to_channel_id:
                to_channel = session.exec(select(Channel).where(Channel.id == voice_act.to_channel_id)).first()
                to_channel_name = to_channel.name if to_channel else None
            
            # Parse details JSON if it exists
            details = {}
            if voice_act.details:
                try:
                    details = json.loads(voice_act.details)
                except json.JSONDecodeError:
                    details = {}
            
            act_data = {
                'id': voice_act.id,
                'action': voice_act.action,
                'member_name': f"{member.name} ({member.global_name})",
                'member_id': member.id,
                'avatar_url': member.avatar_url,
                'from_channel_id': voice_act.from_channel_id,
                'from_channel_name': from_channel_name,
                'to_channel_id': voice_act.to_channel_id,
                'to_channel_name': to_channel_name,
                'timestamp': voice_act.timestamp.isoformat(),
                'details': details
            }
            activities.append(act_data)
        
        return activities


# Helper function to get member activity from database
def get_member_activity():
    """
    Get member activity from the database.
    
    Returns:
        list: List of member activity records
    """
    with Session(engine) as session:
        # Get guild activities (join/leave/ban/unban)
        guild_statement = select(GuildActivity, Member).join(Member, GuildActivity.member_id == Member.id)
        guild_results = session.exec(guild_statement).all()
        
        # Get member activities (role changes)
        member_statement = select(MemberActivity, Member, Role).join(Member, MemberActivity.member_id == Member.id).join(Role, MemberActivity.role_id == Role.id, isouter=True)
        member_results = session.exec(member_statement).all()
        
        activities = []
        
        # Process guild activities
        for guild_act, member in guild_results:
            act_data = {
                'id': guild_act.id,
                'action': guild_act.action,
                'member_name': f"{member.name} ({member.global_name})",
                'member_id': member.id,
                'avatar_url': member.avatar_url,
                'timestamp': guild_act.timestamp.isoformat(),
                'type': 'guild'
            }
            activities.append(act_data)
        
        # Process member activities
        for member_act, member, role in member_results:
            act_data = {
                'id': member_act.id,
                'action': member_act.action,
                'member_name': f"{member.name} ({member.global_name})",
                'member_id': member.id,
                'avatar_url': member.avatar_url,
                'role_name': role.name if role else None,
                'role_id': member_act.role_id,
                'timestamp': member_act.timestamp.isoformat(),
                'type': 'member'
            }
            activities.append(act_data)
        
        return activities



# Helper function to format timestamps
def format_timestamp(timestamp_str):
    """
    Format ISO timestamp to a more readable format.
    
    Args:
        timestamp_str (str): ISO timestamp string
        
    Returns:
        str: Formatted timestamp string
    """
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except (ValueError, AttributeError):
        return timestamp_str

# Helper function to calculate summary statistics
# Helper function to calculate summary statistics
def get_summary_stats():
    """
    Calculate summary statistics from database tables.
    
    Returns:
        dict: Dictionary containing summary statistics
    """
    with Session(engine) as session:
        # Count records in each table
        deleted_count = len(session.exec(select(DeletedMessage)).all())
        edited_count = len(session.exec(select(EditedMessage)).all())
        voice_count = len(session.exec(select(VoiceActivity)).all())
        member_count = len(session.exec(select(GuildActivity)).all()) + len(session.exec(select(MemberActivity)).all())
        
        # Find the most recent event across all tables
        latest_deleted = session.exec(select(DeletedMessage.deleted_at).order_by(DeletedMessage.deleted_at.desc())).first()
        latest_edited = session.exec(select(EditedMessage.edited_at).order_by(EditedMessage.edited_at.desc())).first()
        latest_voice = session.exec(select(VoiceActivity.timestamp).order_by(VoiceActivity.timestamp.desc())).first()
        latest_guild = session.exec(select(GuildActivity.timestamp).order_by(GuildActivity.timestamp.desc())).first()
        latest_member = session.exec(select(MemberActivity.timestamp).order_by(MemberActivity.timestamp.desc())).first()
        
        # Determine the most recent timestamp
        all_timestamps = [
            latest_deleted,
            latest_edited,
            latest_voice,
            latest_guild,
            latest_member
        ]
        
        # Filter out None values and find the maximum
        valid_timestamps = [ts for ts in all_timestamps if ts is not None]
        most_recent = format_timestamp(valid_timestamps[0].isoformat()) if valid_timestamps else "No events recorded"
        
        return {
            'total_entries': deleted_count + edited_count + voice_count + member_count,
            'last_logged_event': most_recent
        }

# Route for the homepage
@app.route('/')
def index():
    """
    Render the homepage with summary statistics.
    """
    stats = get_summary_stats()
    return render_template('index.html', stats=stats)

# Route for deleted messages log
@app.route('/deleted-messages')
def deleted_messages():
    """
    Render the deleted messages log page.
    """
    messages = get_deleted_messages()
    # Format timestamps for display
    for msg in messages:
        msg['formatted_timestamp'] = format_timestamp(msg['timestamp'])
        msg['formatted_original_sent_at'] = format_timestamp(msg['original_sent_at'])
    return render_template('deleted_messages.html', messages=messages)

# Route for edited messages log
@app.route('/edited-messages')
def edited_messages():
    """
    Render the edited messages log page.
    """
    messages = get_edited_messages()
    # Format timestamps for display
    for msg in messages:
        msg['formatted_timestamp'] = format_timestamp(msg['timestamp'])
        msg['formatted_original_sent_at'] = format_timestamp(msg['original_sent_at'])
    return render_template('edited_messages.html', messages=messages)

# Route for voice channel activity log
@app.route('/voice-activity')
def voice_activity():
    """
    Render the voice channel activity log page.
    """
    activities = get_voice_activity()
    # Format timestamps for display
    for activity in activities:
        activity['formatted_timestamp'] = format_timestamp(activity['timestamp'])
    return render_template('voice_activity.html', activities=activities)

# Route for member activity log
@app.route('/member-activity')
def member_activity():
    """
    Render the member activity log page.
    """
    activities = get_member_activity()
    # Format timestamps for display
    for activity in activities:
        activity['formatted_timestamp'] = format_timestamp(activity['timestamp'])
    return render_template('member_activity.html', activities=activities)

# SQLModel classes for database access
class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    member_id: Optional[int] = Field(foreign_key="member.id")
    channel_id: Optional[int] = Field(foreign_key="channel.id")
    content: Optional[str] = Field(max_length=2000)
    created_at: Optional[datetime]
    is_edited: Optional[bool] = Field(default=False)

class Member(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(max_length=256)
    global_name: Optional[str] = Field(max_length=256)
    avatar_url: Optional[str] = Field(max_length=256)
    created_at: Optional[datetime]
    roles_json: Optional[str] = Field()

class Channel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(max_length=256)
    ch_type: Optional[str] = Field(max_length=256)

class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(max_length=256)
    color: Optional[str] = Field(max_length=256)
    permissions: Optional[int] = Field()
    created_at: Optional[datetime]

class DeletedMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    message_id: Optional[int] = Field(default=None)
    deleted_at: Optional[datetime]

class EditedMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    message_id: Optional[int] = Field(default=None)
    content_before: Optional[str] = Field(max_length=2000)
    content_after: Optional[str] = Field(max_length=2000)
    edited_at: Optional[datetime]


class VoiceActivity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    member_id: Optional[int] = Field()
    action: Optional[str] = Field(max_length=256)
    from_channel_id: Optional[int] = Field()
    to_channel_id: Optional[int] = Field()
    timestamp: Optional[datetime]
    details: Optional[str] = Field()  # JSON field for additional details

class GuildActivity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    action: Optional[str] = Field(max_length=256)
    member_id: Optional[int] = Field()
    timestamp: Optional[datetime]

class MemberActivity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    action: Optional[str] = Field(max_length=256)
    member_id: Optional[int] = Field()
    role_id: Optional[int] = Field()
    timestamp: Optional[datetime]



if __name__ == '__main__':
    load_dotenv()
    app.run(debug=True, port=os.getenv("DASHBOARD_PORT"))
