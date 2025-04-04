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


def SetupCommands(tree: app_commands.CommandTree, guild_id: int, client: discord.Client):
    utils=ClaudiaUtils(client, guild_id)

    @tree.command(
        name="test",
        description="Test the bot",
        guild=discord.Object(id=guild_id)
    )
    async def Test(ctx: discord.Interaction):
        if not await utils.CheckControlChannel(ctx):
            return
        await ctx.response.send_message(embed=discord.Embed(
            title="Success",
            description="I am still here!",
            color=discord.Color.green()
        ))

    @tree.command(
        name="add_to_controls",
        description="Add player to the controls channel",
        guild=discord.Object(id=guild_id)
    )
    async def AddToControls(ctx:discord.Interaction, player: discord.User):
        if not await utils.CheckControlChannel(ctx) or not await utils.CheckOwner(ctx):
            return
        await ctx.channel.set_permissions(player, view_channel=True)
        await ctx.response.send_message(f"{player.name} added!")
        return


    @tree.command(
        name="remove_from_controls",
        description="Remove a player from the controls channel",
        guild=discord.Object(id=guild_id)
    )
    async def RemoveFromControls(ctx:discord.Interaction, player: discord.User):
        if not await utils.CheckControlChannel(ctx) or not await utils.CheckOwner(ctx):
            return
        guild=utils.Guild()
        await ctx.channel.set_permissions(player, view_channel=False)
        await ctx.response.send_message(f"{player.name} removed!")
        return


    class ConfirmButton(Button):
        def __init__(self, traitors: set[discord.Member]):
            super().__init__(label="Click Me", style=discord.ButtonStyle.blurple)
            self.traitors_left=traitors
            self.lock=asyncio.Lock()

        async def callback(self, interaction: discord.Interaction):
            async with self.lock:
                if interaction.user not in self.traitors_left:
                    await interaction.response.defer()
                    return

                await interaction.response.send_message("Thanks for confirming!", ephemeral=True)
                self.traitors_left.discard(interaction.user)
                if len(self.traitors_left) == 0:
                    announcements_channel = await utils.AnnouncementsChannel()
                    await announcements_channel.send(
                        embed=discord.Embed(
                            title="The traitors have been selected",
                            description="Let the game begin.",
                            color=discord.Color.purple()
                        )
                    )
                    self.disabled=True
                    await interaction.message.edit(view=self.view)
            
    async def ConfirmTraitors(traitors :set[discord.Member]):
        view=View()
        view.add_item(ConfirmButton(traitors))
        instructions_channel = await utils.TraitorsInstructionsChannel()
        await instructions_channel.send("comfirm", view=view)


        
    async def InitializeImpl(output_channel: discord.TextChannel, caller: discord.Member, clear_traitors:bool=True):
        guild=utils.Guild()

        private_channel_permissions = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True),
        }

        # Create controls channel
        controls_channel = utils.ControlsChannel()
        if not controls_channel:
            await output_channel.send("Creating controls channel")
            controls_channel = await guild.create_text_channel(
                constants.kControlsChannelName,
                overwrites=private_channel_permissions
                )
        
        # Create read only announcements channel that only Claudia can send messages to 
        read_only = {
            guild.default_role: discord.PermissionOverwrite(send_messages=False),
            guild.me: discord.PermissionOverwrite(send_messages=True)
        }
        announcements_channel = await utils.AnnouncementsChannel(send_error=False)
        if not announcements_channel:
            await output_channel.send("Creating announcements channel")
            announcements_channel = await guild.create_text_channel(constants.kAnnouncementsChannelName,overwrites=read_only)
        
        # Create private instructions channel for only traitors (initially with just Claudia and the owner)
        traitors_instructions_channel = await utils.TraitorsInstructionsChannel(send_error=False)
        if not traitors_instructions_channel:
            await output_channel.send("Creating traitors-instructions channel")
            traitors_instructions_channel = await guild.create_text_channel(
                constants.kTraitorsInstructionsChannelName,
                overwrites=private_channel_permissions
                )

        traitors_chat_channel = await utils.TraitorsChatChannel(send_error=False)
        if not traitors_chat_channel:
            await output_channel.send("Creating traitors-chat channel")
            traitors_chat_channel = await guild.create_text_channel(
                constants.kTraitorsChatChannelName,
                overwrites=private_channel_permissions
                )
        if clear_traitors:
            await utils.ClearTraitors()
            
        
    @tree.command(
        name="initialize",
        description="Initialize traitors server",
        guild=discord.Object(id=guild_id)
    )
    async def Initialize(ctx:discord.Interaction, clear_traitors: bool=False):
        if clear_traitors and not await utils.CheckControlChannel(ctx):
            return False
        await ctx.response.send_message("Initializing for new game")
        await InitializeImpl(ctx.channel, ctx.user, clear_traitors)

    @tree.command(
        name="new_game",
        description="Start a new game",
        guild=discord.Object(id=guild_id)
    )
    async def NewGame(ctx:discord.Interaction, min_num_traitors: int = 2, probability_of_min: float = .8):
        if not await utils.CheckControlChannel(ctx):
            return False
        num_traitors = min_num_traitors if random.random() < probability_of_min else min_num_traitors + 1
        players = utils.GetPlayers()
        if len(players) < min_num_traitors + ( 0 if probability_of_min >= 1 else 1 ):
            await ctx.response.send_message(embed=utils.Error("Possible number of traitors higher than number of players"))
            return
        await ctx.response.send_message(f"Starting game with {num2words(min_num_traitors)} or {num2words(min_num_traitors + 1)} traitors...")

        await InitializeImpl(ctx.channel,ctx.user)

        traitors=random.sample(list(utils.GetPlayers()),num_traitors)
        for traitor in traitors:
            await utils.AddTraitor(traitor)
            await traitor.send(
                embed=discord.Embed(
                    title=f"Congratulations, you have been selected to be a traitor!",
                    description="The traitors private channels are now available for communication and instructions.",
                    color=discord.Color.purple()
                )
            )
        traitors_instructions= await utils.TraitorsInstructionsChannel()
        if not traitors_instructions:
            return
        if not await utils.CheckNumTraitors({min_num_traitors,min_num_traitors + 1}):
            return
        await ctx.channel.send(
            embed=discord.Embed(
                title="New game started successfully!",
                color=discord.Color.green()
            )
            )
        await ConfirmTraitors(await utils.GetTraitors())

    @tree.command(
        name="save_game",
        description="Save the traitors as an encoded string",
        guild=discord.Object(id=guild_id)
    )
    async def SaveGame(interaction:discord.Interaction):
        def encode(players: dict)->str:
            string=json.dumps(players)
            return base64.urlsafe_b64encode(string.encode()).decode()
   
        players={
            "faithful": { member.id: member.name for member in await utils.GetFaithful() },
            "traitor": { member.id: member.name for member in await utils.GetTraitors() }
        }

        saved_game = encode(players)

        description=(
            f"A game has been saved with the following players:"
            f"\n* {"\n* ".join([ player.name for player in utils.GetPlayers()])}.\n\n"
            "Copy the following text and paste into the `/load_game` command to load game."
        )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Game saved!",
                description=description + " A copy has been DM'd to you as well.",
                color=discord.Color.green()
                )
            )
        await interaction.channel.send(f"```{saved_game}```")
        await interaction.user.send(
            embed=discord.Embed(
                title="Game saved!",
                description=description,
                color=discord.Color.green()
                )
            )
        await interaction.user.send(f"```{saved_game}```")


    @tree.command(
        name="load_game",
        description="Load the traitors from an encoded string",
        guild=discord.Object(id=guild_id)
    )
    async def LoadGame(interaction:discord.Interaction, saved_game: str):
        if not await utils.CheckControlChannel(interaction):
            return
        await InitializeImpl(interaction.channel, interaction.user)

        async def decode(encoded_text)->dict[str, dict[int, str]]:
            """Decodes the encoded string back to a list of member IDs."""
            try:
               return json.loads(base64.urlsafe_b64decode(encoded_text.strip("`").encode()).decode())
            except (binascii.Error, UnicodeDecodeError)  as e:
                await interaction.response.send_message(embed=utils.Error("Unable to decode saved game. make sure you copied it correctly."))
                return None
                

        
        missing_players=set()
        old_players=set()
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
                    color=discord.Color.purple()
                    )
                )
            await utils.AddTraitor(traitor)
        for id, name in decoded_game["faithful"].items():
            faithful=guild.get_member(int(id))
            if not faithful:
                missing_players.add(name)
                continue
            old_players.add(faithful)
            await faithful.send(
                embed=discord.Embed(
                    title="A game has been loaded",
                    description="You are a **faithful**.",
                    color=discord.Color.purple()
                    )
                )
        current_players = utils.GetPlayers()
        print("\n\n\n")
        print(current_players)
        print(old_players)
        print("\n\n\n")

        new_players=current_players - old_players
        description=""
        if missing_players:
            description+=(
                "These players are no longer present in the server:"
                f"\n* {"\n* ".join(missing_players)}.\n\n"
                )
        if new_players:
            description+=(
                "These players in the sever were not previously present:"
                f"\n* {"\n* ".join({ player.name for player in new_players })}.\n\n"
                )
        description+="Have fun!"
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Game loaded!",
                description=description,
                color=discord.Color.green()
                )
            )


    @tree.command(
        name="check_traitors",
        description="Check that the number of traitors is as expected",
        guild=discord.Object(id=guild_id)
    )
    async def CheckTraitors(ctx:discord.Interaction, min_expected: int):
        if not await utils.CheckNumTraitors({min_expected, min_expected + 1}):
            await ctx.response.send_message("Traitor initialization unsuccessful!")
            return
        await ctx.response.send_message(
            embed=discord.Embed(
                title="Success!",
                description="The traitors have been initialized successfully.",
                color=discord.Color.green()
                )
            )
        return


    async def CheckPlayerCallback(interaction: discord.Interaction, view: View,  member: discord.Member, probability: float):
        check_player_resonse=None
        for item in view.children:
            if item.custom_id=="check_player":
                check_player_resonse=item
            
        check_player_resonse.disabled = True
        await interaction.message.edit(view=view)

        if check_player_resonse.values[0] == "no":
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{member.display_name} not added.",
                    color=discord.Color.red()
                    )
                )
            return

        if random.random() < probability:
            await utils.AddTraitor(member)

        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{member.display_name} added to game!",
                color=discord.Color.green()
                )
            )


    @tree.command(
        name="add_player",
        description="Add player to game, possibly making them a traitor",
        guild=discord.Object(id=guild_id)
    )
    # Default probablity is .22, as assuming 10 initial players, with 2-3 traitors and min probability
    # of .8, this gives the same probability for any new players.
    async def AddPlayer(ctx: discord.Interaction, member: discord.Member, probability: float = .22):
        if not await utils.CheckControlChannel(ctx):
            return
        # await ctx.response.send_message(f"Adding{member.display_name} to the game...")
        check_player = Select(
            custom_id="check_player",
            placeholder="Respond",
            options=[
                discord.SelectOption(label="yes", value="yes"),
                discord.SelectOption(label="no", value="no"),
                ]
            )
        view = View()
        view.add_item(check_player)
            
        await ctx.response.send_message(f"Confirm: Add {member.display_name} to the game with {probability} chance of being a traitor?", view=view)
        check_player.callback = lambda ctx: CheckPlayerCallback(ctx, view, member, probability)

        
    @tree.command(
        name="clear_all_traitors",
        description="Remove all traitors",
        guild=discord.Object(id=guild_id)
    )
    async def ClearAllTraitors(ctx:discord.Interaction):
        await utils.ClearTraitors()
        await ctx.response.send_message("All traitors removed.")