from __future__ import annotations
from collections.abc import Iterable
import base64
from datetime import datetime
import io
import os
import pickle
import discord
from . import constants
from dataclasses import dataclass
from enum import Enum
import random
import asyncio
from discord.ui import Button, View
import re

# TODO: Decide whether to use this on every function
# def requires_init(func):
#     def wrapper(self, *args, **kwargs):
#         if not self._initialized:
#             raise RuntimeError(f"Cannot call {func.__name__}. Object not initialized.")
#         return func(self, *args, **kwargs)

#     return wrapper


@dataclass
class Player:
    class State(Enum):
        ACTIVE = "active"
        DEAD = "dead"
        BANISHED = "banished"

    id: int
    name: str
    display_name: str
    is_traitor: bool = False
    state: State = State.ACTIVE


class DiscordError(discord.Embed):
    def __init__(self, description: str):
        super().__init__(
            title="ERROR", description=description, color=discord.Color.red()
        )


class ConfirmButton(Button):
    def __init__(
        self,
        discord_interface: DiscordInterface,
        traitors: set[discord.Member],
        label: str,
        click_response: str,
        final_announcement: discord.Embed,
    ):
        super().__init__(label=label, style=discord.ButtonStyle.blurple)
        self.discord_interface = discord_interface
        self.traitors_left = traitors
        self.lock = asyncio.Lock()
        self.click_response = click_response
        self.final_announcement = final_announcement

    async def callback(self, interaction: discord.Interaction):
        async with self.lock:
            if interaction.user not in self.traitors_left:
                await interaction.response.defer()
                return

            await interaction.response.send_message(self.click_response, ephemeral=True)
            self.traitors_left.discard(interaction.user)
            if len(self.traitors_left) == 0:
                announcements_channel = (
                    await self.discord_interface.announcements_channel
                )
                await announcements_channel.send(embed=self.final_announcement)
                self.disabled = True
                await interaction.message.edit(view=self.view)


class LoadGameView(discord.ui.View):
    def __init__(self, message: discord.Message, discord_interface: DiscordInterface):
        super().__init__(timeout=None)
        self.message = message
        self.discord_interface = discord_interface

    @discord.ui.button(
        label="Load game",
        style=discord.ButtonStyle.primary,
        custom_id="load_game_button",
    )
    async def process_attachment(
        self, ctx: discord.Interaction, button: discord.ui.Button
    ):
        # TODO: make this better/more informational
        await self.discord_interface.load_game(
            ctx, await self.message.attachments[0].read()
        )


class NewPlayerEmbed(discord.Embed):
    def __init__(
        self,
        discord_interface: DiscordInterface,
        players: Iterable[Player],
        probabilty: float,
    ):
        super().__init__(
            title="New players added to game",
            description=(
                f"{discord_interface._display_players(players)} added with {probabilty:.1f} "
                "probability of being a traitor."
            ),
        )


class NewProbabilityModal(discord.ui.Modal):
    def __init__(
        self,
        discord_interface: DiscordInterface,
        players: Iterable[Player],
        title: str = "New probability",
    ):
        super().__init__(title=title)
        self.discord_interface = discord_interface
        self.players = players

    text_input = discord.ui.TextInput(
        label="Enter a value between 0 and 1",
        placeholder="Type something here...",
        max_length=100,
        style=discord.TextStyle.short,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            probability = float(self.text_input.value)
        except ValueError:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Invalid probaility input",
                    description=(
                        "Could not convert input to float:   "
                        f"'{self.text_input.value}'.\n\nPlease try again"
                    ),
                    color=discord.Color.red(),
                )
            )
            return
        await self.discord_interface.add_players(self.players, probability)
        await interaction.response.send_message(
            embed=NewPlayerEmbed(self.discord_interface, self.players, probability),
            ephemeral=True,
        )
        self.stop()


