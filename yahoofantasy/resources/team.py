from __future__ import annotations

import json
from inspect import getmembers
from typing import List

from typing import TYPE_CHECKING

from EZPZLogging.setup_logging import get_logger

if TYPE_CHECKING:
    from yahoofantasy import Context, League

from yahoofantasy.util.logger import logger
from yahoofantasy.api.parse import as_list, from_response_object
from yahoofantasy.util.persistence import DEFAULT_TTL
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .player import Player
from .roster import Roster


class TeamManager:

    def __init__(self, manager_id: int, name: str, guid: str):
        self.manager_id = manager_id
        self.name = name
        self.guid = guid


class Team:

    def __init__(self,
                 ctx: Context,
                 league: League,
                 team_id: int,
                 team_key: str,
                 name: str,
                 waiver_priority: int,
                 number_of_moves: int,
                 number_of_trades: int,
                 draft_position: int,
                 managers_dict: dict
                 ):
        self.ctx = ctx
        self.league = league
        # like 1, 2, 3
        self.team_id = team_id
        # the identifier I think built by the lib
        self.team_key = team_key
        self.name = name
        self.waiver_priority = waiver_priority
        self.number_of_moves = number_of_moves
        self.number_of_trades = number_of_trades
        self.draft_position = draft_position
        logger = get_logger("team")
        # logger.info(getmembers(managers_dict))
        logger.info(json.dumps(managers_dict, indent=4))
        # raise Exception("all managers?")
        # exit()
        first_manager = managers_dict["manager"]
        self.managers = [
            TeamManager(first_manager["manager_id"]["$"], first_manager["nickname"]["$"], first_manager["guid"]["$"]),
        ]

    @property
    def manager(self):
        """ We can have multiple managers, so here's a shortcut to get 1 manager """
        return as_list(self.managers)[0]

    def players(self, persist_ttl=DEFAULT_TTL) -> List[Player]:
        logger.debug("Looking up current players on team")
        data = self.ctx._load_or_fetch(
            f"team.{self.id}.players",
            f"team/{self.id}/players",
        )
        players = []
        for p in data['fantasy_content']['team']['players']['player']:
            player = Player.from_response(p, self.league)
            player = from_response_object(player, p)
            players.append(player)
        return players

    # TODO: Adjust this method to account for non-week based games
    def roster(self, week_num=None):
        """ Fetch this team's roster for a given week

        If week_num is None fetch the live roster
        """
        # First item is the peristence key, second is the API filter
        keys = ('live', '')
        if week_num:
            keys = (str(week_num), f"week={week_num}")
        data = self.ctx._load_or_fetch(
            f"team.{self.id}.roster.{keys[0]}",
            f"team/{self.id}/roster;{keys[1]}",
        )
        roster_data = data['fantasy_content']['team']['roster']
        roster = Roster(self, week_num)
        roster = from_response_object(roster, roster_data, set_raw=True)
        return roster

    def __repr__(self):
        return f"Team {self.name}"
