import discord
from discord import app_commands
import constants
from claudia_utils import ClaudiaUtils
from discord.ui import Select, View, Button
import asyncio
from num2words import num2words
import random
import base64
import binascii
import json


def SetupCommands(
    tree: app_commands.CommandTree, guild_id: int, client: discord.Client
):
    utils = ClaudiaUtils(client, guild_id)

    @tree.command(
        name="test", description="Test the bot", guild=discord.Object(id=guild_id)
    )
    async def Test(ctx: discord.Interaction):
        if not await utils.CheckControlChannel(ctx):
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
        guild=discord.Object(id=guild_id),
    )
    async def AddToControls(ctx: discord.Interaction, player: discord.User):
        if not await utils.CheckControlChannel(ctx) or not await utils.CheckOwner(ctx):
            return
        await ctx.channel.set_permissions(player, view_channel=True)
        await ctx.response.send_message(f"{player.name} added!")
        return

    @tree.command(
        name="remove_from_controls",
        description="Remove a player from the controls channel",
        guild=discord.Object(id=guild_id),
    )
    async def RemoveFromControls(ctx: discord.Interaction, player: discord.User):
        if not await utils.CheckControlChannel(ctx) or not await utils.CheckOwner(ctx):
            return
        guild = utils.Guild()
        await ctx.channel.set_permissions(player, view_channel=False)
        await ctx.response.send_message(f"{player.name} removed!")
        return

    class ConfirmButton(Button):
        def __init__(
            self,
            traitors: set[discord.Member],
            label: str,
            click_response: str,
            final_announcement: discord.Embed,
        ):
            super().__init__(label=label, style=discord.ButtonStyle.blurple)
            self.traitors_left = traitors
            self.lock = asyncio.Lock()
            self.click_response = click_response
            self.final_announcement = final_announcement

        async def callback(self, interaction: discord.Interaction):
            async with self.lock:
                if interaction.user not in self.traitors_left:
                    await interaction.response.defer()
                    return

                await interaction.response.send_message(
                    self.click_response, ephemeral=True
                )
                self.traitors_left.discard(interaction.user)
                if len(self.traitors_left) == 0:
                    announcements_channel = await utils.AnnouncementsChannel()
                    await announcements_channel.send(embed=self.final_announcement)
                    self.disabled = True
                    await interaction.message.edit(view=self.view)

    async def ConfirmTraitors(traitors: set[discord.Member]):
        view = View()
        view.add_item(
            ConfirmButton(
                traitors,
                label="I swear",
                click_response=(
                    "And with that, you are now a traitor. The game will "
                    "commence when all of the traitors have taken the oath."
                ),
                final_announcement=discord.Embed(
                    title="The traitors have been selected",
                    description="Let the game begin.",
                    color=discord.Color.purple(),
                ),
            )
        )
        instructions_channel = await utils.TraitorsInstructionsChannel()
        await instructions_channel.send(
            embed=discord.Embed(
                title="Before you don your cloak, you must take the Traitor's Oath.",
                description=(
                    "🔪 Do you commit to lying and deceiving your way through this game?\n\n"
                    "🔪 Do you swear to murder your fellow players throughout the game?\n\n"
                    "🔪 Do you vow to keep your identity and the identity of your fellow traitors a secret?"
                ),
                color=discord.Color.dark_magenta(),
            ),
            view=view,
        )

    async def InitializeImpl(
        output_channel: discord.TextChannel,
        reset: bool = True,
    ):
        guild = utils.Guild()

        if reset:
            for channel in client.get_guild(guild_id).text_channels:
                if channel.name != constants.kControlsChannelName:
                    await channel.delete()
            banished_role = discord.utils.get(guild.roles, name=constants.kBanishedRoleName)
            if banished_role:
                for player in utils.GetPlayers():
                    # if banished_role in player.roles:
                    await player.remove_roles(banished_role)

        private_channel_permissions = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True),
        }

        # Create general channel
        general_channel = utils.GeneralChannel()
        if not general_channel:
            general_channel = await guild.create_text_channel(
                constants.kGeneralChannelName
            )

        # Create controls channel
        controls_channel = utils.ControlsChannel()
        if not controls_channel:
            controls_channel = await guild.create_text_channel(
                constants.kControlsChannelName, overwrites=private_channel_permissions
            )

        # Create read only announcements channel that only Claudia can send messages to
        read_only = {
            guild.default_role: discord.PermissionOverwrite(
                send_messages=False,
                create_public_threads=False,
                create_private_threads=False,
            ),
            guild.me: discord.PermissionOverwrite(send_messages=True),
        }
        announcements_channel = await utils.AnnouncementsChannel(send_error=False)
        if not announcements_channel:
            announcements_channel = await guild.create_text_channel(
                constants.kAnnouncementsChannelName, overwrites=read_only
            )

        # Create private instructions channel for only traitors (initially with just Claudia and the owner)
        traitors_instructions_channel = await utils.TraitorsInstructionsChannel(
            send_error=False
        )
        if not traitors_instructions_channel:
            traitors_instructions_channel = await guild.create_text_channel(
                constants.kTraitorsInstructionsChannelName,
                overwrites=private_channel_permissions,
            )

        traitors_chat_channel = await utils.TraitorsChatChannel(send_error=False)
        if not traitors_chat_channel:
            traitors_chat_channel = await guild.create_text_channel(
                constants.kTraitorsChatChannelName,
                overwrites=private_channel_permissions,
            )

    @tree.command(
        name="initialize",
        description="Reset the traitors server",
        guild=discord.Object(id=guild_id),
    )
    async def Initialize(
        ctx: discord.Interaction,
        reset: bool = False,
    ):
        if reset and not await utils.CheckControlChannel(ctx):
            return False
        await ctx.response.send_message("Initializing server...")
        await InitializeImpl(ctx.channel, reset)
        await ctx.edit_original_response(content="Server initialized!")

    @tree.command(
        name="new_game",
        description="Start a new game",
        guild=discord.Object(id=guild_id),
    )
    async def NewGame(
        ctx: discord.Interaction,
        min_num_traitors: int = 2,
        probability_of_min: float = 0.8,
    ):
        if not await utils.CheckControlChannel(ctx):
            return False
        num_traitors = (
            min_num_traitors
            if random.random() < probability_of_min
            else min_num_traitors + 1
        )
        players = utils.GetPlayers()
        if len(players) < min_num_traitors + (0 if probability_of_min >= 1 else 1):
            await ctx.response.send_message(
                embed=utils.Error(
                    "Possible number of traitors higher than number of players"
                )
            )
            return
        await ctx.response.send_message(
            f"Starting game with {num2words(min_num_traitors)} or {num2words(min_num_traitors + 1)} traitors..."
        )

        await InitializeImpl(ctx.channel)

        traitors_instructions = await utils.TraitorsInstructionsChannel()
        traitors_chat = await utils.TraitorsChatChannel()
        if not traitors_instructions or not traitors_chat:
            return

        traitors = random.sample(list(utils.GetPlayers()), num_traitors)
        for traitor in traitors:
            await utils.AddTraitor(traitor)
            await traitor.send(
                embed=discord.Embed(
                    title=f"Congratulations, you have been selected to be a traitor!",
                    description=(
                        "The traitors private channels are now available to you. You can "
                        "communicate with your fellow traitors using the private chat channel:\n\n"
                        f"<#{traitors_chat.id}>"
                    ),
                    color=discord.Color.purple(),
                )
            )
        if not await utils.CheckNumTraitors({min_num_traitors, min_num_traitors + 1}):
            return
        await traitors_chat.send(
            embed=discord.Embed(
                title=f"Welcome traitors",
                description=(
                    "You may reveal yourself to your fellow traitors here. "
                    "When you are ready, visit the traitors instructions channel "
                    "to take the Traitor's Oath and begin the game.\n\n"
                    f"<#{traitors_instructions.id}>"
                ),
                color=discord.Color.purple(),
            )
        )
        for player in await utils.GetFaithful():
            await player.send(
                embed=discord.Embed(
                    title="The game has begun!",
                    description="You are a **faithful**.",
                    color=discord.Color.purple(),
                )
            )
        await ctx.channel.send(
            embed=discord.Embed(
                title="New game started successfully!", color=discord.Color.green()
            )
        )
        await ConfirmTraitors(await utils.GetTraitors())

    @tree.command(
        name="save_game",
        description="Save the traitors as an encoded string",
        guild=discord.Object(id=guild_id),
    )
    async def SaveGame(interaction: discord.Interaction):
        def encode(players: dict) -> str:
            string = json.dumps(players)
            return base64.urlsafe_b64encode(string.encode()).decode()

        players = {
            "faithful": {
                member.id: member.name for member in await utils.GetFaithful()
            },
            "traitor": {member.id: member.name for member in await utils.GetTraitors()},
        }

        saved_game = encode(players)

        description = (
            f"A game has been saved with the following players:"
            f"\n* {"\n* ".join([ player.name for player in utils.GetPlayers()])}.\n\n"
            "Copy the following text and paste into the `/load_game` command to load game."
        )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Game saved!",
                description=description + " A copy has been DM'd to you as well.",
                color=discord.Color.green(),
            )
        )
        await interaction.channel.send(f"```{saved_game}```")
        await interaction.user.send(
            embed=discord.Embed(
                title="Game saved!",
                description=description,
                color=discord.Color.green(),
            )
        )
        await interaction.user.send(f"```{saved_game}```")

    @tree.command(
        name="load_game",
        description="Load the traitors from an encoded string",
        guild=discord.Object(id=guild_id),
    )
    @app_commands.describe(
        new_player_traitor_probability="Probability that new players (players not in the game on save) will be added as traitors."
    )
    async def LoadGame(
        interaction: discord.Interaction,
        saved_game: str,
        new_player_traitor_probability: float = 0.22,
    ):
        if not await utils.CheckControlChannel(interaction):
            return
        await InitializeImpl(interaction.channel)

        async def decode(encoded_text) -> dict[str, dict[int, str]]:
            """Decodes the encoded string back to a list of member IDs."""
            try:
                return json.loads(
                    base64.urlsafe_b64decode(encoded_text.strip("`").encode()).decode()
                )
            except (binascii.Error, UnicodeDecodeError) as e:
                await interaction.response.send_message(
                    embed=utils.Error(
                        "Unable to decode saved game. make sure you copied it correctly."
                    )
                )
                return None

        missing_players = set()
        old_players = set()
        guild = utils.Guild()
        decoded_game = await decode(saved_game)
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
        current_players = utils.GetPlayers()

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

            await interaction.response.send_message(
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
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Game loaded!",
                description=description,
                color=discord.Color.green(),
            )
        )

    @tree.command(
        name="check_traitors",
        description="Check that the number of traitors is as expected",
        guild=discord.Object(id=guild_id),
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
        guild=discord.Object(id=guild_id),
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
        guild=discord.Object(id=guild_id),
    )
    async def Demo(ctx: discord.Interaction):
        if not await utils.CheckControlChannel(ctx):
            return
        await ctx.response.defer()
        await InitializeImpl(ctx.channel, reset=True)
        failed = []
        for player in utils.GetPlayers():
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
                utils.GetPlayers(),
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
        guild=discord.Object(id=guild_id),
    )
    async def ClearAllTraitors(ctx: discord.Interaction):
        await utils.ClearTraitors()
        await ctx.response.send_message("All traitors removed.")

    @tree.command(
        name="delete_messsages",
        description="Delete messages in channel",
    )
    async def DeleteMessages(ctx, limit:int=500):
        await ctx.response.send_message(f"Deleting {limit} messages...", delete_after=2)  # Auto-delete the confirmation message
        await asyncio.sleep(3)
        await ctx.channel.purge(limit=limit)
