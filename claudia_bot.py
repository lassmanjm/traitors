from absl import app
from absl import flags
import discord
from discord import app_commands
from discord.ui import Select, View, Button
import asyncio
import math
from num2words import num2words
import os
import random

import setup_commands
import game_controls

FLAGS = flags.FLAGS
flags.DEFINE_string(
    "bot_token",
    "",
    # TODO add description
    "description"
)
flags.DEFINE_string(
    "server_id",
    "",
    # TODO add description
    "description"
)

intents = discord.Intents.default()
intents.members = True
intents.guilds = True 
intents.guild_messages = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def main(argv):
    guild_id=FLAGS.server_id if FLAGS.server_id else os.environ.get('TRAITORS_SERVER_ID')
    if not guild_id:
        raise ValueError("Server ID not provided. Set 'server_id' flag or 'TRAITORS_SERVER_ID' environment variable.")
    guild_id=int(guild_id)

    bot_token=FLAGS.bot_token if FLAGS.bot_token else os.environ.get('TRAITORS_BOT_TOKEN')
    if not bot_token:
        raise ValueError("Bot token not provided. Set 'bot_token' flag or 'TRAITORS_BOT_TOKEN' environment variable.")

    @client.event
    async def on_ready():
        setup_commands.SetupCommands(tree, guild_id, client)
        game_controls.GameControls(tree, guild_id, client)
        await tree.sync(guild=discord.Object(id=guild_id))
        print(f'Logged in as {client.user}: commands')

    client.run(bot_token)

if __name__ == "__main__":
    app.run(main)

