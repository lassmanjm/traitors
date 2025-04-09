import discord
from discord import app_commands
import constants
from claudia_utils import ClaudiaUtils
from discord.ui import Select, View, Button
import asyncio
from num2words import num2words
import math


def GameControls(tree: app_commands.CommandTree, guild_id: int, client: discord.Client):
    utils = ClaudiaUtils(client, guild_id)

    @tree.command(
        name="anonymous",
        description="Communicate anonymously with the group",
        guild=discord.Object(id=guild_id),
    )
    async def anonymous(interaction: discord.Interaction, message: str):
        announcements_channel = await utils.AnnouncementsChannel()
        await interaction.response.send_message("Message sent", ephemeral=True)
        await announcements_channel.send(
            embed=discord.Embed(
                title="Anonymous message",
                description=message,
                color=discord.Color.pink(),
            )
        )

    # ----------------------------------------[ Murder ]----------------------------------------
    async def Kill(victims: list[discord.User]):
        announcements_channel = await utils.AnnouncementsChannel()
        await announcements_channel.send(
            embed=discord.Embed(
                title="The traitors have struck!",
                description=(
                    f"**{utils.DisplayPlayers([victim.display_name for victim in victims])}** "
                    f"{"are" if len(victims)>1 else "is"} dead."
                ),
                color=discord.Color.red(),
            )
        )

    # Murder selections
    async def victim_select_callback(interaction: discord.Interaction, view: View):
        victim_select = None
        for item in view.children:
            if item.custom_id == "victim_select":
                victim_select = item
        if not victim_select:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Failed to select victim.",
                    description="Ask for help by using the `/help` command.",
                    color=discord.Color.red(),
                )
            )
            return

        victim_select.disabled = True
        await interaction.message.edit(view=view)

        victims = [client.get_user(int(victim)) for victim in victim_select.values]
        await interaction.response.send_message(
            (
                f"You have made your selection. **{utils.DisplayPlayers([victim.display_name for victim in victims])}** "
                "will no longer be with us."
            )
        )
        await Kill(victims)

    @tree.command(
        name="murder",
        description="Send instructions to murder",
        guild=discord.Object(id=guild_id),
    )
    async def Murder(ctx: discord.Interaction, num_victims: int = 1):
        traitors_channel = await utils.TraitorsInstructionsChannel()
        user_options = [
            discord.SelectOption(label=member.display_name, value=member.id)
            for member in await utils.GetFaithful()
        ]
        victim_select = Select(
            custom_id="victim_select",
            placeholder="Select an option",
            options=user_options,
            max_values=num_victims,
            min_values=num_victims,
        )
        view = View()
        view.add_item(victim_select)
        await traitors_channel.send(
            embed=discord.Embed(
                title="Time to murder",
                description="Traitors, you now decide who lives and who dies. Choose carefully.\nDecide who to murder as a group, and make a selection.",
                color=discord.Color.purple(),
            ),
        )
        await traitors_channel.send(
            f"Select {"a" if num_victims==1 else num_victims} player{"s" if num_victims > 1 else ""} to murder:",
            view=view,
        )

        victim_select.callback = lambda ctx: victim_select_callback(ctx, view)
        await ctx.response.send_message("Murder initiated.")

    # ----------------------------------------[ Recruit ]----------------------------------------
    async def RecruitComplete():
        control_channel = utils.ControlsChannel()
        await control_channel.send(
            embed=discord.Embed(
                title="Recruitment Complete",
                description="The traitors have finished recruiting.",
                color=discord.Color.green(),
            )
        )

    async def RecruitResponseCallback(
        interaction: discord.Interaction, view, selected_user: discord.User, force: bool
    ):
        recruit_response = None
        for item in view.children:
            if item.custom_id == "recruit_response":
                recruit_response = item

        recruit_response.disabled = True
        await interaction.message.edit(view=view)

        accept = recruit_response.values[0] == "yes"
        traitors_channel = await utils.TraitorsInstructionsChannel()

        if accept:
            await utils.AddTraitor(selected_user)
            await traitors_channel.send(
                embed=discord.Embed(
                    title=f"{selected_user.display_name} has accepted the offer.",
                    description="They have now joined your ranks.",
                    color=discord.Color.green(),
                )
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"🔪 Welcome to the ranks of the traitors",
                    description="You can now access the traitors instructions and chat channels.",
                    color=discord.Color.purple(),
                )
            )
            traitors_chat_channel = await utils.TraitorsChatChannel()
            await traitors_chat_channel.send(
                embed=discord.Embed(
                    title=f"Welcome, {selected_user.display_name}",
                    color=discord.Color.green(),
                )
            )
        else:
            if force:
                await interaction.response.send_message(
                    f"You have rejected the offer, and therefore will die. Hope it was worth it."
                )
                await traitors_channel.send(
                    embed=discord.Embed(
                        title=f"{selected_user.display_name} has rejected the offer. They will now be murdered.",
                        color=discord.Color.red(),
                    )
                )
                await Kill([selected_user])

            else:
                await interaction.response.send_message(
                    f"You have rejected the offer, and therefore remain faithful."
                )
                await traitors_channel.send(
                    embed=discord.Embed(
                        title=f"{selected_user.display_name} has rejected the offer. They remain faithful.",
                        color=discord.Color.red(),
                    )
                )
        await RecruitComplete()

    async def RecruitSelectCallback(
        interaction: discord.Interaction, view, force: bool
    ):
        recruit_select = None
        for item in view.children:
            if item.custom_id == "recruit_select":
                recruit_select = item
        if not recruit_select:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Failed to select recruit.",
                    description="Ask for help by using the `/help` command.",
                    color=discord.Color.red(),
                )
            )
            return

        recruit_select.disabled = True
        await interaction.message.edit(view=view)

        selected_recruit = client.get_user(
            int(recruit_select.values[0])
        )  # The selected user ID

        if selected_recruit:
            await interaction.response.send_message(
                f"You have made your selection. **{selected_recruit.display_name}** will be asked to join your ranks."
            )
            if force:
                await selected_recruit.send(
                    embed=discord.Embed(
                        title="You are being recruited",
                        description="The traitors are making you an offer: Join or die. If you reject, you will be murdered and removed from the game. Do you accept?",
                        color=discord.Color.purple(),
                    )
                )
            else:
                await selected_recruit.send(
                    embed=discord.Embed(
                        title="You are being recruited",
                        description="The traitors are making you an offer to join there ranks. If you reject, you will remain a faithful. Will you accept?",
                        color=discord.Color.purple(),
                    )
                )
            recruit_response = Select(
                custom_id="recruit_response",
                placeholder="Respond",
                options=[
                    discord.SelectOption(label="yes", value="yes"),
                    discord.SelectOption(label="no", value="no"),
                ],
            )
            view = View()
            view.add_item(recruit_response)

            await selected_recruit.send("Join the traitors?", view=view)
            recruit_response.callback = lambda ctx: RecruitResponseCallback(
                ctx, view, selected_recruit, force
            )

        else:
            traitors_channel = await utils.TraitorsInstructionsChannel()
            await traitors_channel.send(
                embed=discord.Embed(
                    title="Recruitment Error! ",
                    description="User not found. Ask for help with the `/help` command.",
                    color=discord.Color.red(),
                )
            )

    async def InitiateRecruit(force: bool = False):
        traitors_channel = await utils.TraitorsInstructionsChannel()
        user_options = [
            discord.SelectOption(label=member.display_name, value=member.id)
            for member in await utils.GetFaithful()
        ]
        recruit_select = Select(
            custom_id="recruit_select",
            placeholder="Select an option",
            options=user_options,
        )
        view = View()
        view.add_item(recruit_select)
        await traitors_channel.send(
            f"Select a player to recruit to be a traitor:", view=view
        )

        recruit_select.callback = lambda ctx: RecruitSelectCallback(ctx, view, force)

    async def RecruitDecideCallback(interaction: discord.Interaction, view):
        recruit_decide = None
        for item in view.children:
            if item.custom_id == "recruit_decide":
                recruit_decide = item
        if not recruit_decide:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Selection failed",
                    description="Ask for help by using the `/help` command.",
                    color=discord.Color.red(),
                )
            )
            return

        recruit_decide.disabled = True
        await interaction.message.edit(view=view)

        decision = recruit_decide.values[0]
        if decision == "yes":
            await interaction.response.send_message(f"Excellent.")
            await InitiateRecruit()
        else:
            await interaction.response.send_message(
                f"You have rejected the opportunity to recruit. Your numbers will not change."
            )
            await asyncio.sleep(10)
            await RecruitComplete()

    @tree.command(
        name="recruit",
        description="Send instructions to recruit",
        guild=discord.Object(id=guild_id),
    )
    async def Recruit(ctx: discord.Interaction, force: bool = False):
        traitors_channel = await utils.TraitorsInstructionsChannel()
        if force:
            await traitors_channel.send(
                embed=discord.Embed(
                    title="You must now recruit.",
                    description="Traitors, you may now add to your ranks. Choose carefully.",
                    color=discord.Color.purple(),
                ),
            )
            await InitiateRecruit(force=True)
            await ctx.response.send_message("Recruit initiated.")
            return
        # TODO: change var name
        user_options = [
            discord.SelectOption(label="yes", value="yes"),
            discord.SelectOption(label="no", value="no"),
        ]
        recruit_select = Select(
            custom_id="recruit_decide",
            placeholder="Select an option",
            options=user_options,
        )
        view = View()
        view.add_item(recruit_select)
        await traitors_channel.send(
            embed=discord.Embed(
                title="You may now recruit.",
                description="Traitors, you may now add to your ranks, if you so choose.",
                color=discord.Color.purple(),
            ),
        )
        await traitors_channel.send(f"Would you like to recruit?", view=view)

        recruit_select.callback = lambda ctx: RecruitDecideCallback(ctx, view)
        await ctx.response.send_message("Recruit initiated.")

    # ----------------------------------------[ Deathmatch ]----------------------------------------
    async def DeathmatchVictimSelectCallback(
        interaction: discord.Interaction, view, num_players: int, num_victims: int
    ):
        deathmatch_victim_select = None
        for item in view.children:
            if item.custom_id == "deathmatch_victim_select":
                deathmatch_victim_select = item
        if not deathmatch_victim_select:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Failed to select deathmatch victim.",
                    description="Ask for help by using the `/help` command.",
                    color=discord.Color.red(),
                )
            )
            return

        deathmatch_victim_select.disabled = True
        await interaction.message.edit(view=view)

        deathmatch_victims = [
            client.get_user(int(victim)).display_name
            for victim in deathmatch_victim_select.values
        ]
        victims_string = utils.DisplayPlayers(deathmatch_victims)
        await interaction.response.send_message(
            f"You have made your selection. **{victims_string}** will be sent to the deathmatch."
        )
        announcements_channel = await utils.AnnouncementsChannel()
        await announcements_channel.send(
            embed=discord.Embed(
                title="The traitors have thought of a new way to torture you",
                description=f"**{victims_string}** have been selected for a Death Match. Only {num2words(num_players - num_victims)} will survive.",
                color=discord.Color.red(),
            )
        )

    @tree.command(
        name="deathmatch",
        description="Send instructions for deathmatch",
        guild=discord.Object(id=guild_id),
    )
    async def DeathMatch(
        ctx: discord.Interaction, num_players: int = 4, num_victims: int = 1
    ):
        traitors_channel = await utils.TraitorsInstructionsChannel()
        players = utils.GetPlayers()
        if num_players > len(players):
            await ctx.response.send_message(
                embed=utils.Error(
                    "Too many players selected. Cannot be more "
                    f"than the number of players in the game ({len(players)})."
                )
            )
            return
        if num_victims > num_players - 1:
            await ctx.response.send_message(
                embed=utils.Error(
                    "Too many victims selected; there must be at least one survivor. "
                    f"Select no more than {num_players-1}."
                )
            )
            return

        user_options = [
            discord.SelectOption(label=member.display_name, value=member.id)
            for member in utils.GetPlayers()
        ]
        deathmatch_victim_select = Select(
            custom_id="deathmatch_victim_select",
            placeholder="Select an option",
            options=user_options,
            max_values=num_players,
            min_values=num_players,
        )
        view = View()
        view.add_item(deathmatch_victim_select)
        await traitors_channel.send(
            embed=discord.Embed(
                title="It is time for the Death Match",
                description=f"Traitors, you now have a unique opportunity and may send any {num_players} players to a Death Match, including at most {num_players-num_victims} of yourselves. {num2words(num_players).capitalize()} will walk in, but only {num2words(num_players-num_victims)} will walk out.",
                color=discord.Color.purple(),
            ),
        )
        await traitors_channel.send(
            f"Select {num_players} players to send to the Death Match:", view=view
        )

        deathmatch_victim_select.callback = lambda ctx: DeathmatchVictimSelectCallback(
            ctx, view, num_players, num_victims
        )
        await ctx.response.send_message("Death Match initiated")

    # ----------------------------------------[ Round Table ]----------------------------------------
    def CountdownMessage(sec_left: int, length_sec: int) -> discord.Embed:
        minutes, seconds = (length_sec // 60, length_sec % 60)
        length_string = f"{f"{minutes} minute{"s" if minutes > 1 else ""}" if minutes > 0 else ""}{" and " if minutes > 0 and seconds > 0 else ""}{f"{seconds} second{"s" if seconds > 1 else ""}" if seconds > 0 else ""}"

        minutes, seconds = (sec_left // 60, sec_left % 60)
        if sec_left == 0:
            return discord.Embed(
                title="Round Table",
                description=f"Players, welcome to the round table. This is your only oppurtunity to strike back at the traitors. You have {length_string}. Good luck.\n⏰ Time's up!",
                color=discord.Color.red(),
            )

        return discord.Embed(
            title="Round Table",
            description=f"Players, welcome to the round table. This is your only oppurtunity to strike back at the traitors. You have {length_string}. Good luck.\n⏳ Time left: {minutes}:{seconds:02}",
            color=discord.Color.purple(),
        )

    @tree.command(
        name="round_table",
        description="Initiate a round table",
        guild=discord.Object(id=guild_id),
    )
    async def RoundTable(ctx: discord.Interaction, length_min: float = 5.0):
        if not await utils.CheckControlChannel(ctx):
            return
        length_sec = math.floor(length_min * 60)
        if length_sec <= 0:
            await ctx.response.send_message(
                embed=utils.Error("The countdown must be longer than 0 seconds!")
            )
            return

        channel = await utils.AnnouncementsChannel()

        await ctx.response.send_message(
            f"Starting round table for {length_sec} seconds"
        )

        sec_left = length_sec
        countdown_message = await channel.send(
            embed=CountdownMessage(sec_left, length_sec)
        )

        while sec_left > 0:
            sec_left -= 1
            await countdown_message.edit(embed=CountdownMessage(sec_left, length_sec))
            await asyncio.sleep(1)

        await channel.send("The time for talk is now over. ")
