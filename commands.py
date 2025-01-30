import discord
import constants
from discord import app_commands
from discord.ui import Select, View
import time
import asyncio
import math

intents = discord.Intents.default()
intents.members = True
intents.guilds = True 
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def DisplayVictims(victims: list[str]):
    if len(victims) == 1:
        return victims[0]
    if len(victims) ==2:
        return " and ".join(victims)
    out=victims.copy()
    out[-1]=f"and {out[-1]}"
    return ', '.join(out)

# Traitor commands ---------------------------------------------------------------------------------------------------------------------------

@tree.command(
    name="help",
    description="Ask anonymous questions to the group",
    guild=discord.Object(id=constants.traitors_only_guild)
)
async def help(interaction, problem: str):
    instructions_channel = client.get_channel(constants.instructions_channel_id)
    await interaction.response.send_message("Help requested!")
    await instructions_channel.send(embed=discord.Embed(title="Anonymous help requested!", description=problem, color=discord.Color.pink()) )

@tree.command(
    name="anonymous",
    description="Communicate anonymously with the group",
    guild=discord.Object(id=constants.traitors_only_guild)
)
async def help(interaction, message: str):
    instructions_channel = client.get_channel(constants.instructions_channel_id)
    await interaction.response.send_message("Message sent")
    await instructions_channel.send(embed=discord.Embed(title="Anonymous communication", description=message, color=discord.Color.dark_purple()) )
# \Traitor commands ---------------------------------------------------------------------------------------------------------------------------

# Control Commands ---------------------------------------------------------------------------------------------------------------------------
@tree.command(
    name="test",
    description="Test the bot",
    guild=discord.Object(id=constants.control_guild)
)
async def Test(ctx: discord.Interaction, length: float=5.):
    await ctx.response.send_message(embed=discord.Embed(
        title="Test succesful",
        description="I am still here!",
        color=discord.Color.green()
    ))

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

    channel = client.get_channel(constants.instructions_channel_id)
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


async def murder(victims):
    instructions_channel = client.get_channel(constants.instructions_channel_id)
    await instructions_channel.send(embed=discord.Embed(title="The traitors have struck again!", description=f"**{DisplayVictims([victim.display_name for victim in victims])}** {"are" if len(victims)>1 else "is"} dead.", color=discord.Color.red()) )
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

    victims = [client.get_user(int(victim)) for victim in victim_select.values]
    await interaction.response.send_message(f"You have made your selection. **{DisplayVictims([victim.display_name for victim in victims])}** will no longer be with us.")
    await murder(victims)

@tree.command(
    name="murder_instructions",
    description="Send instructions to murder",
    guild=discord.Object(id=constants.control_guild)
)
async def MurderInstructions(ctx, num_victims:int = 1):
    traitors_channel = client.get_channel(constants.traitors_channel_id)

    main_guild = client.get_guild(constants.main_guild)
    traitors_only_guild = client.get_guild(constants.traitors_only_guild)
    members = [member for member in main_guild.members if member not in traitors_only_guild.members]
    user_options = [discord.SelectOption(label=member.display_name, value=member.id) for member in members]
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

async def RecruitComplete():
    await client.get_channel(constants.control_channel_id).send(embed=discord.Embed(
        title="Recruitment Complete",
        description="The traitors have finished recruiting.",
        color=discord.Color.green()
    ))
    

