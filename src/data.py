import yfinance as yf
import pandas as pd
import os
import hashlib
import json
from datetime import datetime


CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cache")


def _cache_key(tickers: list[str], start: str | None, end: str | None, period: str | None) -> str:
    raw = json.dumps({"tickers": sorted(tickers), "start": start, "end": end, "period": period})
    return hashlib.md5(raw.encode()).hexdigest()


def _cache_path(key: str) -> str:
    return os.path.join(CACHE_DIR, f"{key}.parquet")


def _meta_path(key: str) -> str:
    return os.path.join(CACHE_DIR, f"{key}.json")


def _is_cache_valid(key: str, max_age_days: int = 1) -> bool:
    meta_file = _meta_path(key)
    if not os.path.exists(meta_file):
        return False
    with open(meta_file, "r") as f:
        meta = json.load(f)
    cached_time = datetime.fromisoformat(meta.get("fetched_at", "2000-01-01"))
    age = (datetime.now() - cached_time).days
    return age <= max_age_days


def clear_cache(tickers: list[str] | None = None) -> int:
    os.makedirs(CACHE_DIR, exist_ok=True)
    if tickers is None:
        count = 0
        for f in os.listdir(CACHE_DIR):
            os.remove(os.path.join(CACHE_DIR, f))
            count += 1
        return count
    key = _cache_key(tickers, None, None, None)
    removed = 0
    for f in [_cache_path(key), _meta_path(key)]:
        if os.path.exists(f):
            os.remove(f)
            removed += 1
    return removed


def fetch_prices(
    tickers: list[str],
    start: str | None = None,
    end: str | None = None,
    period: str | None = None,
    use_cache: bool = True,
    cache_max_age_days: int = 1,
) -> pd.DataFrame:
    key = _cache_key(tickers, start, end, period)

    if use_cache and _is_cache_valid(key, cache_max_age_days):
        cache_file = _cache_path(key)
        if os.path.exists(cache_file):
            prices = pd.read_parquet(cache_file)
            prices.index = pd.to_datetime(prices.index)
            return prices

    kwargs = {"tickers": tickers, "auto_adjust": True, "progress": False}
    if start or end:
        kwargs["start"] = start
        kwargs["end"] = end
    else:
        kwargs["period"] = period or "10y"
    data = yf.download(**kwargs)
    if data.empty:
        return pd.DataFrame()

    close = data["Close"] if "Close" in data.columns else data
    if isinstance(close, pd.DataFrame) and close.columns.inferred_type == "mixed":
        close.columns = [str(c) for c in close.columns]
    if len(tickers) == 1:
        prices = close.to_frame(name=tickers[0]) if isinstance(close, pd.Series) else close
    else:
        prices = close
    prices = prices.dropna()
    prices.index = pd.to_datetime(prices.index)

    if use_cache:
        os.makedirs(CACHE_DIR, exist_ok=True)
        prices.to_parquet(_cache_path(key))
        with open(_meta_path(key), "w") as f:
            json.dump({
                "fetched_at": datetime.now().isoformat(),
                "tickers": tickers,
                "start": start,
                "end": end,
                "period": period,
                "rows": len(prices),
            }, f)

    return prices


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna()


def fetch_info(ticker: str) -> dict:
    return yf.Ticker(ticker).info
