import datetime
from io import StringIO
from time import sleep
from typing import Any, Optional, Union

import pandas as pd
from bs4 import BeautifulSoup, Comment
from curl_cffi import requests

from ..datahelpers import singleton


class BRefSession(singleton.Singleton):
    """
    This is needed because Baseball Reference has rules against bots.

    Current policy says no more than 20 requests per minute, but in testing
    anything more than 10 requests per minute gets you blocked for one hour.

    So this global session will prevent a user from getting themselves blocked.
    """

    def __init__(self, max_requests_per_minute: int = 10) -> None:
        self.max_requests_per_minute = max_requests_per_minute
        self.last_request: Optional[datetime.datetime]  = None
        self.session = requests.Session()
    
    def get(self, url: str, **kwargs: Any) -> requests.Response:
        if self.last_request:
            delta = datetime.datetime.now() - self.last_request
            sleep_length = (60 / self.max_requests_per_minute) - delta.total_seconds()
            if sleep_length > 0:
                sleep(sleep_length)

        self.last_request = datetime.datetime.now()
        try:
            resp = self.session.get(url, impersonate="chrome", **kwargs)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

        return -1


def read_bref_table(html: Union[str, bytes], table_id: str) -> pd.DataFrame:
    if isinstance(html, bytes):
        html = html.decode("utf-8", errors="replace")

    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", attrs={"id": table_id})
    if table is None:
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment_soup = BeautifulSoup(comment, "lxml")
            table = comment_soup.find("table", attrs={"id": table_id})
            if table is not None:
                break

    if table is None:
        raise RuntimeError(f"Table with id '{table_id}' not found on scraped page.")

    return pd.read_html(StringIO(str(table)))[0]
                
