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

FLAGS = flags.FLAGS
flags.DEFINE_string(
    "bot_token",
    os.environ.get('TRAITORS_BOT_TOKEN'),
    "",
)


bot_token=os.environ['TRAITORS_BOT_TOKEN']
# bot_user_id=int(os.environ['TRAITORS_BOT_USER_ID'])
# admin_user_id=int(os.environ.get('TRAITORS_ADMIN_USER_ID', ""))

# instructions_channel_id=int(os.environ['TRAITORS_INSTRUCTIONS_CHANNEL_ID'])
# traitors_channel_id=int(os.environ['TRAITORS_TRAITORS_CHANNEL_ID'])
# control_channel_id=int(os.environ['TRAITORS_CONTROL_CHANNEL_ID'])

# main_guild_id=int(os.environ['TRAITORS_MAIN_GUILD_ID'])
# traitors_only_guild_id=int(os.environ['TRAITORS_TRAITORS_ONLY_GUILD_ID'])
# control_guild_id=int(os.environ['TRAITORS_CONTROL_GUILD_ID'])

guild_id=int(os.environ['TRAITORS_GUILD_ID'])

kAnnouncementsChannelName="announcements"
kControlsChannelName="controls"
kTraitorsInstructionsChannelName="traitors-instructions"
kTraitorsChatChannelName="traitors-chat"



intents = discord.Intents.default()
intents.members = True
intents.guilds = True 
intents.guild_messages = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def Guild() -> discord.Guild | None:
    return client.get_guild(guild_id)


async def AnnouncementsChannel(send_error:bool = True)->discord.TextChannel | None:
    guild=Guild()
    channel = discord.utils.get(guild.text_channels, name=kAnnouncementsChannelName)
    if not channel and send_error:
        await SendError(ChannelNotFoundError(kAnnouncementsChannelName))
    return channel
        

async def TraitorsInstructionsChannel(send_error:bool = True)->discord.TextChannel | None:
    guild=Guild()
    channel = discord.utils.get(guild.text_channels, name=kTraitorsInstructionsChannelName)
    if not channel and send_error:
        await SendError(ChannelNotFoundError(kTraitorsInstructionsChannelName))
    return channel


async def TraitorsChatChannel(send_error:bool = True)->discord.TextChannel | None:
    guild=Guild()
    channel = discord.utils.get(guild.text_channels, name=kTraitorsChatChannelName)
    if not channel and send_error:
        await SendError(ChannelNotFoundError(kTraitorsChatChannelName))
    return channel


def ControlsChannel()->discord.TextChannel | None:
    guild=Guild()
    return discord.utils.get(guild.text_channels, name=kControlsChannelName)


def DisplayVictims(victims: list[str]):
    if len(victims) == 1:
        return victims[0]
    if len(victims) ==2:
        return " and ".join(victims)
    out=victims.copy()
    out[-1]=f"and {out[-1]}"
    return ', '.join(out)


def Error(description:str) -> discord.Embed:
    return discord.Embed(
        title="ERROR", 
        description=description,
        color=discord.Color.red()
        )

    
def ChannelNotFoundError(channel_name: str) -> discord.Embed:
    return Error(f"Channel `{channel_name}` not found.")


async def SendError(error: discord.Embed):
    guild=Guild()
    controls_channel=ControlsChannel()
    if controls_channel:
        await controls_channel.send(embed=error)
    else: 
        await guild.owner.send(embed=ChannelNotFoundError(kControlsChannelName))
        await guild.owner.send(embed=error)
    

async def CheckControlChannel(ctx: discord.Interaction) -> bool:
    if ctx.channel.name == kControlsChannelName:
        return True
    await ctx.response.send_message(
        embed=Error("Must execture this command from control channel!"),
        ephemeral=True
        )
    return False


async def CheckOwner(ctx: discord.Interaction) -> bool:
    if ctx.user == ctx.guild.owner:
        return True
    await ctx.response.send_message(
        embed=Error("Command must be executed by owner of guild!"),
        ephemeral=True
        )
    return False
async def AddTraitor(member: discord.Member) -> bool:
    for channel in [await TraitorsInstructionsChannel(), await TraitorsChatChannel()]:
        if not channel:
            return False
        # Grant permission to the user to view the channel
        await channel.set_permissions(member, view_channel=True)
        

async def ClearTraitors():
    guild=Guild()
    for channel in [await TraitorsInstructionsChannel(), await TraitorsChatChannel()]:
        for user_or_role in channel.overwrites.keys():
            # Skip the bot and server owner
            if user_or_role != guild.me and user_or_role != guild.owner:
                await channel.set_permissions(
                    user_or_role,
                    overwrite=discord.PermissionOverwrite(view_channel=False)
                    ) 