# TODO: use button to change probability
class NewPlayersView(discord.ui.View):
    def __init__(
        self, discord_interface: DiscordInterface, new_players: Iterable[Player]
    ):
        super().__init__()

        # Default probablity is 0.22, as assuming 10 initial players,
        # with 2-3 traitors and min probability of .8, this gives
        # the same probability for any new players.
        self.traitor_probability: float = 0.22
        self.discord_interface = discord_interface
        self.players = new_players

    async def _disable_buttons(self, ctx: discord.Interaction):
        for child in self.children:
            print(child.type)
            if child.type is discord.ComponentType.button:
                print("is_buttiwn")
                child.disabled = True
                await ctx.response.edit_message(view=self)

    @discord.ui.button(
        label="Yes",
        style=discord.ButtonStyle.green,
        # TODO: better labesls for yes and no
        custom_id="yes_buton",
    )
    async def yes(self, ctx: discord.Interaction, button: discord.ui.Button):
        await self.discord_interface.add_players(self.players, self.traitor_probability)
        await ctx.response.send_message(
            embed=NewPlayerEmbed(
                self.discord_interface, self.players, self.traitor_probability
            )
        )
        await self._disable_buttons(ctx)
        button.disabled = True

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.red,
        custom_id="no_button",
    )
    async def no(self, ctx: discord.Interaction, button: discord.ui.Button):
        await self._disable_buttons()
        # TODO: Banish players
        pass

    @discord.ui.button(
        label="Change probability",
        style=discord.ButtonStyle.primary,
        custom_id="change_probability_button",
    )
    async def change_probability(
        self, ctx: discord.Interaction, button: discord.ui.Button
    ):
        await ctx.response.send_modal(
            NewProbabilityModal(self.discord_interface, self.players)
        )
        # TODO: disable all buttons

    # @discord.ui.select(
    #     placeholder="Respond",
    #     min_values=1,
    #     max_values=1,
    #     options=[
    #         discord.SelectOption(label="Yes", value="yes"),
    #         discord.SelectOption(label="No", value="no"),
    #         discord.SelectOption(
    #             label="Change probability", value="change_probability"
    #         ),
    #     ],
    # )
    # async def select_callback(
    #     self, ctx: discord.Interaction, select: discord.ui.Select
    # ):
    #     match select.values[0]:
    #         case "yes":
    #         case "change_probability":
    #             await ctx.response.send_modal(
    #                 NewProbabilityModal(self.game, self.players)
    #             )
    #         case "no":
    #             pass
    #         case _:
    #             pass


