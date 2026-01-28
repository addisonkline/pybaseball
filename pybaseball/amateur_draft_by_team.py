import logging

import pandas as pd

from . import cache
from .datasources.bref import BRefSession, read_bref_table

logger = logging.getLogger(__name__)

session = BRefSession()

# pylint: disable=line-too-long
_URL = "https://www.baseball-reference.com/draft/?team_ID={team}&year_ID={year}&draft_type=junreg&query_type=franch_year"


def get_draft_results(team: str, year: int) -> pd.DataFrame:
    logger.debug(f"getting draft results for {team} in {year}")
    url = _URL.format(team=team, year=year)
    resp = session.get(url, timeout=None)
    if resp == -1:
        raise RuntimeError(f"error getting draft results for {team} in {year}")
    try:
        draft_results = read_bref_table(resp.text, "draft_stats")
        return draft_results
    except Exception as e:
        logger.error(f"error getting draft results for {team} in {year}: {e}")
        logger.debug("response got status code %s", getattr(resp, "status_code", "unknown"))
        logger.debug("response got content type %s", getattr(resp, "headers", {}).get("Content-Type", "unknown"))
        logger.debug("response got content %s...", str(resp.text)[:200])
        raise e


def postprocess(draft_results: pd.DataFrame) -> pd.DataFrame:
    logger.debug("postprocessing draft results")
    draft_results = draft_results.drop(["Year", "Rnd", "RdPck", "DT"], axis=1)
    return remove_name_suffix(draft_results)


def remove_name_suffix(draft_results: pd.DataFrame) -> pd.DataFrame:
    logger.debug("removing name suffix from draft results")
    draft_results.loc[:, "Name"] = draft_results["Name"].apply(remove_minors_link)
    return draft_results


def remove_minors_link(draftee: str) -> str:
    logger.debug(f"removing minors link from {draftee}")
    return draftee.split("(")[0]


def drop_stats(draft_results: pd.DataFrame) -> pd.DataFrame:
    logger.debug("dropping stats from draft results")
    draft_results.drop(
        ["WAR", "G", "AB", "HR", "BA", "OPS", "G.1", "W", "L", "ERA", "WHIP", "SV"],
        axis=1,
        inplace=True,
    )
    return draft_results


@cache.df_cache()
def amateur_draft_by_team(
    team: str,
    year: int,
    keep_stats: bool = True,
) -> pd.DataFrame:
    """
    Get amateur draft results by team and year.

    ARGUMENTS
        team: Team code which you want to check. See docs for team codes 
            (https://github.com/jldbc/pybaseball/blob/master/docs/amateur_draft_by_team.md)
        year: Year which you want to check.

    """
    logger.debug(f"getting amateur draft results for {team} in {year}")
    draft_results = get_draft_results(team, year)
    draft_results = postprocess(draft_results)
    if not keep_stats:
        draft_results = drop_stats(draft_results)
    
    logger.debug(f"amateur draft results for {team} in {year} retrieved SUCCESSFULLY")
    return draft_results
