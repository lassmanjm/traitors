import discord
import constants
from discord import app_commands
from discord.ui import Select, View
import time
import asyncio
import math

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


# Traitor commands ---------------------------------------------------------------------------------------------------------------------------
@tree.command(
    name="murder",
    description="Select murder victim(s).",
    guild=discord.Object(id=constants.traitors_only_guild)
)
async def MurderCommand(interaction, victims: str):
    instructions_channel = client.get_channel(constants.instructions_channel_id)
    traitors_channel = client.get_channel(constants.traitors_channel_id)
    is_are="are" if ( "," in victims or " " in victims ) else "is"
    await interaction.response.send_message(f"You have made your selection. **{victims}** will no longer be with us.")
    await instructions_channel.send(embed=discord.Embed(title="A murder has been committed!", description=f"**{victims}** {is_are} dead.", color=discord.Color.red()) )
    # await instructions_channel.send(f"The traitors have struck again. **{victims}** {is_are} dead.")

@tree.command(
    name="recruit",
    description="Recruit a player to be a traitor",
    guild=discord.Object(id=constants.traitors_only_guild)
)
async def Recruit(ctx):
    main_guild = client.get_guild(constants.main_guild)
    traitors_only_guild = client.get_guild(constants.traitors_only_guild)
    # members = [member for member in main_guild.members]
    members = [member for member in main_guild.members if member not in traitors_only_guild.members]
    user_options = [discord.SelectOption(label=member.display_name, value=str(member.id)) for member in members]
    select = Select(placeholder="Select an option", options=user_options)
    view = View()
    view.add_item(select)
    
    await ctx.response.send_message("Select a player to recruit:", view=view)

    # Wait for the selection
    async def select_callback(interaction: discord.Interaction, view=view):
        select.disabled = True
        await interaction.message.edit(view=view)
        # Get the selected user
        user_id = int(select.values[0])  # The selected user ID
        selected_user = client.get_user(user_id)
        
        if selected_user:
            await interaction.response.send_message(f"Recruiting **{selected_user.display_name}**")
            await selected_user.send(embed=discord.Embed(
                title="You are being recruited",
                description="The traitors are making you an offer to join there ranks. Will you accept?",
                color=discord.Color.purple()
                ))
            response = Select(
                placeholder="Respond",
                options=[
                    discord.SelectOption(label="yes", value="yes"),
                    discord.SelectOption(label="no", value="no"),
                    ]
                )
            view = View()
            view.add_item(response)
            
            # Send the selection prompt to the caller in Server A
            await selected_user.send("Join the traitors?", view=view)
            async def response_callback(interaction: discord.Interaction):
                response.disabled = True
                await interaction.message.edit(view=view)
                accept =response.values[0] == "yes"
                traitors_channel = client.get_channel(constants.traitors_channel_id)

                if accept:
                    invite = await traitors_channel.create_invite(max_uses=1) 
                    await interaction.response.send_message(f"Join the server: {invite.url}")
                    await traitors_channel.send(embed=discord.Embed(
                        title=f"{selected_user.name} has accepted the offer.",
                        description="They will be joining you shortly",
                        color=discord.Color.green()
                    ))
                else:
                    await interaction.response.send_message(f"You have rejected the offer, and therefore remain faithful.")
                    await traitors_channel.send(embed=discord.Embed(
                        title=f"{selected_user.name} has rejected the offer. They remain faithful.",
                        color=discord.Color.red()
                    ))
            response.callback = response_callback
                    

        else:
            instructions_channel = client.get_channel(constants.instructions_channel_id)
            await instructions_channel.send(embed=discord.Embed(
                title="Recruitment Error! ",
                description="User not found",
                color=discord.Color.red()
                ))
    
    select.callback = select_callback


@tree.command(
    name="help",
    description="Ask anonymous questions to the group",
    guild=discord.Object(id=constants.traitors_only_guild)
)
async def help(interaction, problem: str):
    instructions_channel = client.get_channel(constants.instructions_channel_id)
    await interaction.response.send_message("Help requested!")
    await instructions_channel.send(embed=discord.Embed(title="Anonymous help requested!", description=problem, color=discord.Color.blue()) )
# \Traitor commands ---------------------------------------------------------------------------------------------------------------------------

