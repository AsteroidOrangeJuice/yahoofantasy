from __future__ import annotations

import json

from EZPZLogging.setup_logging import get_logger
from yahoofantasy.api.parse import from_response_object, get_value
from yahoofantasy.util.persistence import DEFAULT_TTL
from yahoofantasy.util.logger import logger
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ..context import Context
from .team import Team
from .standings import Standings
from .week import Week
from .draft_result import DraftResult
from .transaction import Transaction


class League:

    def __init__(self,
                 ctx: Context,
                 name: str,
                 league_key: str,
                 league_id: str,
                 draft_status: str,
                 num_teams: str,
                 scoring_type: str,
                 league_type: str,
                 renew: int,
                 current_week: int,
                 start_week: int,
                 end_week: int,
                 year: int,
                 ):
        self.ctx = ctx
        self.id = league_key
        self.name = name
        self.league_key = league_key
        self.players = list()
        self.league_id = league_id
        self.draft_status = draft_status
        self.num_teams = num_teams
        self.scoring_type = scoring_type
        self.league_type = league_type
        self.renew = renew
        self.current_week = current_week
        self.start_week = start_week
        self.end_week = end_week
        self.year = year

    def get_team(self, team_key):
        return next((t for t in self.teams() if t.team_key == team_key), None)

    def teams(self, persist_ttl=DEFAULT_TTL) -> List[Team]:
        data = self.ctx._load_or_fetch('teams.' + self.id, 'teams', league=self.id)
        teams = []
        for team in data['fantasy_content']['league']['teams']['team']:
            t = Team(
                self.ctx,
                self,
                get_value(team['team_id']),
                get_value(team['team_key']),
                get_value(team['name']),
                get_value(team['waiver_priority']),
                get_value(team['number_of_moves']),
                get_value(team['number_of_trades']),
                get_value(team['draft_position']),
                team['managers'],
            )
            # from_response_object(t, team)
            teams.append(t)
        return teams

    def standings(self, persist_ttl=DEFAULT_TTL):
        logger.debug("Looking up standings")
        data = self.ctx._load_or_fetch(
            'standings.' + self.id, 'standings', league=self.id)
        standings = []
        for team in data['fantasy_content']['league']['standings']['teams']['team']:
            standing = Standings(self.ctx, self, get_value(team['team_key']))
            from_response_object(standing, team)
            standings.append(standing)
        return standings

    def weeks(self, persist_ttl=DEFAULT_TTL):
        if not self.start_week or not self.end_week:
            raise AttributeError(
                "Can't fetch weeks for a league without start/end weeks. Is it a "
                "head-to-head league? Did you sync your league already?")
        logger.debug("Looking up weeks")
        out = []
        for week_num in range(self.start_week, self.end_week + 1):
            week = Week(self.ctx, self, week_num)
            week.sync()
            out.append(week)
        return out

    def draft_results(self, persist_ttl=DEFAULT_TTL):
        results = []
        for team in self.teams(persist_ttl):
            data = self.ctx._load_or_fetch(
                'draftresults.' + team.id,
                f'team/{team.id}/draftresults;out=players')
            for result in data['fantasy_content']['team']['draft_results']['draft_result']:
                dr = DraftResult(self, team)
                from_response_object(dr, result)
                results.append(dr)
        return results

    def transactions(self, persist_ttl=DEFAULT_TTL):
        results = []
        data = self.ctx._load_or_fetch(
            'transactions.' + self.id, 'transactions', league=self.id)
        for result in data['fantasy_content']['league']['transactions']['transaction']:
            trans = Transaction.from_response(result, self)
            results.append(trans)
        return results

    def __repr__(self):
        return "League: {}".format(getattr(self, 'name', 'Unnamed League'))
