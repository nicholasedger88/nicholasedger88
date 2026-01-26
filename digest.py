from dataclasses import dataclass
from typing import List


@dataclass
class MarketTile:
    name: str
    change_1d: str
    change_5d: str
    change_ytd: str


@dataclass
class Digest:
    subject: str
    summary: str
    tiles: List[MarketTile]


def build_digest() -> Digest:
    tiles = [
        MarketTile("S&P 500", "+0.4%", "+1.2%", "+9.1%"),
        MarketTile("Nasdaq 100", "+0.6%", "+1.8%", "+12.4%"),
        MarketTile("FTSE 100", "-0.2%", "+0.5%", "+4.3%"),
        MarketTile("MSCI World", "+0.3%", "+0.8%", "+8.4%"),
        MarketTile("Gold", "-0.1%", "-0.6%", "+6.2%"),
        MarketTile("Oil", "-0.8%", "-2.1%", "+3.0%"),
        MarketTile("USD Index", "+0.2%", "+0.1%", "-1.4%"),
        MarketTile("US 10Y", "+4bp", "+8bp", "-12bp"),
    ]
    return Digest(
        subject="Markets in 90 Seconds",
        summary=(
            "Calm snapshot: equities were steady, yields nudged higher, and energy cooled on"
            " improved inventories."
        ),
        tiles=tiles,
    )