async def recruit_response_callback(interaction: discord.Interaction, view, selected_user, force:bool):
    recruit_response=None
    for item in view.children:
        if item.custom_id=="recruit_response":
            recruit_response=item
        
    recruit_response.disabled = True
    await interaction.message.edit(view=view)

    accept = recruit_response.values[0] == "yes"
    traitors_channel = client.get_channel(constants.traitors_channel_id)

    if accept:
        invite = await traitors_channel.create_invite(max_uses=1) 
        await interaction.response.send_message(f"Join the server: {invite.url}")
        await traitors_channel.send(embed=discord.Embed(
            title=f"{selected_user.display_name} has accepted the offer.",
            description="They will be joining you shortly",
            color=discord.Color.green()
        ))
    else:
        if force:
            await interaction.response.send_message(f"You have rejected the offer, and therefore will die. Hope it was worth it.")
            await traitors_channel.send(embed=discord.Embed(
                title=f"{selected_user.display_name} has rejected the offer. They will now be murdered.",
                color=discord.Color.red()
            ))
            await murder([selected_user])

        else:
            await interaction.response.send_message(f"You have rejected the offer, and therefore remain faithful.")
            await traitors_channel.send(embed=discord.Embed(
                title=f"{selected_user.display_name} has rejected the offer. They remain faithful.",
                color=discord.Color.red()
            ))
    await RecruitComplete()


    
async def recruit_select_callback(interaction: discord.Interaction, view, force:bool):
    recruit_select=None
    for item in view.children:
        if item.custom_id=="recruit_select":
            recruit_select=item
    if not recruit_select:
        await interaction.response.send_message(embed=discord.Embed(
            title="Failed to select recruit.",
            description="Ask for help by using the `/help` command.",
            color=discord.Color.red()
            ))
        return 
        
    recruit_select.disabled = True
    await interaction.message.edit(view=view)

    selected_recruit = client.get_user(int(recruit_select.values[0]))  # The selected user ID
        
    if selected_recruit:
        await interaction.response.send_message(f"You have made your selection. **{selected_recruit.display_name}** will be asked to join your ranks.")
        # await interaction.response.send_message(f"Recruiting **{recruit.display_name}**")
        if force:
            await selected_recruit.send(embed=discord.Embed(
                title="You are being recruited",
                description="The traitors are making you an offer: Join or die. If you reject, you will be murdered and removed from the game. Do you accept?",
                color=discord.Color.purple()
                ))
        else:
            await selected_recruit.send(embed=discord.Embed(
                title="You are being recruited",
                description="The traitors are making you an offer to join there ranks. If you reject, you will remain a faithful. Will you accept?",
                color=discord.Color.purple()
                ))
        recruit_response = Select(
            custom_id="recruit_response",
            placeholder="Respond",
            options=[
                discord.SelectOption(label="yes", value="yes"),
                discord.SelectOption(label="no", value="no"),
                ]
            )
        view = View()
        view.add_item(recruit_response)
        
        await selected_recruit.send("Join the traitors?", view=view)
        recruit_response.callback = lambda ctx: recruit_response_callback(ctx, view, selected_recruit, force)

    else:
        traitors_channel = client.get_channel(constants.traitors_channel_id)
        await traitors_channel.send(embed=discord.Embed(
            title="Recruitment Error! ",
            description="User not found. Ask for help with the `/help` command.",
            color=discord.Color.red()
            ))
    


async def recruit(force:bool=False):
    traitors_channel=client.get_channel(constants.traitors_channel_id)

    main_guild = client.get_guild(constants.main_guild)
    traitors_only_guild = client.get_guild(constants.traitors_only_guild)
    members = [member for member in main_guild.members if member not in traitors_only_guild.members]
    user_options = [discord.SelectOption(label=member.display_name, value=member.id) for member in members]
    recruit_select = Select(
        custom_id="recruit_select",
        placeholder="Select an option",
        options=user_options,
        )
    view = View()
    view.add_item(recruit_select)
    await traitors_channel.send(f"Select a player to recruit to be a traitor:", view=view)

    
    recruit_select.callback = lambda ctx: recruit_select_callback(ctx, view, force)

