from absl import app
from absl import flags
import discord
from discord import app_commands
import os

import setup_commands
import game_controls
from interface import DiscordInterface, Player

FLAGS = flags.FLAGS
BOT_TOKEN = flags.DEFINE_string(
    "bot_token",
    None,
    # TODO add description
    "description",
)
SERVER_ID = flags.DEFINE_string(
    "server_id",
    "",
    # TODO add description
    "description",
)
BUTTON_REFRESH_HISTORY_LIMIT = flags.DEFINE_integer(
    "button_refresh_history_limit",
    None,
    (
        "Limit of how far to go back in DM's and control "
        "channel history to reestablish button functionality"
    ),
)
SAVED_GAME_PATH = flags.DEFINE_string(
    "saved_game_path", None, "Path to directory where saved game files will be written."
)


async def get_button_refresh_history_limit(
    discord_interface: DiscordInterface, default: int = 100
) -> int:
    """Get the button history refresh limit. First checks the flag value, if empty defaults
    to the TRAITORS_BUTTON_REFRESH_HITORY_LIMIT environment variable. If that is not set, defaults to the
    default value parameter.
    """
    if BUTTON_REFRESH_HISTORY_LIMIT.value is not None:
        return BUTTON_REFRESH_HISTORY_LIMIT.value
    button_refresh_history_limit_string = os.environ.get(
        "TRAITORS_BUTTON_REFRESH_HITORY_LIMIT"
    )
    if button_refresh_history_limit_string:
        try:
            return int(button_refresh_history_limit_string)
        except Exception as e:
            await discord_interface.send_error(
                (
                    f"Unable to parse environment variable `TRAITORS_BUTTON_REFRESH_HITORY_LIMIT` "
                    f"as int: `{button_refresh_history_limit_string}`.\n\nDefaulting to {default}"
                )
            )
    return default


def main(argv):

    guild_id = (
        SERVER_ID.value if SERVER_ID.value else os.environ.get("TRAITORS_SERVER_ID")
    )
    if not guild_id:
        raise ValueError(
            "Server ID not provided. Set 'server_id' flag or 'TRAITORS_SERVER_ID' environment variable."
        )
    guild_id = int(guild_id)

    bot_token = (
        BOT_TOKEN.value if BOT_TOKEN.value else os.environ.get("TRAITORS_BOT_TOKEN")
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
        saved_game_path = SAVED_GAME_PATH.value
        if not saved_game_path:
            saved_game_path = os.path.join(
                os.path.dirname(os.path.abspath(argv[0])), "saved_games"
            )

        discord_interface = DiscordInterface(
            client=client, guild_id=guild_id, saved_game_path=saved_game_path
        )

        setup_commands.setup_commands(tree, client, discord_interface)
        game_controls.GameControls(tree, guild_id, client, discord_interface)
        await tree.sync(guild=discord.Object(id=guild_id))
        print(f"Logged in as {client.user}. Let the game begin.")
        await discord_interface.send_controls_message(
            title="Here I am!",
            description="Claudia bot has been loaded.",
        )
        await discord_interface.refresh_load_game_views(
            limit=await get_button_refresh_history_limit(discord_interface)
        )
        await discord_interface.send_controls_message(
            title="Butons refreshed!",
            description="Claudia bot has been loaded.",
        )

    client.run(bot_token)


if __name__ == "__main__":
    app.run(main)
