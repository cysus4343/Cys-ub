"""
Enhanced Feature-Packed Discord Selfbot in Python using discord.py
Author: BLACKBOXAI
Note: Using selfbots violates Discord's TOS. Use responsibly and only for personal automation on your own account.
Make sure you install discord.py version 1.7+ (compatible with selfbots)
via: pip install discord.py==1.7.3

Usage: python discord_selfbot.py
You will be prompted to input your user token securely.

Features Included:
1-15: Previous features (auto status, typing, message commands, reactions, info commands, mass DM, pin/unpin, clear, etc.)
16. Server invite info command
17. Emoji info command
18. Role info command
19. Leave server command
20. Join server via invite command
21. View pinned messages command
22. Create and delete text channels
23. Create and delete roles
24. Search messages by keyword
25. Toggle Do Not Disturb status
26. Toggle Invisible status
27. List mutual servers with a user
28. Show latency/ping
29. Show bot uptime
30. Fetch avatar URL
31. Fetch user creation date (account age)
32. Quote a message by ID
33. Repeat last deleted message (snipe last own deleted)
34. Send embed message command
35. Send file from URL command

Commands prefix: .

"""

import discord
from discord.ext import commands, tasks
import asyncio
import sys
import getpass
import time
import datetime
import aiohttp
import io

intents = discord.Intents.all()
client = commands.Bot(command_prefix='.', self_bot=True, intents=intents)

# Globals
last_message = None
status_cycle_task = None
status_messages = [
    "Coding cool stuff!",
    "In a meeting with AI",
    "Helping users with code",
    "Listening to music",
    "Watching YouTube tutorials",
]
last_deleted_message_content = None
start_time = time.time()

# =========== Events ===========

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("Selfbot is ready!")
    auto_status_change.start()

@client.event
async def on_message(message):
    global last_message
    if message.author.id != client.user.id:
        return

    last_message = message  # track last message sent by user (self)
    await client.process_commands(message)

@client.event
async def on_message_delete(message):
    global last_deleted_message_content
    if message.author.id == client.user.id:
        last_deleted_message_content = message.content

# =========== Tasks ===========

@tasks.loop(minutes=5)
async def auto_status_change():
    for status in status_messages:
        await client.change_presence(activity=discord.Game(name=status))
        await asyncio.sleep(300)

# =========== Commands ===========

@client.command()
async def say(ctx, *, msg: str):
    """Send a message: .say Your message here"""
    await ctx.message.delete()
    await ctx.send(msg)

@client.command()
async def del_(ctx):
    """Delete last message sent by self: .del"""
    await ctx.message.delete()
    global last_message
    if last_message:
        try:
            await last_message.delete()
            await ctx.send("Deleted last message.", delete_after=3)
            last_message = None
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete messages.", delete_after=5)
        except Exception as e:
            await ctx.send(f"Error: {e}", delete_after=5)
    else:
        await ctx.send("No last message tracked.", delete_after=5)

@client.command()
async def edit(ctx, *, new_content: str):
    """Edit last sent message: .edit New message content"""
    await ctx.message.delete()
    global last_message
    if last_message:
        try:
            await last_message.edit(content=new_content)
            await ctx.send("Edited last message.", delete_after=3)
        except discord.Forbidden:
            await ctx.send("I don't have permission to edit that message.", delete_after=5)
        except Exception as e:
            await ctx.send(f"Error: {e}", delete_after=5)
    else:
        await ctx.send("No last message tracked.", delete_after=5)

@client.command()
async def react(ctx, emoji):
    """React to last sent message: .react 😀"""
    await ctx.message.delete()
    global last_message
    if last_message:
        try:
            await last_message.add_reaction(emoji)
            await ctx.send(f"Reacted with {emoji}.", delete_after=3)
        except discord.HTTPException:
            await ctx.send("Failed to add reaction. Validate emoji.", delete_after=5)
    else:
        await ctx.send("No last message tracked.", delete_after=5)