async def recruit_decide_callback(interaction: discord.Interaction, view):
    recruit_decide=None
    for item in view.children:
        if item.custom_id=="recruit_decide":
            recruit_decide=item
    if not recruit_decide:
        await interaction.response.send_message(embed=discord.Embed(
            title="Selection failed",
            description="Ask for help by using the `/help` command.",
            color=discord.Color.red()
            ))
        return 
        
    recruit_decide.disabled = True
    await interaction.message.edit(view=view)

    decision = recruit_decide.values[0]  # The selected user ID
    if decision == "yes":
        await interaction.response.send_message(f"Excellent.")
        await recruit()
    else:
        await interaction.response.send_message(f"You have rejected the opportunity to recruit. Your numbers will not change. Await further instructions.")
        await asyncio.sleep(10)
        await RecruitComplete()
    

@tree.command(
    name="rectruit_instructions",
    description="Send instructions to recruit",
    guild=discord.Object(id=constants.control_guild)
)
async def RecruitInstructions(ctx, force:bool = False):
    if force:
        await recruit(force=True)
        await ctx.response.send_message("Recruit instructions sent.")
        return
    traitors_channel = client.get_channel(constants.traitors_channel_id)
    user_options = [
        discord.SelectOption(label="yes", value="yes"),
        discord.SelectOption(label="no", value="no")
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
            color=discord.Color.purple()
            ),
        )
    await traitors_channel.send(f"Would you like to recruit?", view=view)

    
    recruit_select.callback = lambda ctx: recruit_decide_callback(ctx, view)
    await ctx.response.send_message("Recruit instructions sent.")
    
# Murder selections
async def deathmatch_victim_select_callback(interaction: discord.Interaction, view):
    deathmatch_victim_select=None
    for item in view.children:
        if item.custom_id=="deathmatch_victim_select":
            deathmatch_victim_select=item
    if not deathmatch_victim_select:
        await interaction.response.send_message(embed=discord.Embed(
            title="Failed to select deathmatch victim.",
            description="Ask for help by using the `/help` command.",
            color=discord.Color.red()
            ))
        return 
        
    deathmatch_victim_select.disabled = True
    await interaction.message.edit(view=view)

    deathmatch_victims = [client.get_user(int(victim)).display_name for victim in deathmatch_victim_select.values]
    victims_string=DisplayVictims(deathmatch_victims)
    await interaction.response.send_message(f"You have made your selection. **{victims_string}** will be sent to the deathmatch.")
    instructions_channel = client.get_channel(constants.instructions_channel_id)
    traitors_channel = client.get_channel(constants.traitors_channel_id)
    await instructions_channel.send(embed=discord.Embed(
        title="The traitors have struck again!",
        description=f"**{victims_string}** have been sent to the Death Match.",
        color=discord.Color.red()
        ))

@tree.command(
    name="deathmatch_instructions",
    description="Send instructions for deathmatch",
    guild=discord.Object(id=constants.control_guild)
)
async def DeathmatchInstructions(ctx, num_victims:int = 4):
    traitors_channel = client.get_channel(constants.traitors_channel_id)

    main_guild = client.get_guild(constants.main_guild)
    members = main_guild.members
    user_options = [ discord.SelectOption(label=member.display_name, value=member.id) 
                    for member in main_guild.members 
                    if member.id not in {1333590716005351435, 1333193323506172097}]
    deathmatch_victim_select = Select(
        custom_id="deathmatch_victim_select",
        placeholder="Select an option",
        options=user_options,
        max_values=num_victims,
        min_values=num_victims
        )
    view = View()
    view.add_item(deathmatch_victim_select)
    await traitors_channel.send(
        embed=discord.Embed(
            title="It is time for the Death Match",
            description="Traitors, you now have a unique opportunity and may send any 4 players to a Death Match, including at most 3 of yourselves. Four will walk in, but only three will walk out.",
            color=discord.Color.purple()
            ),
        )
    await traitors_channel.send(f"Select 4 players to send to the Death Match:", view=view)

    
    deathmatch_victim_select.callback = lambda ctx: deathmatch_victim_select_callback(ctx, view)
    await ctx.response.send_message("Death Match instructions sent.")

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

