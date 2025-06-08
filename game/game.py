import discord
import game.constants as constants
from player import Player


class Game:
    def __init__(self, client: discord.Client, guild_id: int):
        self.guild = self.client.get_guild(guild_id)
        if not self.guild:
            raise ValueError(f"Could not find guild from guild id: '{guild_id}'")
        self.client = client
        self.players = [Player(player) for player in self._get_players()]

    # ------------------------------[ Getters ]------------------------------
    def _guild(self) -> discord.Guild:
        return self.guild

    def _general_channel(self):
        pass

    def _announcements_channel(self):
        pass

    def _traitors_instructions_channel(self):
        pass

    def _traitors_chat_channel(self):
        pass

    def _controls_channel(self):
        pass

    def _banished_role(self):
        pass

    def _dead_role(self):
        pass

    # ------------------------------[ Game State Information ]------------------------------
    def _is_player(self, player):
        pass

    def _get_players(self):
        pass

    def _display_players(self):
        pass

    def _get_faithful(self):
        pass

    def _is_traitor(self, player):
        pass

    def _get_traitors(self):
        pass

    def _get_role(self, player):
        pass

    def _is_banished(self, player):
        pass

    def _get_banished(self):
        pass

    def _is_dead(self, player):
        pass

    def _get_dead(self):
        pass

    def _is_out(self, player):
        pass

    # ------------------------------[ Actions ]------------------------------

    def kill(self, player):
        pass

    def banish(self, palayer):
        pass

    def make_traitor(self, player):
        pass

    def clear_traitors(self):
        pass

    def check_num_traitors(self):
        pass

    def check_in_controls_channel(self):
        pass

    def check_owner(self) -> bool:
        pass

    # TODO: use inheritance from discord.Emed:
    # error
    # channel_not_found_error
    # send_error
