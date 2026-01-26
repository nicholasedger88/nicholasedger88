import datetime as dt
from dataclasses import dataclass
from typing import Dict, List

import requests

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
COINGECKO_MARKET_URL = "https://api.coingecko.com/api/v3/coins/pax-gold/market_chart"


@dataclass
class MarketSnapshot:
    name: str
    current: float
    change_1d: float
    change_5d: float
    change_ytd: float
    label: str


YAHOO_SYMBOLS = {
    "S&P 500": "^GSPC",
    "Nasdaq 100": "^NDX",
    "FTSE 100": "^FTSE",
    "MSCI World": "URTH",
    "Oil (Brent)": "BZ=F",
    "USD (DXY)": "DX-Y.NYB",
    "US 10Y": "^TNX",
}


def _label_from_change(change_1d: float) -> str:
    if change_1d > 1:
        return "strong"
    if change_1d < -1:
        return "shaky"
    return "steady"


def _percent_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return round(((current - previous) / previous) * 100, 2)


def _parse_yahoo_series(data: Dict) -> List[float]:
    closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    return [value for value in closes if value is not None]


def _parse_yahoo_timestamps(data: Dict) -> List[int]:
    return data["chart"]["result"][0]["timestamp"]


def _fetch_yahoo_snapshot(name: str, symbol: str) -> MarketSnapshot:
    response = requests.get(
        YAHOO_CHART_URL.format(symbol=symbol),
        params={"interval": "1d", "range": "1y"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    closes = _parse_yahoo_series(data)
    timestamps = _parse_yahoo_timestamps(data)

    if len(closes) < 6:
        raise ValueError(f"Not enough data for {name}")

    current = closes[-1]
    change_1d = _percent_change(current, closes[-2])
    change_5d = _percent_change(current, closes[-6])

    year_start_index = 0
    for idx, ts in enumerate(timestamps):
        date = dt.datetime.utcfromtimestamp(ts)
        if date.year == dt.datetime.utcnow().year:
            year_start_index = idx
            break

    ytd_base = closes[max(year_start_index, 0)]
    change_ytd = _percent_change(current, ytd_base)

    return MarketSnapshot(
        name=name,
        current=round(current, 2),
        change_1d=change_1d,
        change_5d=change_5d,
        change_ytd=change_ytd,
        label=_label_from_change(change_1d),
    )


def _fetch_gold_snapshot() -> MarketSnapshot:
    response = requests.get(
        COINGECKO_MARKET_URL,
        params={"vs_currency": "usd", "days": 365},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    prices = [point[1] for point in data.get("prices", [])]
    timestamps = [point[0] for point in data.get("prices", [])]
    if len(prices) < 6:
        raise ValueError("Not enough data for gold")

    current = prices[-1]
    change_1d = _percent_change(current, prices[-2])
    change_5d = _percent_change(current, prices[-6])

    current_year = dt.datetime.utcnow().year
    year_start_index = 0
    for idx, ts in enumerate(timestamps):
        date = dt.datetime.utcfromtimestamp(ts / 1000)
        if date.year == current_year:
            year_start_index = idx
            break

    ytd_base = prices[max(year_start_index, 0)]
    change_ytd = _percent_change(current, ytd_base)

    return MarketSnapshot(
        name="Gold",
        current=round(current, 2),
        change_1d=change_1d,
        change_5d=change_5d,
        change_ytd=change_ytd,
        label=_label_from_change(change_1d),
    )


def fetch_market_snapshot() -> List[MarketSnapshot]:
    snapshots: List[MarketSnapshot] = []
    for name, symbol in YAHOO_SYMBOLS.items():
        snapshots.append(_fetch_yahoo_snapshot(name, symbol))
    snapshots.append(_fetch_gold_snapshot())
    return snapshots


def generate_summary(markets: List[MarketSnapshot]) -> str:
    strong = [m.name for m in markets if m.label == "strong"]
    shaky = [m.name for m in markets if m.label == "shaky"]

    if strong and shaky:
        return f"Mixed session: strength in {', '.join(strong[:2])}, softness in {', '.join(shaky[:2])}."
    if strong:
        return f"Momentum held firm with {', '.join(strong[:2])} leading higher."
    if shaky:
        return f"Risk appetite softened as {', '.join(shaky[:2])} slipped." 
    return "Markets were steady with only modest moves across the board."
