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

# bot_token=os.environ['TRAITORS_BOT_TOKEN']
# guild_id=int(os.environ['TRAITORS_GUILD_ID'])

intents = discord.Intents.default()
intents.members = True
intents.guilds = True 
intents.guild_messages = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

    
# Setup --------------------------------------------------------------------------------------------------------------------------------------

# Traitor commands ---------------------------------------------------------------------------------------------------------------------------

# @tree.command(
#     name="help",
#     description="Ask anonymous questions to the group",
# )
# async def help(interaction:discord.Interaction, problem: str):
#     announcements_channel = await utils.AnnouncementsChannel()
#     await interaction.response.send_message("Help requested!", ephemeral=True)
#     await announcements_channel.send(embed=discord.Embed(title="Anonymous help requested!", description=problem, color=discord.Color.pink()) )

# @tree.command(
#     name="anonymous",
#     description="Communicate anonymously with the group",
#     guild=discord.Object(id=guild_id)
# )
# async def help(interaction:discord.Interaction, message: str):
#     instructions_channel = client.get_channel(utils.instructions_channel_id)
#     await interaction.response.send_message("Message sent", ephemeral=True)
#     await instructions_channel.send(embed=discord.Embed(title="Anonymous communication", description=message, color=discord.Color.dark_purple()) )
# # \Traitor commands ---------------------------------------------------------------------------------------------------------------------------

# # Control Commands ---------------------------------------------------------------------------------------------------------------------------
# @tree.command(
#     name="test",
#     description="Test the bot",
#     guild=discord.Object(id=guild_id)
# )
# async def Test(ctx: discord.Interaction, length: float=5.):
#     await ctx.response.send_message(embed=discord.Embed(
#         title="Success",
#         description="I am still here!",
#         color=discord.Color.green()
#     ))

# @tree.command(
#     name="pick_traitors",
#     description="Pick traitors",
#     guild=discord.Object(id=guild_id)
# )
# async def PickTraitors(ctx: discord.Interaction, min:int = 2, min_probabilty:float=.8):
#     num_traitors=min if random.random() < min_probabilty else min + 1
#     main_guild = client.get_guild(main_guild_id)
#     members = [member for member in main_guild.members if member.id not in {bot_user_id, admin_user_id}]
#     traitors=random.sample(members,num_traitors)
#     await ctx.response.send_message(embed=discord.Embed(
#         title="Traitors selected",
#         description=f"{num2words(min).capitalize()} or {num2words(min + 1)} Traitors selected",
#         color=discord.Color.green()
#     ))
#     traitors_channel = client.get_channel(traitors_channel_id)
#     for traitor in traitors:
#         invite = await traitors_channel.create_invite(max_uses=1) 
#         await traitor.send(embed=discord.Embed(
#             title=f"Congratulations, you have been selected to be a traitor!",
#             color=discord.Color.purple()
#         ))
#         await traitor.send(f"🔪 Join the server: {invite.url}")

# @tree.command(
#     name="check_traitors_old",
#     description="Check that the right number of traitors are in the traitors guild.",
#     guild=discord.Object(id=guild_id)
# )
# async def CheckTraitors(ctx: discord.Interaction, min:int = 2):
#     traitors_guild = client.get_guild(traitors_only_guild_id)
#     num_members = len([member for member in traitors_guild.members if member.id not in {bot_user_id, admin_user_id}])
#     if num_members == min or num_members == (min + 1):
#         await ctx.response.send_message(embed=discord.Embed(
#             title="There are the right number of traitors",
#             color=discord.Color.green()
#         ))
#     else:
#         await ctx.response.send_message(embed=discord.Embed(
#             title="There are not the right number of traitors",
#             color=discord.Color.red()
#         ))

# def CountdownMessage(sec_left: int, length_sec:int) -> discord.Embed:
#     minutes, seconds = (length_sec//60, length_sec%60)
#     length_string=f"{f"{minutes} minute{"s" if minutes > 1 else ""}" if minutes > 0 else ""}{" and " if minutes > 0 and seconds > 0 else ""}{f"{seconds} second{"s" if seconds > 1 else ""}" if seconds > 0 else ""}"

