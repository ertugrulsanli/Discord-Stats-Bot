import discord
from discord.ext import commands, tasks
import datetime

TOKEN = "BOT TOKEN GİRİNİZ"
guild_id = KANAL ID GİRİN

intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def create_or_update_channel(guild, channel_prefix, category_name=None, check_full_name=False):
    category = None
    for c in guild.categories:
        if c.name == category_name:
            category = c
            break
    else:
        category = await guild.create_category(category_name)

    existing_channel = None
    for channel in category.channels:
        if (check_full_name and channel.name == channel_prefix) or (not check_full_name and channel.name.startswith(channel_prefix.split(' ')[0])):
            existing_channel = channel
            break

    if existing_channel:
        await existing_channel.edit(name=channel_prefix)
        return existing_channel
    else:
        channel = await guild.create_voice_channel(name=channel_prefix, category=category)
        return channel

@bot.event
async def on_ready():
    global guild_id
    print("Bot is ready.")

    if not guild_id:
        guild_id = bot.guilds[0].id

    guild = bot.get_guild(guild_id)

    update_channels.start(guild)

@tasks.loop(minutes=5)  # 1 dakika yerine 5 dakikada bir güncelleme
async def update_channels(guild):
    print("Updating channels...")

    stats_category = None
    for c in guild.categories:
        if c.name == "📊 Server Stats 📊":
            stats_category = c
            break
    else:
        stats_category = await guild.create_category("📊 Server Stats 📊")

        # Tarih kanalı
        tr_time = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
        date_format = tr_time.strftime("%d.%m.%Y")
        date_channel_name = f"📅 {date_format}"
        date_channel = await create_or_update_channel(guild, date_channel_name, category_name=stats_category.name)
        await date_channel.edit(name=date_channel_name)

    # Saat kanalı
    tr_time = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
    time_format = tr_time.strftime("%H:%M")
    time_channel_name = f"⏰ {time_format}"
    time_channel = await create_or_update_channel(guild, time_channel_name, category_name=stats_category.name)
    await time_channel.edit(name=time_channel_name)

    # Eğer dakika değişmediyse, diğer kanalları güncelleme
    if update_channels.prev_minute == tr_time.minute:
        return

    update_channels.prev_minute = tr_time.minute

    # Durumlar kanalı
    online_members = 0
    idle_members = 0
    dnd_members = 0
    offline_members = 0

    for member in guild.members:
        if member.status == discord.Status.online:
            online_members += 1
        elif member.status == discord.Status.idle:
            idle_members += 1
        elif member.status == discord.Status.dnd:
            dnd_members += 1
        else:
            offline_members += 1

    channel_name = f"🟢 {online_members} 🌙 {idle_members} ⛔ {dnd_members}"
    if offline_members > 0:
        channel_name += f" ⚪ {offline_members}"
    status_channel = await create_or_update_channel(guild, channel_name, category_name=stats_category.name, check_full_name=True)
    await status_channel.edit(name=channel_name)

    # Toplam üye kanalı
    total_members = sum(1 for _ in guild.members)
    member_count_channel_name = f"Toplam Üye: {total_members}"
    member_count_channel = await create_or_update_channel(guild, member_count_channel_name, category_name=stats_category.name)

    # Gereksiz kanalları silme
    for c in stats_category.channels:
        if c.id not in [member_count_channel.id, status_channel.id, time_channel.id]:
            await c.delete()

# İlk çalıştırmada prev_minute'i ayarlama
update_channels.prev_minute = -1

bot.run(TOKEN)
