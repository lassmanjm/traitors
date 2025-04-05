import discord
import constants

class ClaudiaUtils:
  def __init__(self, client: discord.Client, guild_id: int):
    self.client=client
    self.guild_id=guild_id
    self.guild=None

  def Guild(self) -> discord.Guild | None:
    return self.client.get_guild(self.guild_id)


  async def AnnouncementsChannel(self, send_error:bool = True)->discord.TextChannel | None:
    guild=self.Guild()
    channel = discord.utils.get(guild.text_channels, name=constants.kAnnouncementsChannelName)
    if not channel and send_error:
        await self.SendError(self.ChannelNotFoundError(constants.kAnnouncementsChannelName))
    return channel
          

  async def TraitorsInstructionsChannel(self, send_error:bool = True)->discord.TextChannel | None:
    guild=self.Guild()
    channel = discord.utils.get(guild.text_channels, name=constants.kTraitorsInstructionsChannelName)
    if not channel and send_error:
        await self.SendError(self.ChannelNotFoundError(constants.kTraitorsInstructionsChannelName))
    return channel


  async def TraitorsChatChannel(self, send_error:bool = True)->discord.TextChannel | None:
    guild=self.Guild()
    channel = discord.utils.get(guild.text_channels, name=constants.kTraitorsChatChannelName)
    if not channel and send_error:
        await self.SendError(self.ChannelNotFoundError(constants.kTraitorsChatChannelName))
    return channel


  def ControlsChannel(self)->discord.TextChannel | None:
    guild=self.Guild()
    return discord.utils.get(guild.text_channels, name=constants.kControlsChannelName)


  def DisplayPlayers(self, victims: list[str]):
    if len(victims) == 1:
        return victims[0]
    if len(victims) ==2:
        return " and ".join(victims)
    out=victims.copy()
    out[-1]=f"and {out[-1]}"
    return ', '.join(out)


  def Error(self, description:str) -> discord.Embed:
    return discord.Embed(
        title="ERROR", 
        description=description,
        color=discord.Color.red()
        )

      
  def ChannelNotFoundError(self, channel_name: str) -> discord.Embed:
    return self.Error(f"Channel `{channel_name}` not found.")


  async def SendError(self, error: discord.Embed):
    guild=self.Guild()
    controls_channel=self.ControlsChannel()
    if controls_channel:
        await controls_channel.send(embed=error)
    else: 
        await guild.owner.send(embed=self.ChannelNotFoundError(constants.kControlsChannelName))
        await guild.owner.send(embed=error)
    

  async def CheckControlChannel(self, ctx: discord.Interaction) -> bool:
    if ctx.channel.name == constants.kControlsChannelName:
        return True
    await ctx.response.send_message(
        embed=self.Error("Must execture this command from control channel!"),
        ephemeral=True
        )
    return False


  async def CheckOwner(self, ctx: discord.Interaction) -> bool:
    if ctx.user == ctx.guild.owner:
        return True
    await ctx.response.send_message(
        embed=self.Error("Command must be executed by owner of guild!"),
        ephemeral=True
        )
    return False

  async def AddTraitor(self, member: discord.Member) -> bool:
    for channel in [await self.TraitorsInstructionsChannel(), await self.TraitorsChatChannel()]:
        if not channel:
            return False
        # Grant permission to the user to view the channel
        await channel.set_permissions(member, view_channel=True, send_messages=False)
        

  async def ClearTraitors(self):
    guild=self.Guild()
    for channel in [await self.TraitorsInstructionsChannel(), await self.TraitorsChatChannel()]:
        for user_or_role in channel.overwrites.keys():
            # Skip the bot and server owner
            if user_or_role != guild.me and user_or_role != guild.owner:
                await channel.set_permissions(
                    user_or_role,
                    overwrite=discord.PermissionOverwrite(view_channel=False)
                    ) 


  async def CheckNumTraitors(self, valid_nums:set[int]) -> bool:   
    guild=self.Guild()
    instructions_channel = await self.TraitorsInstructionsChannel()
    chat_channel = await self.TraitorsChatChannel()
    if not instructions_channel:
        return False
    if not chat_channel:
        return False
    num_instructions_members = 0
    num_chat_members = 0
    for player in self.GetPlayers():
        if instructions_channel.permissions_for(player).view_channel:
            num_instructions_members += 1
        if chat_channel.permissions_for(player).view_channel:
            num_chat_members += 1
    if num_instructions_members not in valid_nums or num_chat_members not in valid_nums:
        await self.SendError(self.Error("Incorrect number of traitors!"))
        return False
    return True


  def IsPlayer(self, user: discord.Member) -> bool: 
    """Check if member is human player."""
    guild=self.Guild()
    if user in {guild.me, guild.owner}:
        return False
    return True


  def GetPlayers(self) -> set[discord.Member]:
    """Return all players of the game as discord.Member objects."""
    guild=self.Guild()
    players=set()
    for member in guild.members:
        if self.IsPlayer(member):
            players.add(member)
    return players


  async def IsTraitor(self, user: discord.Member) -> bool:
    if not self.IsPlayer(user):
        return False
    traitors_channel = await self.TraitorsInstructionsChannel()
    if traitors_channel.permissions_for(user).view_channel:
        return True
    return False


  async def GetTraitors(self)->set[discord.Member]:
    return {player for player in self.GetPlayers() if await self.IsTraitor(player)}


  async def GetFaithful(self)->set[discord.Member]:
    return {player for player in self.GetPlayers() if not await self.IsTraitor(player)}
    