#     minutes, seconds = (sec_left//60, sec_left%60)
#     if sec_left == 0:
#         return discord.Embed(
#             title="Round Table",
#             description=f"Players, welcome to the round table. This is your only oppurtunity to strike back at the traitors. You have {length_string}. Good luck.\n⏰ Time's up!",
#             color=discord.Color.red()
#         )

#     return discord.Embed(
#         title="Round Table",
#         description=f"Players, welcome to the round table. This is your only oppurtunity to strike back at the traitors. You have {length_string}. Good luck.\n⏳ Time left: {minutes}:{seconds:02}",
#         color=discord.Color.purple()
#     )
    
# @tree.command(
#     name="round_table",
#     description="Initiate a round table",
#     guild=discord.Object(id=guild_id)
# )
# async def RoundTable(ctx, length_min: float=5.):
#     length_sec=math.floor(length_min*60)
#     if length_sec <= 0:
#       await channel.send("The countdown must be longer than 0 seconds!")
#       return

#     channel = client.get_channel(instructions_channel_id)
#     await ctx.response.send_message(f"Starting round table for {length_sec} seconds")
    
#     sec_left=length_sec
#     countdown_message=await channel.send(embed=CountdownMessage(sec_left, length_sec))

#     while sec_left > 0:
#         sec_left -= 1
#         await countdown_message.edit(embed=CountdownMessage(sec_left, length_sec))
#         await asyncio.sleep(1)

#     await channel.send("The time for talk is now over. ")


# async def Kill(victims):
#     instructions_channel = client.get_channel(instructions_channel_id)
#     await instructions_channel.send(embed=discord.Embed(title="The traitors have struck again!", description=f"**{DisplayVictims([victim.display_name for victim in victims])}** {"are" if len(victims)>1 else "is"} dead.", color=discord.Color.red()) )
# # Murder selections
# async def victim_select_callback(interaction: discord.Interaction, view):
#     victim_select=None
#     for item in view.children:
#         if item.custom_id=="victim_select":
#             victim_select=item
#     if not victim_select:
#         await interaction.response.send_message(embed=discord.Embed(
#             title="Failed to select victim.",
#             description="Ask for help by using the `/help` command.",
#             color=discord.Color.red()
#             ))
#         return 
        
#     victim_select.disabled = True
#     await interaction.message.edit(view=view)

#     victims = [client.get_user(int(victim)) for victim in victim_select.values]
#     await interaction.response.send_message(f"You have made your selection. **{DisplayVictims([victim.display_name for victim in victims])}** will no longer be with us.")
#     await Kill(victims)

# @tree.command(
#     name="murder",
#     description="Send instructions to murder",
#     guild=discord.Object(id=guild_id)
# )
# async def Murder(ctx, num_victims:int = 1):
#     traitors_channel = client.get_channel(traitors_channel_id)

#     main_guild = client.get_guild(main_guild_id)
#     traitors_only_guild = client.get_guild(traitors_only_guild_id)
#     members = [member for member in main_guild.members if member not in traitors_only_guild.members]
#     user_options = [discord.SelectOption(label=member.display_name, value=member.id) for member in members]
#     victim_select = Select(
#         custom_id="victim_select",
#         placeholder="Select an option",
#         options=user_options,
#         max_values=num_victims,
#         min_values=num_victims
#         )
#     view = View()
#     view.add_item(victim_select)
#     await traitors_channel.send(
#         embed=discord.Embed(
#             title="Time to murder",
#             description="Traitors, you now decide who lives and who dies. Choose carefully.\nDecide who to murder as a group, and make a selection.",
#             color=discord.Color.purple()
#             ),
#         )
#     await traitors_channel.send(f"Select {"a" if num_victims==1 else num_victims} player{"s" if num_victims > 1 else ""} to murder:", view=view)

    
#     victim_select.callback = lambda ctx: victim_select_callback(ctx, view)
#     await ctx.response.send_message("Murder initiated.")