async def CheckNumTraitors(valid_nums:set[int]) -> bool:   
    guild=Guild()
    instructions_channel = await TraitorsInstructionsChannel()
    chat_channel = await TraitorsChatChannel()
    if not instructions_channel:
        return False
    if not chat_channel:
        return False
    num_instructions_members = 0
    num_chat_members = 0
    for player in GetPlayers():
        if instructions_channel.permissions_for(player).view_channel:
            num_instructions_members += 1
        if chat_channel.permissions_for(player).view_channel:
            num_chat_members += 1
    if num_instructions_members not in valid_nums or num_chat_members not in valid_nums:
        await SendError(Error("Incorrect number of traitors!"))
        return False
    return True


def IsPlayer(user: discord.Member) -> bool: 
    guild=Guild()
    if user in {guild.me, guild.owner}:
        return False
    return True


def GetPlayers() -> set[discord.Member]:
    guild=Guild()
    players=set()
    for member in guild.members:
        if IsPlayer(member):
            players.add(member)
    return players


async def IsTraitor(user: discord.Member) -> bool:
    if not IsPlayer(user):
        return False
    traitors_channel = await TraitorsInstructionsChannel()
    if traitors_channel.overwrites[user].view_channel:
        return True
    return False


async def GetTraitors()->set[discord.Member]:
    return {player for player in GetPlayers() if await IsTraitor(player)}


async def GetFaithful()->set[discord.Member]:
    return {player for player in GetPlayers() if not await IsTraitor(player)}
    
    
# Setup --------------------------------------------------------------------------------------------------------------------------------------
@tree.command(
    name="add_to_controls",
    description="Add player to controls channel",
    guild=discord.Object(id=guild_id)
)
async def AddToControls(ctx:discord.Interaction, player: discord.User):
    if not await CheckControlChannel(ctx) or not await CheckOwner(ctx):
        return
    await ctx.channel.set_permissions(player, view_channel=True)
    await ctx.response.send_message(f"{player.name} added!")
    return


@tree.command(
    name="remove_from_controls",
    description="Add player to controls channel",
    guild=discord.Object(id=guild_id)
)
async def RemoveFromControls(ctx:discord.Interaction, player: discord.User):
    if not await CheckControlChannel(ctx) or not await CheckOwner(ctx):
        return
    guild=Guild()
    await ctx.channel.set_permissions(player, view_channel=False)
    await ctx.response.send_message(f"{player.name} removed!")
    return


class ConfirmButton(Button):
    def __init__(self, traitors: set[discord.Member]):
        super().__init__(label="Click Me", style=discord.ButtonStyle.primary)
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
                announcements_channel = await AnnouncementsChannel()
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
    instructions_channel = await TraitorsInstructionsChannel()
    await instructions_channel.send("comfirm", view=view)


    
async def InitializeImpl(output_channel: discord.TextChannel, caller: discord.Member, clear_traitors:bool=True):
    guild=Guild()

    private_channel_permissions = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(view_channel=True),
    }

    # Create controls channel
    controls_channel = ControlsChannel()
    if not controls_channel:
        await output_channel.send("Creating controls channel")
        controls_channel = await guild.create_text_channel(
            kControlsChannelName,
            overwrites=private_channel_permissions
            )
    
    # Create read only announcements channel that only Claudia can send messages to 
    read_only = {
        guild.default_role: discord.PermissionOverwrite(send_messages=False),
        guild.me: discord.PermissionOverwrite(send_messages=True)
    }
    announcements_channel = await AnnouncementsChannel(send_error=False)
    if not announcements_channel:
        await output_channel.send("Creating announcements channel")
        announcements_channel = await guild.create_text_channel(kAnnouncementsChannelName,overwrites=read_only)
    
    # Create private instructions channel for only traitors (initially with just Claudia and the owner)
    traitors_instructions_channel = await TraitorsInstructionsChannel(send_error=False)
    if not traitors_instructions_channel:
        await output_channel.send("Creating traitors-instructions channel")
        traitors_instructions_channel = await guild.create_text_channel(
            kTraitorsInstructionsChannelName,
            overwrites=private_channel_permissions
            )

    traitors_chat_channel = await TraitorsChatChannel(send_error=False)
    if not traitors_chat_channel:
        await output_channel.send("Creating traitors-chat channel")
        traitors_chat_channel = await guild.create_text_channel(
            kTraitorsChatChannelName,
            overwrites=private_channel_permissions
            )
    if clear_traitors:
        await ClearTraitors()
        
    
