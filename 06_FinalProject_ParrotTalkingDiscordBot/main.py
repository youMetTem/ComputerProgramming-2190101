import discord, os, asyncio, math, logging
from discord.ext import commands
from mutagen.mp3 import MP3
from gtts import gTTS
from dotenv import load_dotenv


load_dotenv() #Getting TOKEN from .env file, which will be hidden
token = os.getenv("DISCORD_TOKEN")

#Basic setting for bot
handler = logging.FileHandler(filename = "discord.log", encoding = "utf-8", mode = "w")
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix = "!", intents = intents)
bot.remove_command('help') #Removing default !help, so we could later create our own

sayQueue = [] #Storing !say queue

#Defining a sleep function to prevent interfering voices
def make_sleep():
    async def sleep(delay, result = None, *, loop = None):
        coro = asyncio.sleep(delay, result = result)
        task = asyncio.ensure_future(coro)
        sleep.tasks.add(task)
        try: return await task
        except asyncio.CancelledError: return result
        finally: sleep.tasks.remove(task)
    sleep.tasks = set()
    sleep.cancel_all = lambda: sum(task.cancel() for task in sleep.tasks)
    return sleep
sleep = make_sleep()

#Recussive function to play audio, iterating through the sayQueue list
async def playAudio(guild: discord.Guild):
    if sayQueue == []: return
    else: pass
    
    voice_client = guild.voice_client
    if not voice_client:
        sayQueue.clear()
        return
    else: pass
    
    try:
        message, lang = sayQueue[0]

        output = gTTS(text = message, tld = 'com', lang = lang, slow = False)
        output.save("output.mp3")

        audioSource = discord.FFmpegPCMAudio("output.mp3")
        voice_client.play(audioSource, after = None)

        audioFile = MP3("output.mp3")
        duration = math.ceil(audioFile.info.length)
        await sleep(duration)

        if sayQueue != []: sayQueue.pop(0)
        else: pass

        await playAudio(guild)
    except Exception as e:
        print(f"An error occurred: {e}")
        if sayQueue != []: sayQueue.pop(0)
        await playAudio(guild)

#Active when starting the bot
@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")
    
    activity = discord.Activity(type = discord.ActivityType.listening, name = "!help")
    await bot.change_presence(activity = activity)

#Create our own !help command
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title = "Help - Parrot, Text to Speech Bot",
        description = "A simple text to speech bot that joins your voice channel and reads out messages you send it.",
        color = discord.Color.blue()
    )
    embed.add_field(name = "!join", value = "Makes the bot join your current voice channel.", inline = False)
    embed.add_field(name = "!leave", value = "Makes the bot leave the voice channel it is currently in.", inline = False)
    embed.add_field(name = "!say <language> <message>", value = "Adds a message to the queue to be read out loud in the specified language. Example languages: en, es, fr, de, it, ja, ko, zh-CN.", inline = False)
    embed.add_field(name = "!queue", value = "Displays the current queue of messages to be read out loud.", inline = False)
    embed.add_field(name = "!clear", value = "Clears the current queue of messages.", inline = False)
    embed.add_field(name = "!skip", value = "Skips the current message being read out loud.", inline = False)

    embed.set_footer(text = "Developed by Temtem")

    await ctx.send(embed = embed)

#For Joining voice call
@bot.command()
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return
    channel = ctx.message.author.voice.channel
    await channel.connect()
    await ctx.send(f"joined {channel}")

#For leaving voice call
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        sayQueue.clear()
        sleep.cancel_all()

        await ctx.voice_client.disconnect()
        await ctx.send("left the voice channel")
    else:
        await ctx.send("not in a voice channel")

#Command for !say
@bot.command()
async def say(ctx, language: str, *, msg: str):
    if ctx.voice_client is None:
        await ctx.send("You are not connected to a voice channel")
        return
    else: pass

    sayQueue.append((msg, language))
    await ctx.send(f"Added to queue: `{msg}`")

    if not ctx.voice_client.is_playing():
        await playAudio(ctx)

#Checking for queue in sayQueue
@bot.command()
async def queue(ctx):
    output = ""

    if sayQueue == []:
        await ctx.send("The queue is empty")
        return
    else: pass

    for i, (msg, lang) in enumerate(sayQueue[:5], 1):
        output += f"`({i}) {msg}`\n"
    
    if len(sayQueue) > 5:
        output += f"\n ... and {len(sayQueue) - 5} more"

    await ctx.send(output)

#Clearing sayQueue List
@bot.command()
async def clear(ctx):
    if not sayQueue:
        await ctx.send("The queue is already empty.")
        return
    
    sayQueue.clear()
    sleep.cancel_all()
    
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        
    await ctx.send("Queue has been cleared.")

#Skipping current track
@bot.command()
async def skip(ctx):
    if not ctx.voice_client.is_playing():
        await ctx.send("Not currently playing anything.")
        return
    
    if not sayQueue:
        await ctx.send("Queue is empty, nothing to skip.")
        return

    ctx.voice_client.stop()
    sleep.cancel_all()
    
    await ctx.send("Skipped to the next message.")

#running the bot with token
discord.utils.setup_logging(handler = handler, level = logging.DEBUG)
bot.run(token)