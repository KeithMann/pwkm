#!/usr/bin/env python3
"""
Market summary for the startup report: index levels and notable holdings.

Usage:
    python market.py              # Human-readable output
    python market.py --json       # JSON output

Configuration (see .env.example):
    PWKM_MARKET_INDICES     Comma-separated Label=Symbol pairs, e.g.
                            "S&P 500=^GSPC,Dow Jones=^DJI".
    PWKM_PORTFOLIO_TICKERS  Comma-separated Label=Symbol pairs for holdings
                            you want watched. Optional; indices alone are fine.
    PWKM_MARKET_THRESHOLD   Percent move that counts as notable. Default 2.0.

Symbols are whatever the data source expects. For yfinance that means suffixes
such as ".TO" for Toronto listings, and "-" where the ticker itself contains a
dot, so Canadian Tire class A is "CTC-A.TO" while you would rather read
"CTC.A". That is what the Label= half is for.

Set neither variable and the section skips cleanly, like every other optional
part of the startup report. There is no default index list on purpose: a
market section nobody asked for is noise, and it would pull in a dependency
for no reason.

Requires the optional dependency `yfinance`. Without it this section reports
that it is unavailable and the rest of the startup report continues.
"""

import argparse
import json
import os
import sys
from datetime import datetime

from pwkm_env import load_env

load_env()

# No default index list: unset means the section is off. See the docstring.
DEFAULT_INDICES = ""
ALERT_THRESHOLD_DEFAULT = 2.0


def parse_pairs(raw: str) -> dict:
    """Parse 'Label=Symbol,Symbol2' into {symbol: label}.

    An entry with no '=' uses the symbol as its own label. Blank entries and
    entries with a label but no symbol are skipped rather than producing an
    empty ticker that the data source would reject.
    """
    out = {}
    for entry in (e.strip() for e in (raw or "").split(",")):
        if not entry:
            continue
        if "=" in entry:
            label, _, symbol = entry.partition("=")
            label, symbol = label.strip(), symbol.strip()
        else:
            symbol, label = entry, ""
        if not symbol:
            continue
        out[symbol] = label or symbol
    return out


INDICES = parse_pairs(os.environ.get("PWKM_MARKET_INDICES", DEFAULT_INDICES))
PORTFOLIO = parse_pairs(os.environ.get("PWKM_PORTFOLIO_TICKERS", ""))

try:
    ALERT_THRESHOLD = float(os.environ.get("PWKM_MARKET_THRESHOLD", ALERT_THRESHOLD_DEFAULT))
except ValueError:
    ALERT_THRESHOLD = ALERT_THRESHOLD_DEFAULT


def fail(msg: str, use_json: bool) -> int:
    """Report a failure and return exit code 1.

    The message goes to STDERR deliberately. startup.py reads stderr when a
    helper exits non-zero and discards stdout, so a diagnostic printed only to
    stdout is replaced by "Error: Unknown error" in the report.
    """
    if use_json:
        print(json.dumps({"error": msg}))
    print(msg, file=sys.stderr)
    return 1


def pct_change(latest, previous):
    """Percent change, or None if either value is unusable."""
    try:
        p, pv = float(latest), float(previous)
    except (TypeError, ValueError):
        return None
    if p <= 0 or pv <= 0:
        return None
    return (p - pv) / pv * 100.0

def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Market summary for the startup report")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if not INDICES and not PORTFOLIO:
        msg = ("Market not configured. Set PWKM_MARKET_INDICES or "
               "PWKM_PORTFOLIO_TICKERS in .env to enable this section.")
        print(json.dumps({"configured": False, "message": msg}) if args.json else f"[{msg}]")
        # Exit 0: an unconfigured optional section is not a failure.
        return 0

    try:
        import yfinance as yf
    except ImportError:
        msg = ("Market unavailable: yfinance is not installed. "
               "Install it with: pip install yfinance")
        print(json.dumps({"available": False, "message": msg}) if args.json else f"[{msg}]")
        # Exit 0, not 1. A missing optional dependency is a setup choice, and
        # exiting non-zero would replace this actionable message with
        # "Error: Unknown error" in the startup report.
        return 0

    import logging
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)

    now = datetime.now()
    ts = now.strftime("%I:%M %p").lstrip("0").lower()
    all_symbols = list(INDICES) + list(PORTFOLIO)

    try:
        data = yf.download(all_symbols, period="5d", progress=False, threads=True)
        close = data["Close"]
    except Exception as e:
        return fail(f"Market unavailable: failed to fetch market data: {e}", args.json)

    if len(close) < 2:
        return fail("Market unavailable: insufficient trading data returned", args.json)

    last = close.iloc[-1]
    prev = close.iloc[-2]
    trade_date = close.index[-1].strftime("%Y-%m-%d")

    index_data = {}
    for symbol, label in INDICES.items():
        if symbol in last and symbol in prev:
            change = pct_change(last[symbol], prev[symbol])
            if change is not None:
                index_data[label] = {
                    "price": round(float(last[symbol]), 2),
                    "change_pct": round(change, 2),
                }

    movers = []
    for symbol, label in PORTFOLIO.items():
        if symbol in last and symbol in prev:
            change = pct_change(last[symbol], prev[symbol])
            if change is not None and abs(change) >= ALERT_THRESHOLD:
                movers.append({
                    "ticker": label,
                    "price": round(float(last[symbol]), 2),
                    "change_pct": round(change, 2),
                })

    if args.json:
        print(json.dumps({
            "generated": now.strftime("%Y-%m-%d %H:%M"),
            "trade_date": trade_date,
            "indices": index_data,
            "movers": movers,
            "threshold": ALERT_THRESHOLD,
        }, indent=2))
        return 0

    lines = [f"[Generated: {now.strftime('%Y-%m-%d')} {ts} | Last trading day: {trade_date}]"]

    for label, q in index_data.items():
        arrow = "\u25b2" if q["change_pct"] >= 0 else "\u25bc"
        lines.append(f"  {label}: {q['price']:,.2f} ({arrow} {abs(q['change_pct']):.2f}%)")

    if not index_data and INDICES:
        lines.append("  [Index data unavailable]")

    if movers:
        lines.append(f"  Movers (>{ALERT_THRESHOLD:g}%):")
        for m in sorted(movers, key=lambda x: abs(x["change_pct"]), reverse=True):
            arrow = "\u25b2" if m["change_pct"] >= 0 else "\u25bc"
            lines.append(f"    {m['ticker']}: {m['price']:,.2f} ({arrow} {abs(m['change_pct']):.2f}%)")
    elif PORTFOLIO:
        lines.append(f"  No movers above {ALERT_THRESHOLD:g}%.")

    print("\n".join(lines))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())