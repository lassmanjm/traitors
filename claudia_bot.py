from absl import app
from absl import flags
import discord
from discord import app_commands
import os

import setup_commands
import game_controls
from game import Game, Player

FLAGS = flags.FLAGS
flags.DEFINE_string(
    "bot_token",
    "",
    # TODO add description
    "description",
)
flags.DEFINE_string(
    "server_id",
    "",
    # TODO add description
    "description",
)
flags.DEFINE_integer(
    "button_refresh_history_limit",
    None,
    (
        "Limit of how far to go back in DM's and control "
        "channel history to reestablish button functionality"
    ),
)


def main(argv):
    guild_id = (
        FLAGS.server_id if FLAGS.server_id else os.environ.get("TRAITORS_SERVER_ID")
    )
    if not guild_id:
        raise ValueError(
            "Server ID not provided. Set 'server_id' flag or 'TRAITORS_SERVER_ID' environment variable."
        )
    guild_id = int(guild_id)

    bot_token = (
        FLAGS.bot_token if FLAGS.bot_token else os.environ.get("TRAITORS_BOT_TOKEN")
    )
    if not bot_token:
        raise ValueError(
            "Bot token not provided. Set 'bot_token' flag or 'TRAITORS_BOT_TOKEN' environment variable."
        )

    intents = discord.Intents.default()
    intents.members = True
    intents.guilds = True
    intents.guild_messages = True
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)

    @client.event
    async def on_ready():
        game = Game(client=client, guild_id=guild_id)

        button_refresh_history_limit_string = os.environ.get(
            "TRAITORS_BUTTON_REFRESH_HITORY_LIMIT"
        )
        button_refresh_history_limit = 100
        if button_refresh_history_limit_string:
            try:
                button_refresh_history_limit = int(button_refresh_history_limit_string)
            except Exception as e:
                await game._send_error(
                    (
                        f"Unable to parse environment variable 'TRAITORS_BUTTON_REFRESH_HITORY_LIMIT' "
                        f"as int. Value: '{button_refresh_history_limit_string}'"
                    )
                )
        if FLAGS.button_refresh_history_limit is not None:
            button_refresh_history_limit = FLAGS.button_refresh_history_limit
        await game.refresh_load_game_views(limit=button_refresh_history_limit)
        setup_commands.setup_commands(tree, client, game)
        game_controls.GameControls(tree, guild_id, client, game)
        await tree.sync(guild=discord.Object(id=guild_id))
        print(f"Logged in as {client.user}: commands")
        await (await game.controls_channel).send(
            embed=discord.Embed(
                title="Here I am!",
                description="Claudia bot has been loaded.",
                color=discord.Color.green(),
            )
        )

    client.run(bot_token)


if __name__ == "__main__":
    app.run(main)
