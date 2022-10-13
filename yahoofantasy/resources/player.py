from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from yahoofantasy import League

from yahoofantasy.api.parse import from_response_object, get_value
from yahoofantasy.stats.stat import Stat


class Player:

    def __init__(self,
                 league: League,
                 player_id: int,
                 first_name: str,
                 last_name: str,
                 ):
        # A cache of stats - a map of week num to the stats results
        self._stats_cache = {}

        self.league = league
        self.player_id = player_id
        self.first_name = first_name
        self.last_name = last_name

    @classmethod
    def from_response(cls, resp, league):
        p = cls(
            league=league,
            player_id=get_value(resp["player_id"]),
            first_name=get_value(resp["name"]["first"]),
            last_name=get_value(resp["name"]["last"]),
        )
        return from_response_object(p, resp)

    def __repr__(self):
        try:
            return f"Player: {self.name.full} ({self.display_position} - {self.editorial_team_abbr})"
        except AttributeError:
            return "Player: Unknown Player"

    def get_stats(self, week_num=None):
        """ Get this player's stats for a given week or the whole season """
        stats_data = self._fetch_stats(week_num)['player_stats']
        return [
            Stat.from_value(s, self.league.game_code)
            for s in get_value(stats_data).stats.stat
        ]

    def get_stat(self, stat_display, week_num=None):
        """ Get an individual player stat for a given week or the whole season """
        stats = [s for s in self.get_stats(week_num) if s.display == stat_display]
        if stats:
            return stats[0].value
        else:
            return None

    def get_points(self, week_num=None):
        """ Get this player's points for a given week or the whole season """
        player_data = self._fetch_stats(week_num)
        return get_value(player_data['player_points']['total'])

    def _fetch_stats(self, week_num=None):
        """ Fetch the stats endpoint for a given week """
        if week_num in self._stats_cache:
            return self._stats_cache[week_num]
        keys = ('season', '')
        if week_num:
            keys = (str(week_num), f"type=week;week={week_num}")
        data = self.league.ctx._load_or_fetch(
            f"player.{self.player_id}.stats.{self.league.id}.{keys[0]}",
            f"league/{self.league.id}/players;player_keys={self.player_key}/stats;{keys[1]}",
        )
        player_data = data['fantasy_content']['league']['players']['player']
        self._stats_cache[week_num] = player_data
        return player_data
