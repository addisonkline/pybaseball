import pandas as pd

from .amateur_draft import amateur_draft
from .amateur_draft_by_team import amateur_draft_by_team


def amateur_draft_data(
    year: int,
    round: int,
    team: str | None = None,
    keep_stats: bool = True,
) -> pd.DataFrame:
    """
    Get amateur draft results by year and round.
    If `team` is provided, get amateur draft results by team and year.
    """
    if team is None:
        return amateur_draft(year, round, keep_stats)
    else:
        return amateur_draft_by_team(team, year, keep_stats)
