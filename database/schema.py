from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

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