@client.command()
async def userinfo(ctx, user: discord.User = None):
    """Get user info: .userinfo [@user]"""
    await ctx.message.delete()
    user = user or ctx.author
    embed = discord.Embed(title=f"User Info - {user}", color=discord.Color.blurple())
    embed.set_thumbnail(url=user.avatar_url)
    embed.add_field(name="ID", value=user.id)
    embed.add_field(name="Display Name", value=user.display_name)
    embed.add_field(name="Bot?", value=user.bot)
    embed.add_field(name="Created At", value=user.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    embed.add_field(name="Avatar URL", value=user.avatar_url)
    embed.set_footer(text="Requested by " + str(ctx.author))
    await ctx.send(embed=embed)

@client.command()
async def serverinfo(ctx, guild: discord.Guild = None):
    """Get server info: .serverinfo"""
    await ctx.message.delete()
    guild = guild or ctx.guild
    if not guild:
        await ctx.send("This command must be used in a guild/server.", delete_after=5)
        return
    embed = discord.Embed(title=f"Server Info - {guild.name}", color=discord.Color.green())
    embed.set_thumbnail(url=guild.icon_url)
    embed.add_field(name="ID", value=guild.id)
    embed.add_field(name="Owner", value=str(guild.owner))
    embed.add_field(name="Region", value=str(guild.region))
    embed.add_field(name="Members", value=guild.member_count)
    embed.add_field(name="Channels", value=len(guild.channels))
    embed.set_footer(text="Requested by " + str(ctx.author))
    await ctx.send(embed=embed)

@client.command()
async def nick(ctx, *, nickname: str):
    """Change your nickname: .nick NewName"""
    await ctx.message.delete()
    if ctx.guild is None:
        await ctx.send("You can only change nicknames in servers.", delete_after=5)
        return
    try:
        me = ctx.guild.get_member(client.user.id)
        await me.edit(nick=nickname)
        await ctx.send(f"Nickname changed to: {nickname}", delete_after=5)
    except discord.Forbidden:
        await ctx.send("I don't have permission to change your nickname.", delete_after=5)
    except Exception as e:
        await ctx.send(f"Error: {e}", delete_after=5)

@client.command()
async def channelinfo(ctx, channel: discord.TextChannel = None):
    """Get info about a channel: .channelinfo [#channel]"""
    await ctx.message.delete()
    channel = channel or ctx.channel
    embed = discord.Embed(title=f"Channel Info - {channel.name}", color=discord.Color.orange())
    embed.add_field(name="ID", value=channel.id)
    embed.add_field(name="Category", value=channel.category)
    embed.add_field(name="Topic", value=channel.topic or "None")
    embed.add_field(name="NSFW?", value=channel.is_nsfw())
    embed.add_field(name="Slowmode delay", value=f"{channel.slowmode_delay} seconds")
    embed.add_field(name="Position", value=channel.position)
    await ctx.send(embed=embed)

@client.command()
async def dmall(ctx, *, message):
    """DM all your friends (use responsibly): .dmall Your message"""
    await ctx.message.delete()
    count = 0
    for friend in client.user.friends:
        try:
            await friend.send(message)
            count += 1
            await asyncio.sleep(1)
        except Exception:
            continue
    await ctx.send(f"Sent message to {count} friends.", delete_after=10)

@client.command()
async def statuscycle(ctx, action: str):
    """Start or stop cycling your status: .statuscycle start|stop"""
    global status_cycle_task
    await ctx.message.delete()
    action = action.lower()
    if action == "start":
        if status_cycle_task and status_cycle_task.is_running():
            await ctx.send("Status cycling already running!", delete_after=5)
            return
        status_cycle_task = client.loop.create_task(cycle_status())
        await ctx.send("Started cycling status messages.", delete_after=5)
    elif action == "stop":
        if status_cycle_task:
            status_cycle_task.cancel()
            status_cycle_task = None
            await ctx.send("Stopped cycling status messages.", delete_after=5)
            await client.change_presence(status=discord.Status.online)
        else:
            await ctx.send("Status cycling not running.", delete_after=5)
    else:
        await ctx.send("Invalid action. Use 'start' or 'stop'.", delete_after=5)

async def cycle_status():
    try:
        while True:
            for status in status_messages:
                await client.change_presence(activity=discord.Game(name=status))
                await asyncio.sleep(300)
    except asyncio.CancelledError:
        pass

@client.command()
async def msgcount(ctx):
    """Count messages you sent in channel: .msgcount"""
    await ctx.message.delete()
    count = 0
    async for message in ctx.channel.history(limit=1000):
        if message.author == client.user:
            count += 1
    await ctx.send(f"You sent {count} messages here recently.", delete_after=10)

@client.command()
async def pin(ctx):
    """Pin last message sent by you: .pin"""
    await ctx.message.delete()
    global last_message
    if last_message:
        try:
            await last_message.pin()
            await ctx.send("Pinned last message.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("No permission to pin messages.", delete_after=5)
        except Exception as e:
            await ctx.send(f"Error: {e}", delete_after=5)
    else:
        await ctx.send("No last message tracked.", delete_after=5)

@client.command()
async def unpin(ctx):
    """Unpin last message sent by you: .unpin"""
    await ctx.message.delete()
    global last_message
    if last_message:
        try:
            await last_message.unpin()
            await ctx.send("Unpinned last message.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("No permission to unpin messages.", delete_after=5)
        except Exception as e:
            await ctx.send(f"Error: {e}", delete_after=5)
    else:
        await ctx.send("No last message tracked.", delete_after=5)

@client.command()
async def clear(ctx, limit: int = 50):
    """Clear your own messages (default 50): .clear [limit]"""
    await ctx.message.delete()
    def is_me(m):
        return m.author.id == client.user.id
    deleted = await ctx.channel.purge(limit=limit, check=is_me)
    await ctx.send(f"Deleted {len(deleted)} of your messages.", delete_after=7)

@client.command()
async def typing(ctx, duration: int = 5):
    """Show typing indicator: .typing [seconds]"""
    await ctx.message.delete()
    async with ctx.channel.typing():
        await asyncio.sleep(duration)
    await ctx.send(f"Stopped typing after {duration}s.", delete_after=3)

# 16. Server invite info
@client.command()
async def inviteinfo(ctx, invite_code: str):
    """Get info about invite: .inviteinfo CODE"""
    await ctx.message.delete()
    try:
        invite = await client.fetch_invite(invite_code)
        embed = discord.Embed(title=f"Invite info for {invite_code}")
        embed.add_field(name="Guild", value=invite.guild.name if invite.guild else "None")
        embed.add_field(name="Channel", value=invite.channel.name if invite.channel else "None")
        embed.add_field(name="Inviter", value=str(invite.inviter) if invite.inviter else "Unknown")
        embed.add_field(name="Max Age", value=f"{invite.max_age} seconds")
        embed.add_field(name="Max Uses", value=invite.max_uses or "Unlimited")
        embed.add_field(name="Temporary Membership", value=str(invite.temporary))
        embed.add_field(name="Uses", value=invite.uses)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Failed to fetch invite: {e}", delete_after=7)

# 17. Emoji info
@client.command()
async def emojiinfo(ctx, emoji: discord.Emoji = None):
    """Get info about an emoji: .emojiinfo <emoji>"""
    await ctx.message.delete()
    emoji = emoji or ctx.message.content.split(' ')[1] if len(ctx.message.content.split(' '))>1 else None
    if not emoji:
        await ctx.send("Please provide an emoji.", delete_after=5)
        return
    e = None
    if isinstance(emoji, discord.Emoji):
        e = emoji
    else:
        try:
            e = await client.fetch_emoji(int(str(emoji).strip('<:>')))
        except:
            await ctx.send("Invalid emoji provided.", delete_after=5)
            return
    embed = discord.Embed(title=f"Emoji Info - {e.name}")
    embed.add_field(name="ID", value=e.id)
    embed.add_field(name="Animated", value=e.animated)
    embed.add_field(name="Guild", value=e.guild.name)
    embed.set_thumbnail(url=e.url)
    await ctx.send(embed=embed)

# 18. Role info
@client.command()
async def roleinfo(ctx, *, role_name: str = None):
    """Get info about a role in this guild: .roleinfo role_name"""
    await ctx.message.delete()
    if ctx.guild is None:
        await ctx.send("This command only works in a server.", delete_after=5)
        return
    if not role_name:
        await ctx.send("Please provide a role name.", delete_after=5)
        return
    role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), ctx.guild.roles)
    if not role:
        await ctx.send("Role not found.", delete_after=5)
        return
    embed = discord.Embed(title=f"Role Info - {role.name}")
    embed.add_field(name="ID", value=role.id)
    embed.add_field(name="Color", value=str(role.color))
    embed.add_field(name="Hoisted", value=role.hoist)
    embed.add_field(name="Mentionable", value=role.mentionable)
    embed.add_field(name="Position", value=role.position)
    embed.add_field(name="Members", value=len(role.members))
    await ctx.send(embed=embed)

# 19. Leave server
@client.command()
async def leaveserver(ctx, *, guild_name: str = None):
    """Leave a guild by name: .leaveserver Guild Name"""
    await ctx.message.delete()
    if not guild_name:
        await ctx.send("Please specify a guild to leave.", delete_after=5)
        return
    guild = discord.utils.find(lambda g: g.name.lower() == guild_name.lower(), client.guilds)
    if not guild:
        await ctx.send("Guild not found.", delete_after=5)
        return
    try:
        await guild.leave()
        await ctx.send(f"Left the guild {guild.name}.", delete_after=5)
    except Exception as e:
        await ctx.send(f"Failed to leave: {e}", delete_after=5)

# 20. Join server via invite
@client.command()
async def join(ctx, invite_code: str):
    """Join a server via invite code: .join CODE"""
    await ctx.message.delete()
    try:
        invite = await client.fetch_invite(invite_code)
        await client.http.join_guild(invite.guild.id)
        await ctx.send(f"Joined server: {invite.guild.name}", delete_after=5)
    except Exception as e:
        await ctx.send(f"Failed to join server: {e}", delete_after=5)

# 21. View pinned messages
@client.command()
async def pinned(ctx):
    """List pinned messages in the channel: .pinned"""
    await ctx.message.delete()
    pins = await ctx.channel.pins()
    if not pins:
        await ctx.send("No pinned messages found.", delete_after=5)
        return
    msgs = '\n'.join([f"- {m.author.name}: {m.content[:50]}" for m in pins])
    if len(msgs) > 1900:
        msgs = msgs[:1900] + "..."
    await ctx.send(f"**Pinned messages:**\n{msgs}")

# 22. Create text channel
@client.command()
async def createchannel(ctx, *, name: str):
    """Create a text channel in this server: .createchannel channelname"""
    await ctx.message.delete()
    if ctx.guild is None:
        await ctx.send("This command works only in a server.", delete_after=5)
        return
    try:
        await ctx.guild.create_text_channel(name)
        await ctx.send(f"Created channel #{name}.", delete_after=5)
    except discord.Forbidden:
        await ctx.send("No permission to create channels.", delete_after=5)
    except Exception as e:
        await ctx.send(f"Error: {e}", delete_after=5)

# 23. Delete text channel
@client.command()
async def deletechannel(ctx, channel: discord.TextChannel = None):
    """Delete a text channel: .deletechannel #channel"""
    await ctx.message.delete()
    if ctx.guild is None:
        await ctx.send("This command works only in a server.", delete_after=5)
        return
    channel = channel or ctx.channel
    try:
        await channel.delete()
        await ctx.send(f"Deleted channel {channel.name}.", delete_after=5)
    except discord.Forbidden:
        await ctx.send("No permission to delete channels.", delete_after=5)
    except Exception as e:
        await ctx.send(f"Error: {e}", delete_after=5)

# 24. Create role
@client.command()
async def createrole(ctx, *, name: str):
    """Create a role: .createrole RoleName"""
    await ctx.message.delete()
    if ctx.guild is None:
        await ctx.send("Works only in servers.", delete_after=5)
        return
    try:
        await ctx.guild.create_role(name=name)
        await ctx.send(f"Created role {name}.", delete_after=5)
    except discord.Forbidden:
        await ctx.send("No permission to create roles.", delete_after=5)
    except Exception as e:
        await ctx.send(f"Error: {e}", delete_after=5)

# 25. Delete role
@client.command()
async def deleterole(ctx, *, role_name: str):
    """Delete a role by name: .deleterole RoleName"""
    await ctx.message.delete()
    if ctx.guild is None:
        await ctx.send("Works only in servers.", delete_after=5)
        return
    role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), ctx.guild.roles)
    if not role:
        await ctx.send("Role not found.", delete_after=5)
        return
    try:
        await role.delete()
        await ctx.send(f"Deleted role {role_name}.", delete_after=5)
    except discord.Forbidden:
        await ctx.send("No permission to delete roles.", delete_after=5)
    except Exception as e:
        await ctx.send(f"Error: {e}", delete_after=5)

