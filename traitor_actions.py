import discord
from discord.ext import commands
import re
import asyncio
from constants import bot_token, traitors_channel_id, murders_channel_id

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix="!")

canned_responses={
    "$test": "I am still here!",
    "test test": "Is this thing on?",
    "hello claudia!": "Hello everybody. Welcome to Traitors Castle"
    }

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}: responses')

# Event to listen to messages
@bot.event
async def on_message(message):
    # Ensure the bot doesn't respond to itself
    if message.author == bot.user:
        return
    murders_channel = bot.get_channel(murders_channel_id)
    traitors_channel = bot.get_channel(traitors_channel_id)

    # Check if the message is in the source channel
    match = re.fullmatch(r"(murder|mrder|muder|mder|mdr|muer|mrdr): (.*)", message.content, flags=re.IGNORECASE)
    if match:
        if message.channel.id != traitors_channel_id:
            await message.delete()
            await message.author.send(
                f"You posted a murder in the wrong channel: **{message.channel.name}**. Please post them in the **Traitors murder-selection** channel"
                )
            
        elif message.content.lower().startswith("murder:"):
            victim = match.group(2)
            is_are="are" if ( "," in victim or " and " in victim ) else "is"
            await message.channel.send(f"Please confirm: Murder **{victim}**? Type 'yes' to confirm or 'no' to cancel.")

            try:
                # Wait for the user to respond with 'yes' or 'no'
                reply = await bot.wait_for('message', timeout=60.0, check=lambda m: m.content.lower() in ['yes', 'no'] and m.channel == message.channel)

                if reply.content.lower() == 'yes':

                    await message.channel.send(f"Confirmation recievied. Murdering **{victim}**")
                    await murders_channel.send(f"The traitors have struck again. **{victim}** {is_are} dead")
                else:
                    await message.channel.send("Murder selection cancelled.")

            except asyncio.TimeoutError:
                await message.channel.send("Action timed out, no confirmation received. Please try again.")

    if "fuck you" in message.content:
        await message.channel.send("Your mother")

    if message.content.strip().lower() in canned_responses:
        await message.channel.send(canned_responses[message.content.strip().lower()])

# Run the bot with your token
bot.run(bot_token)
