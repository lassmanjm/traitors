import discord
import regex
from discord import app_commands
import contextlib
from claudia_utils import ClaudiaUtils
from discord.ui import Select, View, Button
import asyncio
from num2words import num2words
import random
import base64
import binascii
import json
from datetime import datetime
import os
import io
from dataclasses import dataclass
from enum import Enum
import pickle
from interface import DiscordInterface


class PlayerStatus(Enum):
    ACTIVE = "active"
    DEAD = "dead"
    BANISHED = "banished"


@dataclass
class Player:
    id: int
    name: str
    display_name: str
    is_traitor: bool
    status: PlayerStatus


@contextlib.contextmanager
def maybe_in_mem_file(file_name, content):
    try:
        file_path = os.path.join("/saved_games", file_name)
        with open(file_path, "wb") as f:
            f.write(content)
        f = io.BytesIO(content)
        yield discord.File(f, filename=file_name)
    except Exception:
        f = io.BytesIO(content)
        yield discord.File(f, filename=file_name)


def setup_commands(
    tree: app_commands.CommandTree,
    client: discord.Client,
    discord_interface: DiscordInterface,
):
    utils = ClaudiaUtils(client, discord_interface.guild_id)

    @tree.command(
        name="test",
        description="Test the bot",
        guild=discord.Object(id=discord_interface.guild_id),
    )
    async def test(ctx: discord.Interaction):
        if not await discord_interface.in_controls_channel(ctx):
            return
        await ctx.response.send_message(
            embed=discord.Embed(
                title="Success",
                description="I am still here!",
                color=discord.Color.green(),
            )
        )

    @tree.command(
        name="add_to_controls",
        description="Add player to the controls channel",
        guild=discord.Object(id=discord_interface.guild_id),
    )
    async def add_to_controls(ctx: discord.Interaction, player: discord.User):
        if not await discord_interface.in_controls_channel(
            ctx
        ) or not await discord_interface.check_owner(ctx):
            return
        await (await discord_interface.controls_channel).set_permissions(
            player, view_channel=True
        )
        await ctx.response.send_message(f"{player.name} added!")
        return

    @tree.command(
        name="remove_from_controls",
        description="Remove a player from the controls channel",
        guild=discord.Object(id=discord_interface.guild_id),
    )
    async def remove_from_controls(ctx: discord.Interaction, player: discord.User):
        if not await discord_interface.in_controls_channel(
            ctx
        ) or not await discord_interface.check_owner(ctx):
            return
        await (await discord_interface.controls_channel).set_permissions(
            player, view_channel=False
        )
        await ctx.response.send_message(f"{player.name} removed!")
        return

    @tree.command(
        name="initialize",
        description="Reset the traitors server",
        guild=discord.Object(id=discord_interface.guild_id),
    )
    async def initialize(
        ctx: discord.Interaction,
        reset: bool = False,
    ):
        if reset and not await discord_interface.in_controls_channel(ctx):
            return False
        await ctx.response.send_message("Initializing server...")
        await discord_interface.initialize(reset)
        await ctx.edit_original_response(content="Server initialized!")

    @tree.command(
        name="new_game",
        description="Start a new game",
        guild=discord.Object(id=discord_interface.guild_id),
    )
    async def new_game(
        ctx: discord.Interaction,
        min_num_traitors: int = 2,
        probability_of_min: float = 0.8,
    ):
        if not await discord_interface.in_controls_channel(ctx):
            return
        await ctx.response.defer()
        num_traitors = (
            min_num_traitors
            if random.random() < probability_of_min
            else min_num_traitors + 1
        )
        num_players = await discord_interface.num_players(only_active_players=False)
        if num_players < min_num_traitors + (0 if probability_of_min >= 1 else 1):
            await ctx.followup.send(
                embed=utils.Error(
                    "Possible number of traitors higher than number of players"
                )
            )
            return
        await ctx.followup.send(
            f"Starting game with {num2words(min_num_traitors)} or {num2words(min_num_traitors + 1)} traitors..."
        )
        await discord_interface.initialize(reset=True)
        traitors = await discord_interface.assign_traitors(num_traitors)
        await discord_interface.confirm_traitors()

        await ctx.channel.send(
            embed=discord.Embed(
                title="New game started successfully!", color=discord.Color.green()
            )
        )

    class AttachmentView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(
            label="Load Game",
            style=discord.ButtonStyle.primary,
            custom_id="load_game_button",
        )
        async def process_attachment(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ) -> discord.Attachment:
            # return interaction.message.attachments[0]
            await interaction.response.send_message("hi")

    @tree.command(
        name="save_game",
        description="Save the traitors as an encoded string",
        guild=discord.Object(id=discord_interface.guild_id),
    )
    async def save_game(ctx: discord.Interaction, name: str = ""):
        await discord_interface.save_game(ctx, name)

    async def get_saved_game_choices(ctx: discord.Interaction, current: str):
        choices: list[app_commands.Choice] = []
        for file in os.listdir(discord_interface.saved_game_path):
            if not current.lower() in file.lower():
                continue
            match = regex.fullmatch(r"(.*)_(\d{2}-\d{2}-\d{4})_(\d+)-players.dat", file)
            if not match:
                continue
            choices.append(
                app_commands.Choice(
                    name=(
                        f"{match.group(3)} Players - "
                        f"{datetime.strptime(match.group(2), "%m-%d-%Y").strftime("%A, %B %d %Y")}"
                        f"{"" if match.group(1)=="saved_game" else ": " + match.group(1)}"
                    ),
                    value=file,
                )
            )
        return choices

    @tree.command(
        name="load_game",
        description=f"Load a game from {discord_interface.saved_game_path}",
        guild=discord.Object(id=discord_interface.guild_id),
    )
    @app_commands.autocomplete(saved_game=get_saved_game_choices)
    async def load_game(
        ctx: discord.Interaction,
        saved_game: str,
    ):
        with open(
            os.path.join(discord_interface.saved_game_path, saved_game), "rb"
        ) as f:
            await discord_interface.load_game(ctx, f.read())

    @tree.command(
        name="load_game_from_file",
        description="Load a game from an attached save game file.",
        guild=discord.Object(id=discord_interface.guild_id),
    )
    @app_commands.describe(
        new_player_traitor_probability="Probability that new players (players not in the game on save) will be added as traitors.",
    )
    async def LoadGame(
        interaction: discord.Interaction,
        saved_game: discord.Attachment,
        new_player_traitor_probability: float = 0.22,
    ):
        if not await utils.CheckControlChannel(interaction):
            return
        await interaction.response.defer()
        await initialize_impl(interaction.channel)

        async def decode(saved_game: discord.Attachment) -> list[Player]:
            """Decodes the encoded string back to a list of member IDs."""
            encoded_text = await saved_game.read()
            return pickle.loads(base64.urlsafe_b64decode(encoded_text))
            try:
                pass
            except (binascii.Error, UnicodeDecodeError) as e:
                await interaction.followup.send(
                    embed=utils.Error(
                        f"Unable to decode saved game. The file may be corrupted.\n\n{e}"
                    )
                )
                return None

        missing_players = set()
        old_players = set()
        guild = utils.Guild()
        decoded_game = await decode(saved_game)
        await interaction.followup.send(f"{decoded_game}")
        return
        if not decoded_game:
            return
        for id, name in decoded_game["traitor"].items():
            traitor = guild.get_member(int(id))
            if not traitor:
                missing_players.add(name)
                continue
            old_players.add(traitor)
            await traitor.send(
                embed=discord.Embed(
                    title="A game has been loaded",
                    description="You are a **traitor**.",
                    color=discord.Color.purple(),
                )
            )
            await utils.AddTraitor(traitor)
        for id, name in decoded_game["faithful"].items():
            faithful = guild.get_member(int(id))
            if not faithful:
                missing_players.add(name)
                continue
            old_players.add(faithful)
            await faithful.send(
                embed=discord.Embed(
                    title="A game has been loaded",
                    description="You are a **faithful**.",
                    color=discord.Color.purple(),
                )
            )
        current_players = await utils.GetPlayers(include_out_players=True)

        new_players = current_players - old_players
        description = ""
        if missing_players:
            await interaction.channel.send(
                embed=discord.Embed(
                    title="Missing Players",
                    description=(
                        "**__Missing Players__**\n"
                        "These players are no longer present in the server:"
                        f"\n* {"\n* ".join(missing_players)}."
                    ),
                    color=discord.Color.orange(),
                ),
            )
        if new_players:
            add_player = Select(
                custom_id="add_player",
                placeholder="Respond",
                options=[
                    discord.SelectOption(label="yes", value="yes"),
                    discord.SelectOption(label="no", value="no"),
                ],
            )
            view = View()
            view.add_item(add_player)

            await interaction.followup.send(
                embed=discord.Embed(
                    title="New Players",
                    description=(
                        "These players in the sever were not previously present:"
                        f"\n* {"\n* ".join({ player.name for player in new_players })}.\n\n"
                        f"Add new players to the game with {new_player_traitor_probability} "
                        "chance of being a traitor? Probability can be altered in load_game command call."
                    ),
                    color=discord.Color.orange(),
                ),
                view=view,
            )

            async def Callback(ctx: discord.Interaction):
                await AddPlayerCallback(
                    ctx, view, new_players, new_player_traitor_probability
                )
                await interaction.channel.send(
                    embed=discord.Embed(
                        title="Game loaded!", color=discord.Color.green()
                    )
                )

            add_player.callback = Callback
            return
        await interaction.followup.send(
            embed=discord.Embed(
                title="Game loaded!",
                description=description,
                color=discord.Color.green(),
            )
        )

    @tree.command(
        name="check_traitors",
        description="Check that the number of traitors is as expected",
        guild=discord.Object(id=discord_interface.guild_id),
    )
    async def CheckTraitors(ctx: discord.Interaction, min_expected: int):
        if not await utils.CheckNumTraitors({min_expected, min_expected + 1}):
            await ctx.response.send_message("Traitor initialization unsuccessful!")
            return
        await ctx.response.send_message(
            embed=discord.Embed(
                title="Success!",
                description="The traitors have been initialized successfully.",
                color=discord.Color.green(),
            )
        )
        return

    async def AddPlayer(player: discord.Member, probability: float = 0.22):
        if random.random() < probability:
            await utils.AddTraitor(player)
            await player.send(
                embed=discord.Embed(
                    title="Welcome to the game",
                    description="You are entering as a traitor.",
                    color=discord.Color.purple(),
                )
            )
            return
        await player.send(
            embed=discord.Embed(
                title="Welcome to the game",
                description="You are entering as a faithful.",
                color=discord.Color.purple(),
            )
        )

    async def AddPlayerCallback(
        interaction: discord.Interaction,
        view: View,
        players: set[discord.Member],
        probability: float,
    ):
        add_player_resonse = None
        for item in view.children:
            if item.custom_id == "add_player":
                add_player_resonse = item

        add_player_resonse.disabled = True
        await interaction.message.edit(view=view)

        if add_player_resonse.values[0] == "no":
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"Players not added.", color=discord.Color.red()
                )
            )
            return

        for player in players:
            await AddPlayer(player, probability)

        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{utils.DisplayPlayers(list(players))} added to game!",
                color=discord.Color.green(),
            )
        )

    @tree.command(
        name="add_player",
        description="Add player to game, possibly making them a traitor",
        guild=discord.Object(id=discord_interface.guild_id),
    )
    # Default probablity is .22, as assuming 10 initial players, with 2-3 traitors and min probability
    # of .8, this gives the same probability for any new players.
    async def AddPlayerCmd(
        ctx: discord.Interaction,
        player: discord.Member,
        traitor_probability: float = 0.22,
    ):
        if not await utils.CheckControlChannel(ctx):
            return
        # await ctx.response.send_message(f"Adding{member.display_name} to the game...")
        add_player = Select(
            custom_id="add_player",
            placeholder="Respond",
            options=[
                discord.SelectOption(label="yes", value="yes"),
                discord.SelectOption(label="no", value="no"),
            ],
        )
        view = View()
        view.add_item(add_player)

        await ctx.response.send_message(
            f"Confirm: Add {player.display_name} to the game with {traitor_probability} chance of being a traitor?",
            view=view,
        )
        add_player.callback = lambda ctx: AddPlayerCallback(
            ctx, view, {player}, traitor_probability
        )

    async def DmButtonCallback(interaction: discord.Interaction, button: Button):
        await utils.AddTraitor(interaction.user)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Well done!",
                description=(
                    "You have now been added to the traitors instructions and chat channels. "
                    f"Visit the instructions channel for further *instructions*."
                ),
                color=discord.Color.green(),
            )
        )
        button.disabled = True

    @tree.command(
        name="demo",
        description="Demonstrate the DM and private traitors channel for all players.",
        guild=discord.Object(id=discord_interface.guild_id),
    )
    async def Demo(ctx: discord.Interaction):
        if not await utils.CheckControlChannel(ctx):
            return
        await ctx.response.defer()
        await initialize_impl(ctx.channel, reset=True)
        failed = []
        players = await utils.GetPlayers(include_out_players=True)
        for player in players:
            dm_button = Button(style=discord.ButtonStyle.blurple)
            dm_button.label = "Click Me!"
            dm_button.callback = lambda interaction: DmButtonCallback(
                interaction, dm_button
            )
            view = View()
            view.add_item(dm_button)
            try:
                await player.send("Please confirm you have seen this DM:", view=view)

            except discord.Forbidden:
                failed.append(player.name)
            except discord.HTTPException as e:
                failed.append(player.name)
                await ctx.channel.send(f"Failed to send DM to {player.name}: {e}")

        num_failed = len(failed)
        await ctx.followup.send(
            embed=discord.Embed(
                title="DMs failed" if num_failed > 0 else "DMs successful",
                description=(
                    f"Failed to send to {num_failed} user(s):\n{"\n".join([f"* {failure}" for failure in failed])}"
                    if num_failed > 0
                    else ""
                ),
                color=(
                    discord.Color.red() if num_failed > 0 else discord.Color.green()
                ),
            )
        )
        if num_failed > 0:
            return
        view = View()
        view.add_item(
            ConfirmButton(
                players,
                label="Click Me!",
                click_response="Great work! Hold tight while everyone completes this.",
                final_announcement=discord.Embed(
                    title="Everyone has confirmed",
                    description="Let's play!",
                    color=discord.Color.green(),
                ),
            )
        )
        traitors_channel = await utils.TraitorsInstructionsChannel()
        await traitors_channel.send(
            "Please confirm you've seen the traitors channels:", view=view
        )

    @tree.command(
        name="clear_all_traitors",
        description="Remove all traitors",
        guild=discord.Object(id=discord_interface.guild_id),
    )
    async def ClearAllTraitors(ctx: discord.Interaction):
        await utils.ClearTraitors()
        await ctx.response.send_message("All traitors removed.")

    @tree.command(
        name="delete_messsages",
        description="Delete messages in channel",
    )
    async def DeleteMessages(ctx, limit: int = 500):
        await ctx.response.send_message(
            f"Deleting {limit} messages...", delete_after=2
        )  # Auto-delete the confirmation message
        await asyncio.sleep(3)
        await ctx.channel.purge(limit=limit)