@tree.command(
    name="initialize",
    description="Initialize traitors server",
    guild=discord.Object(id=guild_id)
)
async def Initialize(ctx:discord.Interaction, clear_traitors: bool=False):
    if not await CheckControlChannel(ctx):
        return False
    await ctx.response.send_message("Initializing for new game")
    await InitializeImpl(ctx.channel, ctx.user)

@tree.command(
    name="new_game",
    description="Start a new game",
    guild=discord.Object(id=guild_id)
)
async def NewGame(ctx:discord.Interaction, min_num_traitors: int = 2, probability_of_min: float = .8):
    if not await CheckControlChannel(ctx):
        return False
    await ctx.response.send_message(f"Starting game with {num2words(min_num_traitors)} or {num2words(min_num_traitors + 1)} traitors...")
    await InitializeImpl(ctx.channel,ctx.user)

    num_traitors = min_num_traitors if random.random() < probability_of_min else min_num_traitors + 1
    traitors=random.sample(list(GetPlayers()),num_traitors)
    for traitor in traitors:
        await AddTraitor(traitor)
        await traitor.send(
            embed=discord.Embed(
                title=f"Congratulations, you have been selected to be a traitor!",
                description="The traitors private channels are now available for communication and instructions.",
                color=discord.Color.purple()
            )
        )
    traitors_instructions= await TraitorsInstructionsChannel()
    if not traitors_instructions:
        return
    if not await CheckNumTraitors({min_num_traitors,min_num_traitors + 1}):
        return
    await ctx.channel.send(
        embed=discord.Embed(
            title="New game started successfully!",
            color=discord.Color.green()
        )
        )
    await ConfirmTraitors(await GetTraitors())


@tree.command(
    name="check_traitors",
    description="Check that the number of traitors is as expected",
    guild=discord.Object(id=guild_id)
)
async def CheckTraitors(ctx:discord.Interaction, min_expected: int):
    if not await CheckNumTraitors({min_expected, min_expected + 1}):
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
        await AddTraitor(member)

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
    if not await CheckControlChannel(ctx):
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
    await ClearTraitors()
    await ctx.response.send_message("All traitors removed.")

# Traitor commands ---------------------------------------------------------------------------------------------------------------------------

@tree.command(
    name="help",
    description="Ask anonymous questions to the group",
)
async def help(interaction:discord.Interaction, problem: str):
    announcements_channel = await AnnouncementsChannel()
    await interaction.response.send_message("Help requested!", ephemeral=True)
    await announcements_channel.send(embed=discord.Embed(title="Anonymous help requested!", description=problem, color=discord.Color.pink()) )

@tree.command(
    name="anonymous",
    description="Communicate anonymously with the group",
    guild=discord.Object(id=guild_id)
)
async def help(interaction:discord.Interaction, message: str):
    instructions_channel = client.get_channel(instructions_channel_id)
    await interaction.response.send_message("Message sent", ephemeral=True)
    await instructions_channel.send(embed=discord.Embed(title="Anonymous communication", description=message, color=discord.Color.dark_purple()) )
# \Traitor commands ---------------------------------------------------------------------------------------------------------------------------

# Control Commands ---------------------------------------------------------------------------------------------------------------------------
@tree.command(
    name="test",
    description="Test the bot",
    guild=discord.Object(id=guild_id)
)
async def Test(ctx: discord.Interaction, length: float=5.):
    await ctx.response.send_message(embed=discord.Embed(
        title="Success",
        description="I am still here!",
        color=discord.Color.green()
    ))

@tree.command(
    name="pick_traitors",
    description="Pick traitors",
    guild=discord.Object(id=guild_id)
)
async def PickTraitors(ctx: discord.Interaction, min:int = 2, min_probabilty:float=.8):
    num_traitors=min if random.random() < min_probabilty else min + 1
    main_guild = client.get_guild(main_guild_id)
    members = [member for member in main_guild.members if member.id not in {bot_user_id, admin_user_id}]
    traitors=random.sample(members,num_traitors)
    await ctx.response.send_message(embed=discord.Embed(
        title="Traitors selected",
        description=f"{num2words(min).capitalize()} or {num2words(min + 1)} Traitors selected",
        color=discord.Color.green()
    ))
    traitors_channel = client.get_channel(traitors_channel_id)
    for traitor in traitors:
        invite = await traitors_channel.create_invite(max_uses=1) 
        await traitor.send(embed=discord.Embed(
            title=f"Congratulations, you have been selected to be a traitor!",
            color=discord.Color.purple()
        ))
        await traitor.send(f"🔪 Join the server: {invite.url}")