# 26. Search messages by keyword
@client.command()
async def search(ctx, *, keyword: str):
    """Search last 100 messages for a keyword: .search keyword"""
    await ctx.message.delete()
    found = []
    async for msg in ctx.channel.history(limit=100):
        if keyword.lower() in msg.content.lower() and msg.author == client.user:
            found.append(msg)
    if not found:
        await ctx.send("No matching messages found.", delete_after=5)
        return
    response = '\n'.join([f"{m.created_at.strftime('%H:%M')} | {m.content[:50]}" for m in found])
    if len(response) > 1900:
        response = response[:1900] + "..."
    await ctx.send(f"Found messages:\n{response}")

# 27. Toggle Do Not Disturb status
@client.command()
async def dnd(ctx):
    """Set status to Do Not Disturb: .dnd"""
    await ctx.message.delete()
    await client.change_presence(status=discord.Status.dnd)
    await ctx.send("Status set to Do Not Disturb.", delete_after=5)

# 28. Toggle Invisible status
@client.command()
async def invisible(ctx):
    """Set status to Invisible: .invisible"""
    await ctx.message.delete()
    await client.change_presence(status=discord.Status.invisible)
    await ctx.send("Status set to Invisible.", delete_after=5)

# 29. List mutual servers with user
@client.command()
async def mutual(ctx, user: discord.User):
    """List mutual servers with another user: .mutual @user"""
    await ctx.message.delete()
    mutual_guilds = [g.name for g in client.guilds if g.get_member(user.id)]
    if not mutual_guilds:
        await ctx.send("No mutual servers found.", delete_after=5)
        return
    await ctx.send(f"Mutual servers with {user.name}:\n" + '\n'.join(mutual_guilds), delete_after=20)

