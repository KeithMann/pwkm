#!/usr/bin/env python3
"""
Shared .env loader for the PWKM scripts.

Why this exists
---------------
Most PWKM scripts read their configuration at module level, for example:

    TZ = ZoneInfo(os.environ.get("LOCAL_TIMEZONE", "America/New_York"))

That read happens the moment the module is imported. Any .env loading that
happens later, inside a function, is too late to affect it. Several scripts
also never loaded .env at all. The result was that setting LOCAL_TIMEZONE or
any PWKM_* variable in .env silently did nothing: no error, no warning, just
the default value.

Every script therefore calls load_env() at the top of the module, before its
first os.environ read.

Precedence
----------
The real process environment wins. Values from .env are only applied to keys
that are not already set, so an explicit environment variable, a CI secret, or
a per-invocation override always beats the file. This matches the behaviour of
python-dotenv's default (override=False), so scripts that also call
load_dotenv() later stay consistent with this one.

Dependencies
------------
None. This module deliberately uses only the standard library, so the scripts
that do not otherwise need python-dotenv do not acquire a dependency on it.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

__all__ = ["load_env", "env_path"]

_QUOTES = ("'", '"')


def env_path(start: Optional[Path] = None) -> Path:
    """Return the expected .env path: beside this module, i.e. the scripts dir."""
    base = Path(start) if start is not None else Path(__file__).resolve().parent
    return base / ".env"


def _strip_inline_comment(value: str) -> str:
    """Drop an unquoted trailing comment, e.g. 'America/Toronto  # my tz'."""
    if not value or value[0] in _QUOTES:
        return value
    marker = value.find(" #")
    if marker == -1:
        return value
    return value[:marker]


def load_env(path: Optional[Path] = None) -> Dict[str, str]:
    """
    Read KEY=VALUE pairs from .env into os.environ without overriding existing
    values. Returns the mapping that was parsed from the file, whether or not
    each key was actually applied.

    A missing .env is not an error. Scripts that genuinely require a value are
    responsible for saying so themselves, with a message specific to what they
    need. Absence of the file is a normal state for a setup that supplies its
    configuration through the real environment.
    """
    target = Path(path) if path is not None else env_path()
    parsed: Dict[str, str] = {}

    if not target.exists():
        return parsed

    # utf-8-sig, not utf-8: several Windows editors and PowerShell's own
    # redirection write a byte-order mark by default. Reading as plain utf-8
    # succeeds on such a file but silently folds the BOM into the first key
    # name, so LOCAL_TIMEZONE becomes "\ufeffLOCAL_TIMEZONE" and never matches.
    # utf-8-sig strips a BOM when present and is a no-op when it is not.
    try:
        raw_text = target.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        raw_text = target.read_text(encoding="utf-8-sig", errors="replace")

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue

        value = _strip_inline_comment(value.strip()).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in _QUOTES:
            value = value[1:-1]

        parsed[key] = value
        os.environ.setdefault(key, value)

    return parsed


if __name__ == "__main__":
    import json
    import sys

    found = env_path()
    values = load_env()
    print(json.dumps({
        "env_file": str(found),
        "exists": found.exists(),
        "keys_parsed": sorted(values),
    }, indent=2))
    sys.exit(0)