# async def RecruitComplete():
#     await client.get_channel(control_channel_id).send(embed=discord.Embed(
#         title="Recruitment Complete",
#         description="The traitors have finished recruiting.",
#         color=discord.Color.green()
#     ))
    

# async def RecruitResponseCallback(interaction: discord.Interaction, view, selected_user, force:bool):
#     recruit_response=None
#     for item in view.children:
#         if item.custom_id=="recruit_response":
#             recruit_response=item
        
#     recruit_response.disabled = True
#     await interaction.message.edit(view=view)

#     accept = recruit_response.values[0] == "yes"
#     traitors_channel = client.get_channel(traitors_channel_id)

#     if accept:
#         invite = await traitors_channel.create_invite(max_uses=1) 
#         await interaction.response.send_message(f"Join the server: {invite.url}")
#         await traitors_channel.send(embed=discord.Embed(
#             title=f"{selected_user.display_name} has accepted the offer.",
#             description="They will be joining you shortly",
#             color=discord.Color.green()
#         ))
#     else:
#         if force:
#             await interaction.response.send_message(f"You have rejected the offer, and therefore will die. Hope it was worth it.")
#             await traitors_channel.send(embed=discord.Embed(
#                 title=f"{selected_user.display_name} has rejected the offer. They will now be murdered.",
#                 color=discord.Color.red()
#             ))
#             await Kill([selected_user])

#         else:
#             await interaction.response.send_message(f"You have rejected the offer, and therefore remain faithful.")
#             await traitors_channel.send(embed=discord.Embed(
#                 title=f"{selected_user.display_name} has rejected the offer. They remain faithful.",
#                 color=discord.Color.red()
#             ))
#     await RecruitComplete()


    
# async def RecruitSelectCallback(interaction: discord.Interaction, view, force:bool):
#     recruit_select=None
#     for item in view.children:
#         if item.custom_id=="recruit_select":
#             recruit_select=item
#     if not recruit_select:
#         await interaction.response.send_message(embed=discord.Embed(
#             title="Failed to select recruit.",
#             description="Ask for help by using the `/help` command.",
#             color=discord.Color.red()
#             ))
#         return 
        
#     recruit_select.disabled = True
#     await interaction.message.edit(view=view)

#     selected_recruit = client.get_user(int(recruit_select.values[0]))  # The selected user ID
        
#     if selected_recruit:
#         await interaction.response.send_message(f"You have made your selection. **{selected_recruit.display_name}** will be asked to join your ranks.")
#         # await interaction.response.send_message(f"Recruiting **{recruit.display_name}**")
#         if force:
#             await selected_recruit.send(embed=discord.Embed(
#                 title="You are being recruited",
#                 description="The traitors are making you an offer: Join or die. If you reject, you will be murdered and removed from the game. Do you accept?",
#                 color=discord.Color.purple()
#                 ))
#         else:
#             await selected_recruit.send(embed=discord.Embed(
#                 title="You are being recruited",
#                 description="The traitors are making you an offer to join there ranks. If you reject, you will remain a faithful. Will you accept?",
#                 color=discord.Color.purple()
#                 ))
#         recruit_response = Select(
#             custom_id="recruit_response",
#             placeholder="Respond",
#             options=[
#                 discord.SelectOption(label="yes", value="yes"),
#                 discord.SelectOption(label="no", value="no"),
#                 ]
#             )
#         view = View()
#         view.add_item(recruit_response)
        
#         await selected_recruit.send("Join the traitors?", view=view)
#         recruit_response.callback = lambda ctx: RecruitResponseCallback(ctx, view, selected_recruit, force)

#     else:
#         traitors_channel = client.get_channel(traitors_channel_id)
#         await traitors_channel.send(embed=discord.Embed(
#             title="Recruitment Error! ",
#             description="User not found. Ask for help with the `/help` command.",
#             color=discord.Color.red()
#             ))
    


