import abc
import datetime
import functools
import glob
import os
from logging import getLogger
from typing import Any, Callable, Dict, Optional, TypeVar, cast

import pandas as pd

from . import cache_record, func_utils
from .cache_config import CacheConfig, autoload_cache

logger = getLogger(__name__)

# Doing this instead of defining the types in our cache functions allows VS Code to pick up the proper type annotations
# https://github.com/microsoft/pyright/issues/774
_CacheFunc = TypeVar("_CacheFunc", bound=Callable[..., pd.DataFrame])

# Cache is disabled by default
config = autoload_cache()


def enable() -> None:
    config.enable(True)


def disable() -> None:
    config.enable(False)


def purge() -> None:
    """Remove all records from the cache"""
    logger.info("purging cache...")
    record_files = glob.glob(
        os.path.join(config.cache_directory, "*.cache_record.json")
    )
    records = [cache_record.CacheRecord(filename) for filename in record_files]
    for record in records:
        record.delete()
    logger.info("successfully purged cache")


def flush() -> None:
    """Remove all expired files from the cache"""
    record_files = glob.glob(
        os.path.join(config.cache_directory, "*.cache_record.json")
    )
    records = [cache_record.CacheRecord(filename) for filename in record_files]
    for record in records:
        if record.expired:
            record.delete()


# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
class df_cache:
    def __init__(self, expires: int = CacheConfig.DEFAULT_EXPIRATION):
        logger.debug("df_cache.__init__()")
        self.cache_config = config
        self.expires = expires

    def __call__(self, func: _CacheFunc) -> _CacheFunc:
        logger.debug("df_cache.__call__()")

        @functools.wraps(func)
        def _cached(*args: Any, **kwargs: Any) -> pd.DataFrame:
            func_data = self._safe_get_func_data(func, args, kwargs)
            result = self._safe_load_func_cache(func_data)
            if result is None:
                result = func(*args, **kwargs)
                if len(result) > 0:
                    self._safe_save_func_cache(func_data, result)

            return result

        return cast(_CacheFunc, _cached)

    def _safe_get_func_data(self, func: _CacheFunc, args: Any, kwargs: Any) -> Dict:
        logger.debug("attempting _safe_get_func_data...")
        logger.debug(f"func: {_CacheFunc}")
        logger.debug(f"args: {args}, kwargs: {kwargs}")
        try:
            func_name = func_utils.get_func_name(func)

            # Skip all this if cache is disabled
            if not self.cache_config.enabled:
                logger.debug("cache is disabled; skipping")
                return {}

            arglist = list(args)  # tuple won't come through the JSONify well
            if arglist and isinstance(
                arglist[0], abc.ABC
            ):  # remove the table classes when they're self
                arglist = arglist[1:]

            arglist = [
                (
                    arg.isoformat()
                    if any(
                        map(
                            lambda dtype: isinstance(arg, dtype),
                            [datetime.datetime, datetime.date],
                        )
                    )
                    else arg
                )
                for arg in arglist
            ]

            return {"func": func_name, "args": arglist, "kwargs": kwargs}
        except Exception as e:  # pylint: disable=bare-except
            logger.error(f"_safe_get_func_data failed: {e}")
            return {}

    def _safe_load_func_cache(self, func_data: Dict) -> Optional[pd.DataFrame]:
        logger.debug("attempting _safe_load_func_cache...")
        logger.debug(f"func_data: {func_data}")
        try:
            glob_path = os.path.join(
                self.cache_config.cache_directory,
                f"{func_data['func']}*.cache_record.json",
            )
            record_files = glob.glob(glob_path)

            records = [cache_record.CacheRecord(filename) for filename in record_files]

            for record in records:
                if not record.expired and record.supports(func_data):
                    logger.debug("successfully found dataframe")
                    return record.load_df()

            logger.debug("no cache record found")
            return None
        except Exception as e:  # pylint: disable=bare-except
            logger.error(f"_safe_load_func_cache failed: {e}")
            return None

    def _safe_save_func_cache(self, func_data: Dict, result: pd.DataFrame) -> None:
        try:
            if self.cache_config.enabled and func_data:
                new_record = cache_record.CacheRecord(
                    data=func_data, expires=self.expires
                )
                new_record.save()
                new_record.save_df(result)
        except Exception as e:  # pylint: disable=bare-except
            logger.error(f"_safe_save_func_cache failed: {e}")
            pass
