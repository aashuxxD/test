from pyrogram import filters
from pyrogram.types import Message
from strings import get_command
from StrangerMusic import app
from StrangerMusic.misc import SUDOERS
from StrangerMusic.utils.database import autoend_off, autoend_on

# Commands
AUTOEND_COMMAND = get_command("AUTOEND_COMMAND")


@app.on_message(filters.command(AUTOEND_COMMAND) & SUDOERS)
async def auto_end_stream(client, message:Message):
    usage = "**Usage:**\n\n/autoend [enable|disable]"
    if len(message.command) != 2:
        return await message.reply_text(usage)
    state = message.text.split(None, 1)[1].strip()
    state = state.lower()
    if state == "enable":
        await autoend_on()
        await message.reply_text(
            "Auto End Stream Enabled.\n\nBot will leave voice chat automatically after 3 mins if no one is listening with a warning message.."
        )
    elif state == "disable":
        await autoend_off()
        await message.reply_text("Auto End Stream Disabled.")
    else:
        await message.reply_text(usage)


@app.on_message(filters.command("groupinfo") & SUDOERS)
async def groupinfo(client, message: Message):
    if len(message.command) != 2:
        return await message.reply_text("**Usage:** /groupinfo [GROUP_ID/USERNAME]")
    
    group_identifier = message.command[1]
    
    try:
        try:
            group = await client.get_chat(group_identifier)
        except Exception as e:
            if "PEER_ID_INVALID" in str(e):
                return await message.reply_text("I can't access this group. Make sure:\n1. The group ID/username is correct\n2. I have been added to the group")
            return await message.reply_text(f"An error occurred: {str(e)}")

        if "SUPERGROUP" not in str(group.type) and "GROUP" not in str(group.type):
            return await message.reply_text("This is not a group!")

        try:
            bot_info = await client.get_chat_member(group.id, "me")
            if not bot_info.status:
                return await message.reply_text("I'm not a member of this group!")
        except Exception:
            return await message.reply_text("I'm not a member of this group!")

        # Get group information
        members_count = await client.get_chat_members_count(group.id)
        description = group.description or "No description available"
        username = f"@{group.username}" if group.username else "Private Group"
        
        # Create info message
        info_text = f"**Group Information:**\n\n"
        info_text += f"**Title:** {group.title}\n"
        info_text += f"**ID:** `{group.id}`\n"
        info_text += f"**Username:** {username}\n"
        info_text += f"**Members:** {members_count}\n"
        info_text += f"**Description:** {description}\n"
        
        # Add optional fields if available
        if group.invite_link:
            info_text += f"**Invite Link:** {group.invite_link}\n"
            
        await message.reply_text(info_text)
        
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")