# 30. Show latency/ping
@client.command()
async def ping(ctx):
    """Show client latency: .ping"""
    await ctx.message.delete()
    latency_ms = round(client.latency * 1000)
    await ctx.send(f"Pong! Latency: {latency_ms}ms", delete_after=5)

# 31. Show bot uptime
@client.command()
async def uptime(ctx):
    """Show how long the selfbot has been running: .uptime"""
    await ctx.message.delete()
    delta = time.time() - start_time
    uptime_str = str(datetime.timedelta(seconds=int(delta)))
    await ctx.send(f"Uptime: {uptime_str}", delete_after=10)

# 32. Fetch avatar URL
@client.command()
async def avatar(ctx, user: discord.User=None):
    """Get avatar URL: .avatar [@user]"""
    await ctx.message.delete()
    user = user or ctx.author
    await ctx.send(f"{user.name}'s avatar URL: {user.avatar_url}", delete_after=20)

# 33. Fetch user account age
@client.command()
async def created(ctx, user: discord.User=None):
    """Get the Discord account creation date: .created [@user]"""
    await ctx.message.delete()
    user = user or ctx.author
    created = user.created_at.strftime("%Y-%m-%d %H:%M:%S")
    await ctx.send(f"{user.name} created their account on {created}", delete_after=15)

