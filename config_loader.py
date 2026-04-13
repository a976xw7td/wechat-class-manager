#!/usr/bin/env python3
"""
config_loader.py - Single source of truth for all configuration.

Reads challenges.yaml and group_config.yaml and exposes a clean API
so no other module needs to hardcode challenge IDs, names, keywords,
deadlines, or group metadata.

Usage:
    from config_loader import get_config
    cfg = get_config()
    cfg.challenge_keywords   # {id: [keywords]}
    cfg.group_display_name   # "AI+X Elite Class"
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

# Config files live here regardless of which script imports this module
_CONFIG_DIR = Path(__file__).parent / "wechat-class-manager" / "config"


# ---------------------------------------------------------------------------
# YAML loader (with pure-Python fallback if pyyaml not installed)
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    if _HAS_YAML:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    # Minimal fallback: only handles simple key: value lines (not nested)
    result: dict = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip().strip('"').strip("'")
        if key.strip() and val:
            result[key.strip()] = val
    return result


# ---------------------------------------------------------------------------
# AppConfig
# ---------------------------------------------------------------------------

class AppConfig:
    """Parsed, ready-to-use configuration."""

    def __init__(self, challenges: list[dict], group: dict, alerts: dict):
        self._challenges = challenges
        self._group = group
        self._alerts = alerts

    # ---- Challenge helpers ------------------------------------------------

    @property
    def challenges(self) -> list[dict]:
        """Full challenge list as loaded from YAML."""
        return self._challenges

    @property
    def challenge_ids(self) -> list[str]:
        return [c["id"] for c in self._challenges]

    @property
    def challenge_map(self) -> dict[str, dict]:
        """id → challenge dict"""
        return {c["id"]: c for c in self._challenges}

    @property
    def challenge_list(self) -> list[tuple[str, str]]:
        """[(id, name_cn), ...] — for dashboard and reports."""
        return [(c["id"], c.get("name_cn", c["id"])) for c in self._challenges]

    @property
    def challenge_keywords(self) -> dict[str, list[str]]:
        """id → [keyword, ...] — for challenge_linker."""
        return {c["id"]: c.get("keywords", []) for c in self._challenges}

    @property
    def challenges_with_deadlines(self) -> dict[str, str]:
        """id → 'YYYY-MM-DD' for challenges that have a due_date."""
        return {
            c["id"]: c["due_date"]
            for c in self._challenges
            if c.get("due_date")
        }

    @property
    def challenge_ref_pattern(self) -> str:
        """
        Regex pattern that matches any challenge ID in message text.
        Derived from actual IDs so it works for non-C1-C8 schemes too.
        e.g. ids=["C1".."C8"] → r"\bC[1-8][A-Z]?\b"
             ids=["T01","T02"] → r"\b(T01|T02)\b"
        """
        ids = self.challenge_ids
        if not ids:
            return r"\b[A-Z]\d+[A-Z]?\b"

        import re as _re

        # Find the common letter prefix (e.g. "C" from C1..C8)
        prefix_match = _re.match(r"^([A-Za-z]+)", ids[0])
        if prefix_match:
            prefix = prefix_match.group(1)
            # Check all ids share the same prefix
            if all(c.startswith(prefix) for c in ids):
                suffixes = [c[len(prefix):] for c in ids]
                digits = [s[0] for s in suffixes if s and s[0].isdigit()]
                if len(digits) == len(suffixes):
                    mn, mx = min(digits), max(digits)
                    has_letter = any(len(s) > 1 for s in suffixes)
                    letter_part = "[A-Z]?" if has_letter else ""
                    return rf"\b{prefix}[{mn}-{mx}]{letter_part}\b"

        # Fallback: literal alternation of all IDs
        alt = "|".join(_re.escape(i) for i in ids)
        return rf"\b({alt})\b"

    # ---- Group helpers ----------------------------------------------------

    @property
    def group_name(self) -> str:
        """WeChat group name for wechat-cli."""
        return self._group.get("name", "My Group")

    @property
    def group_display_name(self) -> str:
        """Human-readable name for dashboard titles and reports."""
        return self._group.get("display_name", self.group_name)

    @property
    def teacher_ids(self) -> list[str]:
        return self._group.get("teacher_ids", [])

    @property
    def ta_ids(self) -> list[str]:
        return self._group.get("ta_ids", [])

    # ---- Alert thresholds -------------------------------------------------

    @property
    def deadline_warning_days(self) -> int:
        return int(self._alerts.get("deadline_warning_days", 3))

    @property
    def silent_days(self) -> int:
        return int(self._alerts.get("silent_days", 7))

    @property
    def low_submission_threshold(self) -> float:
        return float(self._alerts.get("low_submission_threshold", 0.30))


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

_cache: AppConfig | None = None


def get_config(config_dir: Path | None = None) -> AppConfig:
    """
    Load and cache AppConfig. Pass config_dir to override default location.
    Subsequent calls return the cached instance.
    """
    global _cache
    if _cache is not None and config_dir is None:
        return _cache

    cdir = config_dir or _CONFIG_DIR

    raw_challenges = _load_yaml(cdir / "challenges.yaml")
    raw_group = _load_yaml(cdir / "group_config.yaml")

    challenges: list[dict] = raw_challenges.get("challenges", [])
    group: dict = raw_group.get("group", {})
    alerts: dict = raw_group.get("alerts", {})

    cfg = AppConfig(challenges, group, alerts)
    if config_dir is None:
        _cache = cfg
    return cfg


def reload_config() -> AppConfig:
    """Force reload from disk (clears cache)."""
    global _cache
    _cache = None
    return get_config()
