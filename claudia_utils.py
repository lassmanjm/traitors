import discord
import constants


class ClaudiaUtils:
    def __init__(self, client: discord.Client, guild_id: int):
        self.client = client
        self.guild_id = guild_id
        self.guild = None

    def Guild(self) -> discord.Guild | None:
        return self.client.get_guild(self.guild_id)

    def GeneralChannel(self) -> discord.TextChannel | None:
        guild = self.Guild()
        return discord.utils.get(
            guild.text_channels, name=constants.kGeneralChannelName
        )

    async def AnnouncementsChannel(
        self, send_error: bool = True
    ) -> discord.TextChannel | None:
        guild = self.Guild()
        channel = discord.utils.get(
            guild.text_channels, name=constants.kAnnouncementsChannelName
        )
        if not channel and send_error:
            await self.SendError(
                self.ChannelNotFoundError(constants.kAnnouncementsChannelName)
            )
        return channel

    async def TraitorsInstructionsChannel(
        self, send_error: bool = True
    ) -> discord.TextChannel | None:
        guild = self.Guild()
        channel = discord.utils.get(
            guild.text_channels, name=constants.kTraitorsInstructionsChannelName
        )
        if not channel and send_error:
            await self.SendError(
                self.ChannelNotFoundError(constants.kTraitorsInstructionsChannelName)
            )
        return channel

    async def TraitorsChatChannel(
        self, send_error: bool = True
    ) -> discord.TextChannel | None:
        guild = self.Guild()
        channel = discord.utils.get(
            guild.text_channels, name=constants.kTraitorsChatChannelName
        )
        if not channel and send_error:
            await self.SendError(
                self.ChannelNotFoundError(constants.kTraitorsChatChannelName)
            )
        return channel

    def ControlsChannel(self) -> discord.TextChannel | None:
        guild = self.Guild()
        return discord.utils.get(
            guild.text_channels, name=constants.kControlsChannelName
        )

    async def GetRole(self, role_name: str) -> discord.Role:
        guild = self.Guild()
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            role = await guild.create_role(name=role_name)
        return role

    async def BanishedRole(self) -> discord.Role:
        return await self.GetRole(role_name=constants.kBanishedRoleName)

    async def DeadRole(self) -> discord.Role:
        return await self.GetRole(role_name=constants.kDeadRoleName)

    def DisplayPlayers(self, victims: list[str]):
        if len(victims) == 1:
            return victims[0]
        if len(victims) == 2:
            return " and ".join(victims)
        out = victims.copy()
        out[-1] = f"and {out[-1]}"
        return ", ".join(out)

    def Error(self, description: str) -> discord.Embed:
        return discord.Embed(
            title="ERROR", description=description, color=discord.Color.red()
        )

    def ChannelNotFoundError(self, channel_name: str) -> discord.Embed:
        return self.Error(f"Channel `{channel_name}` not found.")

    async def SendError(self, error: discord.Embed):
        guild = self.Guild()
        controls_channel = self.ControlsChannel()
        if controls_channel:
            await controls_channel.send(embed=error)
        else:
            await guild.owner.send(
                embed=self.ChannelNotFoundError(constants.kControlsChannelName)
            )
            await guild.owner.send(embed=error)

    async def CheckControlChannel(self, ctx: discord.Interaction) -> bool:
        if ctx.channel.name == constants.kControlsChannelName:
            return True
        await ctx.response.send_message(
            embed=self.Error("Must execture this command from control channel!"),
            ephemeral=True,
        )
        return False

    async def CheckOwner(self, ctx: discord.Interaction) -> bool:
        if ctx.user == ctx.guild.owner:
            return True
        await ctx.response.send_message(
            embed=self.Error("Command must be executed by owner of guild!"),
            ephemeral=True,
        )
        return False

    async def AddTraitor(self, member: discord.Member) -> bool:
        instructions_channel = await self.TraitorsInstructionsChannel()
        if not instructions_channel:
            return False
        await instructions_channel.set_permissions(
            member,
            view_channel=True,
            send_messages=False,
            create_public_threads=False,
            create_private_threads=False,
        )
        chat_channel = await self.TraitorsChatChannel()
        if not chat_channel:
            return False
        await chat_channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True,
        )
        return True

    async def ClearTraitors(self):
        guild = self.Guild()
        for channel in [
            await self.TraitorsInstructionsChannel(),
            await self.TraitorsChatChannel(),
        ]:
            for user_or_role in channel.overwrites.keys():
                # Skip the bot and server owner
                if user_or_role != guild.me and user_or_role != guild.owner:
                    await channel.set_permissions(
                        user_or_role,
                        overwrite=discord.PermissionOverwrite(view_channel=False),
                    )

    async def CheckNumTraitors(self, valid_nums: set[int]) -> bool:
        instructions_channel = await self.TraitorsInstructionsChannel()
        chat_channel = await self.TraitorsChatChannel()
        if not instructions_channel:
            return False
        if not chat_channel:
            return False
        num_instructions_members = 0
        num_chat_members = 0
        for player in await self.GetPlayers():
            if instructions_channel.permissions_for(player).view_channel:
                num_instructions_members += 1
            if chat_channel.permissions_for(player).view_channel:
                num_chat_members += 1
        if (
            num_instructions_members not in valid_nums
            or num_chat_members not in valid_nums
        ):
            await self.SendError(self.Error("Incorrect number of traitors!"))
            return False
        return True

    async def IsBanished(self, player: discord.Member) -> bool:
        banished_role = await self.BanishedRole()
        if banished_role in player.roles:
            return True
        return False

    async def IsDead(self, player: discord.Member) -> bool:
        dead_role = await self.DeadRole()
        if dead_role in player.roles:
            return True
        return False

    async def IsOut(self, player: discord.Member) -> bool:
        return await self.IsDead(player) or await self.IsBanished(player)

    async def IsPlayer(
        self, user: discord.Member, include_out_players: bool = False
    ) -> bool:
        """Check if member is human player."""
        guild = self.Guild()
        # User is bot or guild owner
        if user in {guild.me, guild.owner}:
            return False
        if not include_out_players and await self.IsOut(user):
            return False
        return True

    async def GetPlayers(
        self, include_out_players: bool = False
    ) -> set[discord.Member]:
        """Return all players of the game as discord.Member objects."""
        guild = self.Guild()
        players = set()
        for member in guild.members:
            if await self.IsPlayer(member, include_out_players):
                players.add(member)
        return players

    async def IsTraitor(
        self, user: discord.Member, include_banished: bool = False
    ) -> bool:
        if not await self.IsPlayer(user, include_out_players=include_banished):
            return False
        traitors_channel = await self.TraitorsInstructionsChannel()
        if traitors_channel.permissions_for(user).view_channel:
            return True
        return False

    async def GetTraitors(
        self, include_out_players: bool = False
    ) -> set[discord.Member]:
        return {
            player
            for player in await self.GetPlayers(include_out_players)
            if await self.IsTraitor(player, include_banished=include_out_players)
        }

    async def GetFaithful(
        self, include_out_players: bool = False
    ) -> set[discord.Member]:
        return {
            player
            for player in await self.GetPlayers(include_out_players)
            if not await self.IsTraitor(player, include_banished=include_out_players)
        }

    async def GetBanished(self) -> set[discord.Member]:
        return {
            player
            for player in await self.GetPlayers(include_out_players=True)
            if not await self.IsBanished(player)
        }

    async def GetDead(self) -> set[discord.Member]:
        return {
            player
            for player in await self.GetPlayers(include_out_players=True)
            if not await self.IsDead(player)
        }