class DiscordInterface:
    def __init__(self, client: discord.Client, guild_id: int, saved_game_path: str):
        self.client = client
        self.guild_id = guild_id
        self.saved_game_path = saved_game_path
        self.private_channel_permissions = {
            self.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            self.guild.me: discord.PermissionOverwrite(view_channel=True),
        }
        self.read_only_permissons = {
            self.guild.default_role: discord.PermissionOverwrite(
                send_messages=False,
                create_public_threads=False,
                create_private_threads=False,
            ),
            self.guild.me: discord.PermissionOverwrite(send_messages=True),
        }

    # ------------------------------[ Getters ]------------------------------

    @property
    def guild(self) -> discord.Guild:
        guild = self.client.get_guild(self.guild_id)
        if not guild:
            raise ValueError(f"Could not find guild from guild id: '{self.guild_id}'")
        return guild

    @property
    async def general_channel(self) -> discord.TextChannel:
        general_channel = discord.utils.get(
            self.guild.text_channels, name=constants.kGeneralChannelName
        )
        if not general_channel:
            general_channel = await self.guild.create_text_channel(
                constants.kGeneralChannelName
            )
        return general_channel

    @property
    async def announcements_channel(self) -> discord.TextChannel:
        # Read only announcements channel that only Claudia can send messages to
        announcements_channel = discord.utils.get(
            self.guild.text_channels, name=constants.kAnnouncementsChannelName
        )
        if not announcements_channel:
            announcements_channel = await self.guild.create_text_channel(
                constants.kAnnouncementsChannelName,
                overwrites=self.read_only_permissons,
            )
        return announcements_channel

    @property
    async def traitors_instructions_channel(self) -> discord.TextChannel:
        # Private instructions channel for only traitors (initially with just Claudia and the owner)
        traitors_instructions_channel = discord.utils.get(
            self.guild.text_channels, name=constants.kTraitorsInstructionsChannelName
        )
        if not traitors_instructions_channel:
            traitors_instructions_channel = await self.guild.create_text_channel(
                constants.kTraitorsInstructionsChannelName,
                overwrites=self.private_channel_permissions,
            )
        return traitors_instructions_channel

    @property
    async def traitors_chat_channel(self) -> discord.TextChannel:
        # Private chat channel for only traitors (initially with just Claudia and the owner)
        traitors_chat_channel = discord.utils.get(
            self.guild.text_channels, name=constants.kTraitorsChatChannelName
        )
        if not traitors_chat_channel:
            traitors_chat_channel = await self.guild.create_text_channel(
                constants.kTraitorsChatChannelName,
                overwrites=self.private_channel_permissions,
            )
        return traitors_chat_channel

    @property
    async def controls_channel(self) -> discord.TextChannel:
        controls_channel = discord.utils.get(
            self.guild.text_channels, name=constants.kControlsChannelName
        )
        if not controls_channel:
            controls_channel = await self.guild.create_text_channel(
                constants.kControlsChannelName,
                overwrites=self.private_channel_permissions,
            )
        return controls_channel

    async def _get_role(self, role_name: str):
        role = discord.utils.get(self.guild.roles, name=role_name)
        if not role:
            role = await self.guild.create_role(name=role_name)
        return role

    async def _banished_role(self):
        return await self._get_role(constants.kBanishedRoleName)

    async def _dead_role(self):
        return await self._get_role(constants.kDeadRoleName)

    # ------------------------------[ Game State Information ]------------------------------
    async def _is_player(
        self, member: discord.Member, only_active_players: bool
    ) -> bool:
        """Check if member is human player."""
        if member in {self.guild.me, self.guild.owner}:
            # member is bot or guild owner
            return False
        if only_active_players and not await self._is_active(member):
            # Player is out
            return False
        return True

    async def _get_players(self, only_active_players: bool) -> list[discord.Member]:
        return [
            member
            for member in self.guild.members
            if await self._is_player(member, only_active_players)
        ]

    async def _player_data(self, member: discord.Member) -> Player:
        return Player(
            id=member.id,
            name=member.name,
            display_name=member.display_name,
            is_traitor=await self._is_traitor(member, only_active_players=False),
            state=await self._get_state(member),
        )

    async def _get_players_data(self, only_active_players: bool) -> list[Player]:
        return [
            await self._player_data(member)
            for member in await self._get_players(only_active_players)
        ]

    def _player_member(self, player: Player):
        return self.guild.get_member(player.id)

    async def num_players(self, only_active_players):
        return len(await self._get_players(only_active_players))

    # TODO: decide input types
    def _display_players(self, players: Iterable[Player]) -> str:
        players = [player.display_name for player in players]
        if len(players) == 1:
            return players[0]
        if len(players) == 2:
            return " and ".join(players)
        out = players.copy()
        out[-1] = f"and {out[-1]}"
        return ", ".join(out)

    async def _is_traitor(
        self, member: discord.Member, only_active_players: bool
    ) -> bool:
        if not await self._is_player(member, only_active_players):
            return False
        if (
            (await self.traitors_instructions_channel)
            .permissions_for(member)
            .view_channel
        ):
            return True
        return False

    async def _get_faithful(self, only_active_players: bool) -> set[discord.Member]:
        return {
            player
            for player in await self._get_players(only_active_players)
            if not await self._is_traitor(player, only_active_players)
        }

    async def _get_traitors(self, only_active_players: bool) -> set[discord.Member]:
        return {
            player
            for player in await self._get_players(only_active_players)
            if await self._is_traitor(player, only_active_players)
        }

    async def _get_state(self, player: discord.Member) -> Player.State:
        if await self._is_banished(player):
            return Player.State.BANISHED
        elif await self._is_dead(player):
            return Player.State.DEAD
        return Player.State.ACTIVE

    async def _is_banished(self, player: discord.Member) -> bool:
        banished_role = await self._banished_role()
        if banished_role in player.roles:
            return True
        return False

    # async def _get_banished(self):
    #     return {
    #         player
    #         for player in await self._get_players(only_active_players=False)
    #         if not await self._is_banished(player)
    #     }

    async def _is_dead(self, player: discord.Member) -> bool:
        dead_role = await self._dead_role()
        if dead_role in player.roles:
            return True
        return False

    # async def _get_dead(self):
    #     return {
    #         player
    #         for player in await self._get_players(only_active_players=False)
    #         if not await self._is_dead(player)
    #     }

    async def _is_active(self, player: discord.Member) -> bool:
        return not (await self._is_dead(player) or await self._is_banished(player))

    # ------------------------------[ Actions ]------------------------------
    async def send_error(self, description: str):
        await (await self.controls_channel).send(
            embed=DiscordError(description=description)
        )

    async def send_controls_message(
        self,
        title: str,
        description: str = "",
        color: discord.Color = discord.Color.green(),
    ):
        await (await self.controls_channel).send(
            embed=discord.Embed(title=title, description=description, color=color)
        )

    async def kill(self, victims: list[discord.User]) -> None:
        for victim in victims:
            victim_member = await self.guild.fetch_member(victim.id)
            await victim_member.add_roles(await self._dead_role())

    async def banish(self, player: discord.Member) -> bool:
        if await self._banished_role() in player.roles:
            return False
        await player.add_roles(await self._banished_role())
        return True

    async def make_traitor(self, player: discord.Member):
        await (await self.traitors_instructions_channel).set_permissions(
            player,
            view_channel=True,
            send_messages=False,
            create_public_threads=False,
            create_private_threads=False,
        )
        await (await self.traitors_chat_channel).set_permissions(
            player,
            view_channel=True,
            send_messages=True,
        )
        return True

    async def assign_traitors(self, num_traitors: int) -> list[discord.Member]:
        traitors = random.sample(
            list(await self._get_players(only_active_players=True)), num_traitors
        )
        chat_channel_id = (await self.traitors_chat_channel).id
        intructions_channel_id = (await self.traitors_instructions_channel).id
        for traitor in traitors:
            await self.make_traitor(traitor)
            await traitor.send(
                embed=discord.Embed(
                    title=f"Congratulations, you have been selected to be a traitor!",
                    description=(
                        "The traitors private channels are now available to you. You can "
                        "communicate with your fellow traitors using the private chat channel:\n\n"
                        f"<#{chat_channel_id}>"
                    ),
                    color=discord.Color.purple(),
                )
            )
        if not await self.check_num_traitors({num_traitors}):
            return
        await (await self.traitors_chat_channel).send(
            embed=discord.Embed(
                title=f"Welcome traitors",
                description=(
                    "You may reveal yourself to your fellow traitors here. "
                    "When you are ready, visit the traitors instructions channel "
                    "to take the Traitor's Oath and begin the game.\n\n"
                    f"<#{intructions_channel_id}>"
                ),
                color=discord.Color.purple(),
            )
        )
        for player in await self._get_faithful(only_active_players=True):
            await player.send(
                embed=discord.Embed(
                    title="The game has begun!",
                    description="You are a **faithful**.",
                    color=discord.Color.purple(),
                )
            )
        return traitors

    async def confirm_traitors(self):
        traitors = await self._get_traitors(only_active_players=True)
        view = View()
        view.add_item(
            ConfirmButton(
                discord_interface=self,
                traitors=traitors,
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
        instructions_channel = await self.traitors_instructions_channel
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

    async def check_num_traitors(self, valid_nums: set[int]) -> bool:
        num_instructions_members = 0
        num_chat_members = 0
        for player in await self._get_players(only_active_players=True):
            if (
                (await self.traitors_instructions_channel)
                .permissions_for(player)
                .view_channel
            ):
                num_instructions_members += 1
            if (await self.traitors_chat_channel).permissions_for(player).view_channel:
                num_chat_members += 1
        if (
            num_instructions_members not in valid_nums
            or num_chat_members not in valid_nums
        ):
            await self.send_error(DiscordError("Incorrect number of traitors!"))
            return False
        return True

    async def add_player(
        self,
        player: discord.Member,
        traitor_probability: float,
    ):
        if random.random() < traitor_probability:
            await self.make_traitor(player)
            role = "traitor"
        else:
            role = "faithful"
        await player.send(
            embed=discord.Embed(
                title="Welcome to the game",
                description=f"You are entering as a **{role}**.",
                color=discord.Color.purple(),
            )
        )

    async def add_players(self, players: Iterable[Player], traitor_probability: float):
        for player in players:
            player_member = self._player_member(player)
            if not player_member:
                await self.send_error(
                    description=(
                        f"Player {player.display_name} ({player.name}) "
                        "could not be added to game. Not found in guild."
                    )
                )
            await self.add_player(player_member, traitor_probability)

    async def in_controls_channel(self, ctx: discord.Interaction) -> bool:
        if ctx.channel.name == constants.kControlsChannelName:
            return True
        await ctx.response.send_message(
            embed=DiscordError("Must execture this command from control channel!"),
            ephemeral=True,
        )
        return False

    async def check_owner(self, ctx: discord.Interaction) -> bool:
        if ctx.user == ctx.guild.owner:
            return True
        await ctx.response.send_message(
            embed=DiscordError("Command must be executed by owner of guild!"),
            ephemeral=True,
        )
        return False

    async def clear_traitors(self):
        for channel in [
            await self.traitors_instructions_channel,
            await self.traitors_chat_channel,
        ]:
            for user_or_role in channel.overwrites.keys():
                # Skip the bot and server owner
                if user_or_role != self.guild.me and user_or_role != self.guild.owner:
                    await channel.set_permissions(
                        user_or_role,
                        overwrite=discord.PermissionOverwrite(view_channel=False),
                    )

    async def clear_roles(self):
        for role in [await self._dead_role(), await self._banished_role()]:
            for player in await self._get_players(only_active_players=False):
                await player.remove_roles(role)

    async def delete_channels(self):
        for channel in self.guild.text_channels:
            if channel.name != constants.kControlsChannelName:
                await channel.delete()

    async def initialize(self, reset: bool):
        if reset:
            await self.delete_channels()
            await self.clear_roles()
        await self.general_channel
        await self.announcements_channel
        await self.traitors_instructions_channel
        await self.traitors_chat_channel
        await self.controls_channel

    async def save_game(self, ctx: discord.Interaction, name: str):
        await ctx.response.defer()
        name = re.sub(r"[ .]", "-", name)
        name = re.sub(r"[^a-zA-Z0-9-]", "", name)
        players = [
            (await self._player_data(player))
            for player in await self._get_players(only_active_players=False)
        ]
        pickled_players = pickle.dumps(players)
        saved_game = base64.urlsafe_b64encode(pickled_players)

        date = datetime.now().strftime("%m-%d-%Y")
        num_players = len(players)
        file_name = f"{name if name else "saved-game"}_{date}_{num_players}-players.dat"

        try:
            file_path = os.path.join(self.saved_game_path, file_name)
            with open(file_path, "wb") as f:
                f.write(saved_game)
            to_file = (
                f"**Note**: Game saved to {self.saved_game_path}. Can be accessed through /load_game "
                "command, or by providing this attachment to the /load_game_from_file command."
            )
        except Exception:
            to_file = (
                f"**Note**: Game could not be saved to {self.saved_game_path}. Must be loaded by "
                "providing this attachment to the /load_game_from_file command."
            )

        description = (
            f"A game has been saved with the following players:"
            f"\n* {"\n* ".join([ f"{player.display_name} ({player.name})" for player in players])}.\n\n"
            f"Attach the file to the `/load_game` command to load game.\n\n{to_file}"
        )

        message: discord.Message = await ctx.followup.send(
            embed=discord.Embed(
                title="Game saved!",
                description=description + " A copy has been DM'd to you as well.",
                color=discord.Color.green(),
            ),
            file=discord.File(io.BytesIO(saved_game), filename=file_name),
        )
        await message.edit(
            embeds=message.embeds,
            attachments=message.attachments,
            view=LoadGameView(message, self),
        )
        message = await ctx.user.send(
            embed=discord.Embed(
                title="Game saved!",
                description=description,
                color=discord.Color.green(),
            ),
            file=discord.File(io.BytesIO(saved_game), filename=file_name),
        )
        await message.edit(
            embeds=message.embeds,
            attachments=message.attachments,
            view=LoadGameView(message, self),
        )

    async def load_game(
        self,
        ctx: discord.Interaction,
        saved_game: str,
        new_player_traitor_probability: float = 0.22,
    ):
        await ctx.response.defer()

        async def decode(encoded_text: str) -> list[Player]:
            """Decodes the encoded string back to a list of member IDs."""
            try:
                return pickle.loads(base64.urlsafe_b64decode(encoded_text))
            except UnicodeDecodeError as e:
                await ctx.followup.send(
                    embed=DiscordError(
                        f"Unable to decode saved game. The file may be corrupted.\n\n{e}"
                    )
                )
                return None

        await self.initialize(reset=True)
        players = await decode(saved_game)
        if not players:
            return
        players_dict = {player.id: player for player in players}
        missing_players: list[str] = []
        old_players: set[int] = set()

        for id, player in players_dict.items():
            player_member = self._player_member(player)
            if not player_member:
                missing_players.append(f"{player.display_name} ({player.name})")
                continue
            old_players.add(id)
            if player.is_traitor:
                await self.make_traitor(player_member)
            description = (
                f"You are a **{"traitor" if player.is_traitor else "faithful"}**."
            )
            match player.state:
                case Player.State.ACTIVE:
                    pass
                case Player.State.BANISHED:
                    description += " Unfortunately, you have been banished."
                    await self.banish(player_member)
                case Player.State.DEAD:
                    description += (
                        " Unfortunately, you have been killed by the traitors."
                    )
                    await self.kill(victims=[player_member])
            await player_member.send(
                embed=discord.Embed(
                    title="A game has been loaded",
                    description=description,
                    color=discord.Color.purple(),
                )
            )

        current_players_dict = {
            player.id: player
            for player in (await self._get_players_data(only_active_players=False))
        }

        new_players = set(current_players_dict.keys()) - old_players
        description = ""
        if missing_players:
            await ctx.channel.send(
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
            new_players = [current_players_dict[player_id] for player_id in new_players]
            await ctx.channel.send(
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
                view=NewPlayersView(self, new_players),
            )
            return
        loaded_embed = discord.Embed(
            title="Game loaded!",
            description=description,
            color=discord.Color.green(),
        )
        await ctx.followup.send(embed=loaded_embed)
        if not await self.in_controls_channel(ctx):
            (await self.controls_channel).send(embed=loaded_embed)

    async def maybe_refresh_message(self, message: discord.Message):
        if message.author == self.guild.me and message.components:
            for component in message.components:
                if type(component) is not discord.components.ActionRow:
                    continue
                for child in component.children:
                    if child.custom_id == "load_game_button":
                        view = LoadGameView(message, self)
                        message.interaction_metadata
                        await message.edit(
                            attachments=message.attachments,
                            embeds=message.embeds,
                            view=view,
                        )

    async def refresh_load_game_views(self, limit):
        if limit == 0:
            print("Skipping button refreshes")
            return

        print(
            f"Checking channel history for button refreshes. Limit {limit} messages...\n"
        )
        controls = await self.controls_channel
        async for message in controls.history(limit=limit):
            await self.maybe_refresh_message(message)
        for member in controls.members:
            if member is self.guild.me:
                continue
            async for message in member.history(limit=limit):
                await self.maybe_refresh_message(message)

    # TODO: use inheritance from discord.Emed:
    # error
    # channel_not_found_error
    # send_error