# async def InitiateRecruit(force:bool=False):
#     traitors_channel=client.get_channel(traitors_channel_id)

#     main_guild = client.get_guild(main_guild_id)
#     traitors_only_guild = client.get_guild(traitors_only_guild_id)
#     members = [member for member in main_guild.members if member not in traitors_only_guild.members]
#     user_options = [discord.SelectOption(label=member.display_name, value=member.id) for member in members]
#     recruit_select = Select(
#         custom_id="recruit_select",
#         placeholder="Select an option",
#         options=user_options,
#         )
#     view = View()
#     view.add_item(recruit_select)
#     await traitors_channel.send(f"Select a player to recruit to be a traitor:", view=view)

    
#     recruit_select.callback = lambda ctx: RecruitSelectCallback(ctx, view, force)

# async def RecruitDecideCallback(interaction: discord.Interaction, view):
#     recruit_decide=None
#     for item in view.children:
#         if item.custom_id=="recruit_decide":
#             recruit_decide=item
#     if not recruit_decide:
#         await interaction.response.send_message(embed=discord.Embed(
#             title="Selection failed",
#             description="Ask for help by using the `/help` command.",
#             color=discord.Color.red()
#             ))
#         return 
        
#     recruit_decide.disabled = True
#     await interaction.message.edit(view=view)

#     decision = recruit_decide.values[0]  # The selected user ID
#     if decision == "yes":
#         await interaction.response.send_message(f"Excellent.")
#         await InitiateRecruit()
#     else:
#         await interaction.response.send_message(f"You have rejected the opportunity to recruit. Your numbers will not change. Await further instructions.")
#         await asyncio.sleep(10)
#         await RecruitComplete()
    

# @tree.command(
#     name="recruit",
#     description="Send instructions to recruit",
#     guild=discord.Object(id=guild_id)
# )
# async def Recruit(ctx, force:bool = False):
#     traitors_channel = client.get_channel(traitors_channel_id)
#     if force:
#         await traitors_channel.send(
#             embed=discord.Embed(
#                 title="You must now recruit.",
#                 description="Traitors, you may now add to your ranks. Choose carefully.",
#                 color=discord.Color.purple()
#                 ),
#             )
#         await InitiateRecruit(force=True)
#         await ctx.response.send_message("Recruit initiated.")
#         return
#     user_options = [
#         discord.SelectOption(label="yes", value="yes"),
#         discord.SelectOption(label="no", value="no")
#         ]
#     recruit_select = Select(
#         custom_id="recruit_decide",
#         placeholder="Select an option",
#         options=user_options,
#         )
#     view = View()
#     view.add_item(recruit_select)
#     await traitors_channel.send(
#         embed=discord.Embed(
#             title="You may now recruit.",
#             description="Traitors, you may now add to your ranks, if you so choose.",
#             color=discord.Color.purple()
#             ),
#         )
#     await traitors_channel.send(f"Would you like to recruit?", view=view)

    
#     recruit_select.callback = lambda ctx: RecruitDecideCallback(ctx, view)
#     await ctx.response.send_message("Recruit initiated.")
    
# # Murder selections
# async def DeathmatchVictimSelectCallback(interaction: discord.Interaction, view, num_players:int, num_victims:int):
#     deathmatch_victim_select=None
#     for item in view.children:
#         if item.custom_id=="deathmatch_victim_select":
#             deathmatch_victim_select=item
#     if not deathmatch_victim_select:
#         await interaction.response.send_message(embed=discord.Embed(
#             title="Failed to select deathmatch victim.",
#             description="Ask for help by using the `/help` command.",
#             color=discord.Color.red()
#             ))
#         return 
        
#     deathmatch_victim_select.disabled = True
#     await interaction.message.edit(view=view)