@tree.command(
    name="check_traitors_old",
    description="Check that the right number of traitors are in the traitors guild.",
    guild=discord.Object(id=guild_id)
)
async def CheckTraitors(ctx: discord.Interaction, min:int = 2):
    traitors_guild = client.get_guild(traitors_only_guild_id)
    num_members = len([member for member in traitors_guild.members if member.id not in {bot_user_id, admin_user_id}])
    if num_members == min or num_members == (min + 1):
        await ctx.response.send_message(embed=discord.Embed(
            title="There are the right number of traitors",
            color=discord.Color.green()
        ))
    else:
        await ctx.response.send_message(embed=discord.Embed(
            title="There are not the right number of traitors",
            color=discord.Color.red()
        ))

def CountdownMessage(sec_left: int, length_sec:int) -> discord.Embed:
    minutes, seconds = (length_sec//60, length_sec%60)
    length_string=f"{f"{minutes} minute{"s" if minutes > 1 else ""}" if minutes > 0 else ""}{" and " if minutes > 0 and seconds > 0 else ""}{f"{seconds} second{"s" if seconds > 1 else ""}" if seconds > 0 else ""}"

    minutes, seconds = (sec_left//60, sec_left%60)
    if sec_left == 0:
        return discord.Embed(
            title="Round Table",
            description=f"Players, welcome to the round table. This is your only oppurtunity to strike back at the traitors. You have {length_string}. Good luck.\n⏰ Time's up!",
            color=discord.Color.red()
        )

    return discord.Embed(
        title="Round Table",
        description=f"Players, welcome to the round table. This is your only oppurtunity to strike back at the traitors. You have {length_string}. Good luck.\n⏳ Time left: {minutes}:{seconds:02}",
        color=discord.Color.purple()
    )
    
@tree.command(
    name="round_table",
    description="Initiate a round table",
    guild=discord.Object(id=guild_id)
)
async def RoundTable(ctx, length_min: float=5.):
    length_sec=math.floor(length_min*60)
    if length_sec <= 0:
      await channel.send("The countdown must be longer than 0 seconds!")
      return

    channel = client.get_channel(instructions_channel_id)
    await ctx.response.send_message(f"Starting round table for {length_sec} seconds")
    
    sec_left=length_sec
    countdown_message=await channel.send(embed=CountdownMessage(sec_left, length_sec))

    while sec_left > 0:
        sec_left -= 1
        await countdown_message.edit(embed=CountdownMessage(sec_left, length_sec))
        await asyncio.sleep(1)

    await channel.send("The time for talk is now over. ")


async def Kill(victims):
    instructions_channel = client.get_channel(instructions_channel_id)
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
    await Kill(victims)

@tree.command(
    name="murder",
    description="Send instructions to murder",
    guild=discord.Object(id=guild_id)
)
async def Murder(ctx, num_victims:int = 1):
    traitors_channel = client.get_channel(traitors_channel_id)

    main_guild = client.get_guild(main_guild_id)
    traitors_only_guild = client.get_guild(traitors_only_guild_id)
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
    await ctx.response.send_message("Murder initiated.")

async def RecruitComplete():
    await client.get_channel(control_channel_id).send(embed=discord.Embed(
        title="Recruitment Complete",
        description="The traitors have finished recruiting.",
        color=discord.Color.green()
    ))
    

async def RecruitResponseCallback(interaction: discord.Interaction, view, selected_user, force:bool):
    recruit_response=None
    for item in view.children:
        if item.custom_id=="recruit_response":
            recruit_response=item
        
    recruit_response.disabled = True
    await interaction.message.edit(view=view)

    accept = recruit_response.values[0] == "yes"
    traitors_channel = client.get_channel(traitors_channel_id)

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
            await Kill([selected_user])

        else:
            await interaction.response.send_message(f"You have rejected the offer, and therefore remain faithful.")
            await traitors_channel.send(embed=discord.Embed(
                title=f"{selected_user.display_name} has rejected the offer. They remain faithful.",
                color=discord.Color.red()
            ))
    await RecruitComplete()


    
async def RecruitSelectCallback(interaction: discord.Interaction, view, force:bool):
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
        recruit_response.callback = lambda ctx: RecruitResponseCallback(ctx, view, selected_recruit, force)

    else:
        traitors_channel = client.get_channel(traitors_channel_id)
        await traitors_channel.send(embed=discord.Embed(
            title="Recruitment Error! ",
            description="User not found. Ask for help with the `/help` command.",
            color=discord.Color.red()
            ))
    


async def InitiateRecruit(force:bool=False):
    traitors_channel=client.get_channel(traitors_channel_id)

    main_guild = client.get_guild(main_guild_id)
    traitors_only_guild = client.get_guild(traitors_only_guild_id)
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

    
    recruit_select.callback = lambda ctx: RecruitSelectCallback(ctx, view, force)

async def RecruitDecideCallback(interaction: discord.Interaction, view):
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
        await InitiateRecruit()
    else:
        await interaction.response.send_message(f"You have rejected the opportunity to recruit. Your numbers will not change. Await further instructions.")
        await asyncio.sleep(10)
        await RecruitComplete()
    

@tree.command(
    name="recruit",
    description="Send instructions to recruit",
    guild=discord.Object(id=guild_id)
)
async def Recruit(ctx, force:bool = False):
    traitors_channel = client.get_channel(traitors_channel_id)
    if force:
        await traitors_channel.send(
            embed=discord.Embed(
                title="You must now recruit.",
                description="Traitors, you may now add to your ranks. Choose carefully.",
                color=discord.Color.purple()
                ),
            )
        await InitiateRecruit(force=True)
        await ctx.response.send_message("Recruit initiated.")
        return
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

    
    recruit_select.callback = lambda ctx: RecruitDecideCallback(ctx, view)
    await ctx.response.send_message("Recruit initiated.")
    
# Murder selections
async def DeathmatchVictimSelectCallback(interaction: discord.Interaction, view, num_players:int, num_victims:int):
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
    instructions_channel = client.get_channel(instructions_channel_id)
    traitors_channel = client.get_channel(traitors_channel_id)
    await instructions_channel.send(embed=discord.Embed(
        title="The traitors have thought of a new way to torture you",
        description=f"**{victims_string}** have been selected for a Death Match. Only {num2words(num_players - num_victims)} will survive.",
        color=discord.Color.red()
        ))

@tree.command(
    name="deathmatch",
    description="Send instructions for deathmatch",
    guild=discord.Object(id=guild_id)
)
async def DeathMatch(ctx, num_players:int = 4, num_victims:int = 1):
    traitors_channel = client.get_channel(traitors_channel_id)

    main_guild = client.get_guild(main_guild_id)
    members = main_guild.members
    user_options = [ discord.SelectOption(label=member.display_name, value=member.id) 
                    for member in main_guild.members 
                    if member.id not in {admin_user_id, bot_user_id}]
    deathmatch_victim_select = Select(
        custom_id="deathmatch_victim_select",
        placeholder="Select an option",
        options=user_options,
        max_values=num_players,
        min_values=num_players
        )
    view = View()
    view.add_item(deathmatch_victim_select)
    await traitors_channel.send(
        embed=discord.Embed(
            title="It is time for the Death Match",
            description=f"Traitors, you now have a unique opportunity and may send any {num_players} players to a Death Match, including at most {num_players-num_victims} of yourselves. {num2words(num_players).capitalize()} will walk in, but only {num2words(num_players-num_victims)} will walk out.",
            color=discord.Color.purple()
            ),
        )
    await traitors_channel.send(f"Select {num_players} players to send to the Death Match:", view=view)

    
    deathmatch_victim_select.callback = lambda ctx: DeathmatchVictimSelectCallback(ctx, view, num_players, num_victims)
    await ctx.response.send_message("Death Match initiated")

@tree.command(
    name="delete_messsages",
    description="Delete messages in channel",
)
async def DeleteMessages(ctx, limit:int=None):
    if limit is None:
        await ctx.response.send_message("You must provide the number of messages to delete")
    else:
        await ctx.response.send_message(f"Deleting {limit} messages...", delete_after=2)  # Auto-delete the confirmation message
        await asyncio.sleep(3)
        await ctx.channel.purge(limit=limit)

# \Control Commands ---------------------------------------------------------------------------------------------------------------------------


# General Commands ---------------------------------------------------------------------------------------------------------------------------
@tree.command(
    name="dm_test",
    description="Test DM all players.",
    guild=discord.Object(id=guild_id)
)
async def DmTest(ctx):
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
    # ---------------------------------------------------
    import test_command 
    test_command.SetupCommands(tree, guild_id)
    # ---------------------------------------------------
    await tree.sync()
    await tree.sync(guild=discord.Object(id=guild_id))
    # await tree.sync(guild=discord.Object(id=main_guild_id))
    # await tree.sync(guild=discord.Object(id=control_guild_id))
    # await tree.sync(guild=discord.Object(id=traitors_only_guild_id))
    print(f'Logged in as {client.user}: commands')

client.run(bot_token)

