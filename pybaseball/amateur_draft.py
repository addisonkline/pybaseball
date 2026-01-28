import logging

import pandas as pd

from . import cache
from .datasources.bref import BRefSession, read_bref_table

logger = logging.getLogger(__name__)

session = BRefSession()

# pylint: disable=line-too-long
_URL = "https://www.baseball-reference.com/draft/?year_ID={year}&draft_round={draft_round}&draft_type=junreg&query_type=year_round&"


def get_draft_results(year: int, draft_round: int) -> pd.DataFrame:
    logger.debug(f"getting draft results for {year} and {draft_round}")
    url = _URL.format(year=year, draft_round=draft_round)
    resp = session.get(url, timeout=None)
    if resp == -1:
        raise RuntimeError(f"error getting draft results for {year} and {draft_round}")
    try:
        draft_results = read_bref_table(resp.text, "draft_stats")
    except Exception as e:
        logger.error(f"error getting draft results for {year} and {draft_round}: {e}")
        logger.debug("response got status code %s", getattr(resp, "status_code", "unknown"))
        logger.debug("response got content type %s", getattr(resp, "headers", {}).get("Content-Type", "unknown"))
        logger.debug("response got content %s...", str(resp.text)[:200])
        raise e
    return draft_results


@cache.df_cache()
def amateur_draft(year: int, draft_round: int, keep_stats: bool = True) -> pd.DataFrame:
    """
    Retrieves the MLB amateur draft results by year and round.

    ARGUMENTS
        year: The year for which you wish to retrieve draft results.
        draft_round: The round for which you wish to retrieve draft results. There is no distinction made 
            between the competitive balance, supplementary, and main portions of a round.
        keep_stats: A boolean parameter that controls whether the major league stats of each draftee is 
            displayed. Default set to true.
    """
    logger.debug(f"getting amateur draft results for {year} and {draft_round}")
    draft_results = get_draft_results(year, draft_round)
    draft_results = postprocess(draft_results)
    if not keep_stats:
        draft_results = drop_stats(draft_results)

    logger.debug(f"amateur draft results for {year} and {draft_round} retrieved SUCCESSFULLY")
    return draft_results


def postprocess(draft_results: pd.DataFrame) -> pd.DataFrame:
    logger.debug("postprocessing draft results")
    draft_results = draft_results.drop(['Year', 'Rnd', 'RdPck', 'DT', 'FrRnd'], axis=1)
    return remove_name_suffix(draft_results)


def drop_stats(draft_results: pd.DataFrame) -> pd.DataFrame:
    logger.debug("dropping stats from draft results")
    draft_results.drop(['WAR', 'G', 'AB', 'HR', 'BA', 'OPS', 'G.1', 'W', 'L', 'ERA', 'WHIP', 'SV'], axis=1,
                       inplace=True)
    return draft_results


def remove_name_suffix(draft_results: pd.DataFrame) -> pd.DataFrame:
    logger.debug("removing name suffix from draft results")
    draft_results.loc[:, 'Name'] = draft_results['Name'].apply(remove_minors_link)
    return draft_results


def remove_minors_link(draftee: str) -> str:
    logger.debug(f"removing minors link from {draftee}")
    return draftee.split('(')[0]