# 34. Quote a message by ID
@client.command()
async def quote(ctx, message_id: int):
    """Quote a message by ID in current channel: .quote message_id"""
    await ctx.message.delete()
    try:
        msg = await ctx.channel.fetch_message(message_id)
        embed = discord.Embed(description=msg.content, timestamp=msg.created_at, color=discord.Color.blue())
        embed.set_author(name=msg.author.name, icon_url=msg.author.avatar_url)
        embed.set_footer(text=f"Message ID: {msg.id}")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Could not fetch message: {e}", delete_after=7)

# 35. Repeat last deleted message (snipe own deleted message)
@client.command()
async def snipe(ctx):
    """Repeat last deleted message by you: .snipe"""
    await ctx.message.delete()
    global last_deleted_message_content
    if last_deleted_message_content:
        await ctx.send(f"Sniped deleted message: {last_deleted_message_content}")
        last_deleted_message_content = None
    else:
        await ctx.send("No deleted messages found to snipe.", delete_after=5)

# 36. Send embed message
@client.command()
async def embed(ctx, *, content: str):
    """Send embed message: .embed Your message"""
    await ctx.message.delete()
    embed = discord.Embed(description=content, color=discord.Color.purple())
    await ctx.send(embed=embed)

# 37. Send file from URL
@client.command()
async def sendfile(ctx, url: str):
    """Send image/GIF file from URL: .sendfile URL"""
    await ctx.message.delete()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await ctx.send("Failed to download file.", delete_after=5)
                    return
                data = io.BytesIO(await resp.read())
                filename = url.split('/')[-1]
                await ctx.send(file=discord.File(data, filename=filename))
    except Exception as e:
        await ctx.send(f"Error sending file: {e}", delete_after=5)

# =========== Run Bot ===========

def main():
    print("Enhanced Feature-Packed Discord Selfbot")
    print("Warning: Never share your token with anyone!")
    token = MTM3ODgwODIwODM1NjgwNjcwNw.GTZ5RS .YpVg1xVjBh8WGwCZ6doGWR6wFUJdFVaWX-UFOW

    try:
        client.run(token, bot=False)
    except discord.LoginFailure:
        print("Invalid token.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()