# Control Commands ---------------------------------------------------------------------------------------------------------------------------
@tree.command(
    name="round_table",
    description="Initiate a round table",
    guild=discord.Object(id=constants.control_guild)
)
async def RoundTable(ctx, length: float=5.):
    length=math.floor(length*60)
    if length <= 0:
      await channel.send("The countdown must be longer than 0 seconds!")
      return

    channel = client.get_channel(constants.general_channel_id)
    await ctx.response.send_message(f"Starting round table for {length} seconds.")
    await channel.send("Players, welcome to the round table. This is your only oppurtunity to strike back at the traitors. You have five minutes. Good luck.")
    MinutesSeconds= lambda seconds: (seconds//60, seconds%60)

    minutes, seconds = MinutesSeconds(length)

    countdown_message = await channel.send(f"⏳ Time left: {minutes}:{seconds:02}")

    while length > 0:
        length -= 1
        minutes, seconds = MinutesSeconds(length)
        await countdown_message.edit(content=f"⏳ Time left: {minutes}:{seconds:02}")
        await asyncio.sleep(1)

    await countdown_message.edit(content="⏰ Time's up!")
    await channel.send("The time for talk is now over. ")

# Murder selections
async def victim_select_callback(interaction: discord.Interaction, view):
    victim_select=None
    for item in view.children:
        if item.custom_id=="victim_select":
            victim_select=item
    if not victim_select:
        await interaction.response.send_message(embed=discord.Embed(
            title="Failed to select victim.",
            description="Ask for help by using the `/help` command.",
            color=discord.Color.red()
            ))
        return 
        
    victim_select.disabled = True
    await interaction.message.edit(view=view)

    victims = victim_select.values  # The selected user ID
    await interaction.response.send_message(f"You have made your selection. **{', '.join(victims)}** will no longer be with us.")
    instructions_channel = client.get_channel(constants.instructions_channel_id)
    traitors_channel = client.get_channel(constants.traitors_channel_id)
    await instructions_channel.send(embed=discord.Embed(title="The traitors have struck again!", description=f"**{', '.join(victims)}** {"are" if len(victims)>1 else "is"} dead.", color=discord.Color.red()) )

@tree.command(
    name="murder_instructions",
    description="Send instructions to murder",
    guild=discord.Object(id=constants.control_guild)
)
async def MurderInstructions(ctx, num_victims:int = 1):
    traitors_channel = client.get_channel(constants.traitors_channel_id)

    main_guild = client.get_guild(constants.main_guild)
    traitors_only_guild = client.get_guild(constants.traitors_only_guild)
    # members = [member for member in main_guild.members if member not in traitors_only_guild.members]
    members =  main_guild.members
    user_options = [discord.SelectOption(label=member.display_name, value=member.display_name) for member in members]
    victim_select = Select(
        custom_id="victim_select",
        placeholder="Select an option",
        options=user_options,
        max_values=num_victims,
        min_values=num_victims
        )
    view = View()
    view.add_item(victim_select)
    await traitors_channel.send(
        embed=discord.Embed(
            title="Time to murder",
            description="Traitors, you now decide who lives and who dies. Choose carefully.\nDecide who to murder as a group, and make a selection.",
            color=discord.Color.purple()
            ),
        )
    await traitors_channel.send(f"Select {"a" if num_victims==1 else num_victims} player{"s" if num_victims > 1 else ""} to murder:", view=view)

    
    victim_select.callback = lambda ctx: victim_select_callback(ctx, view)
    await ctx.response.send_message("Murder instructions sent.")

@tree.command(
    name="rectruit_instructions",
    description="Send instructions to recruit",
    guild=discord.Object(id=constants.control_guild)
)
async def RecruitInstructions(ctx):
    await ctx.response.send_message("Recruit instructions sent.")
    traitors_channel = client.get_channel(constants.traitors_channel_id)
    await traitors_channel.send(embed=discord.Embed(
        title="You may recruit",
        description="Traitors, you have lost one of your own. You may now choose to recruit. If you decide to, invite the prospective traitor to this server.",
        color=discord.Color.dark_purple()
        ))

@tree.command(
    name="death_match_instructions",
    description="Send instructions to murder",
    guild=discord.Object(id=constants.control_guild)
)
async def RecruitInstructions(ctx):
    await ctx.response.send_message("Rectuit instructions sent.")
    traitors_channel = client.get_channel(constants.traitors_channel_id)
    # TODO do this~!!!!!
    await traitors_channel.send("Traitors, you know decide who lives and who dies. Choose carefully.")
    await traitors_channel.send("Decide who to murder as a group. To make a selection, execute the command by typing `/murder` and giving a name.")
    me=client.get_user("jawshwa3803")
    await me.send("hlllo")
# \Control Commands ---------------------------------------------------------------------------------------------------------------------------


# General Commands ---------------------------------------------------------------------------------------------------------------------------
@tree.command(
    name="dm_test",
    description="Test DM all players.",
    guild=discord.Object(id=constants.main_guild)
)
async def test(ctx):
    # Get the guild (server) the command was called from
    guild = ctx.guild
    failed=[]
    
    # Iterate through all members in the server
    for member in guild.members:
        try:
            # Skip sending DM to the bot itself
            if member == client.user:
                continue
            
            # Send DM to the member
            await member.send("Mic check. One, two")
        
        except discord.Forbidden:
            failed.append(member.name)
        except discord.HTTPException as e:
            failed.append(member.name)
            await ctx.channel.send(f"Failed to send DM to {member.name}: {e}")

    num_failed=len(failed)
    await ctx.response.send_message(
        embed=discord.Embed(
            title="DMs failed" if num_failed > 0 else "DMs successful",
            description=(f"Failed to send to {num_failed} users:\n{"\n".join([f"-{failure}" for failure in failed])}" if num_failed > 0 else ""),
            color=(discord.Color.red() if num_failed > 0 else discord.Color.green())
            )
        )

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=constants.traitors_only_guild))
    await tree.sync(guild=discord.Object(id=constants.control_guild))
    await tree.sync(guild=discord.Object(id=constants.main_guild))
    print(f'Logged in as {client.user}: commands')

client.run(constants.bot_token)