#     deathmatch_victims = [client.get_user(int(victim)).display_name for victim in deathmatch_victim_select.values]
#     victims_string=DisplayVictims(deathmatch_victims)
#     await interaction.response.send_message(f"You have made your selection. **{victims_string}** will be sent to the deathmatch.")
#     instructions_channel = client.get_channel(instructions_channel_id)
#     traitors_channel = client.get_channel(traitors_channel_id)
#     await instructions_channel.send(embed=discord.Embed(
#         title="The traitors have thought of a new way to torture you",
#         description=f"**{victims_string}** have been selected for a Death Match. Only {num2words(num_players - num_victims)} will survive.",
#         color=discord.Color.red()
#         ))

# @tree.command(
#     name="deathmatch",
#     description="Send instructions for deathmatch",
#     guild=discord.Object(id=guild_id)
# )
# async def DeathMatch(ctx, num_players:int = 4, num_victims:int = 1):
#     traitors_channel = client.get_channel(traitors_channel_id)

#     main_guild = client.get_guild(main_guild_id)
#     members = main_guild.members
#     user_options = [ discord.SelectOption(label=member.display_name, value=member.id) 
#                     for member in main_guild.members 
#                     if member.id not in {admin_user_id, bot_user_id}]
#     deathmatch_victim_select = Select(
#         custom_id="deathmatch_victim_select",
#         placeholder="Select an option",
#         options=user_options,
#         max_values=num_players,
#         min_values=num_players
#         )
#     view = View()
#     view.add_item(deathmatch_victim_select)
#     await traitors_channel.send(
#         embed=discord.Embed(
#             title="It is time for the Death Match",
#             description=f"Traitors, you now have a unique opportunity and may send any {num_players} players to a Death Match, including at most {num_players-num_victims} of yourselves. {num2words(num_players).capitalize()} will walk in, but only {num2words(num_players-num_victims)} will walk out.",
#             color=discord.Color.purple()
#             ),
#         )
#     await traitors_channel.send(f"Select {num_players} players to send to the Death Match:", view=view)

    
#     deathmatch_victim_select.callback = lambda ctx: DeathmatchVictimSelectCallback(ctx, view, num_players, num_victims)
#     await ctx.response.send_message("Death Match initiated")

# @tree.command(
#     name="delete_messsages",
#     description="Delete messages in channel",
# )
# async def DeleteMessages(ctx, limit:int=None):
#     if limit is None:
#         await ctx.response.send_message("You must provide the number of messages to delete")
#     else:
#         await ctx.response.send_message(f"Deleting {limit} messages...", delete_after=2)  # Auto-delete the confirmation message
#         await asyncio.sleep(3)
#         await ctx.channel.purge(limit=limit)

# # \Control Commands ---------------------------------------------------------------------------------------------------------------------------


# # General Commands ---------------------------------------------------------------------------------------------------------------------------
# @tree.command(
#     name="dm_test",
#     description="Test DM all players.",
#     guild=discord.Object(id=guild_id)
# )
# async def DmTest(ctx):
#     # Get the guild (server) the command was called from
#     guild = ctx.guild
#     failed=[]
    
#     # Iterate through all members in the server
#     for member in guild.members:
#         try:
#             # Skip sending DM to the bot itself
#             if member == client.user:
#                 continue
            
#             # Send DM to the member
#             await member.send("Mic check. One, two")
        
#         except discord.Forbidden:
#             failed.append(member.name)
#         except discord.HTTPException as e:
#             failed.append(member.name)
#             await ctx.channel.send(f"Failed to send DM to {member.name}: {e}")

#     num_failed=len(failed)
#     await ctx.response.send_message(
#         embed=discord.Embed(
#             title="DMs failed" if num_failed > 0 else "DMs successful",
#             description=(f"Failed to send to {num_failed} users:\n{"\n".join([f"-{failure}" for failure in failed])}" if num_failed > 0 else ""),
#             color=(discord.Color.red() if num_failed > 0 else discord.Color.green())
#             )
#         )

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
        await tree.sync(guild=discord.Object(id=guild_id))
        print(f'Logged in as {client.user}: commands')

    client.run(bot_token)

if __name__ == "__main__":
    app.run(main)

