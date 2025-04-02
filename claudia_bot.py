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
import game_controls

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

    
# # Control Commands ---------------------------------------------------------------------------------------------------------------------------

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
        game_controls.GameControls(tree, guild_id, client)
        await tree.sync(guild=discord.Object(id=guild_id))
        print(f'Logged in as {client.user}: commands')

    client.run(bot_token)

if __name__ == "__main__":
    app.run(main)

