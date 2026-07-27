#!/usr/bin/env python3
"""Shared deterministic helpers for eBay price research."""

from __future__ import annotations

import datetime as dt
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import quote_plus, urlsplit, urlunsplit


MARKETPLACE_HOSTS = {
    "ebay.com": "www.ebay.com",
    "ebay.ca": "www.ebay.ca",
    "ebay.co.uk": "www.ebay.co.uk",
    "ebay.de": "www.ebay.de",
    "ebay.com.au": "www.ebay.com.au",
}
ALLOWED_ITEM_HOSTS = set(MARKETPLACE_HOSTS.values())
UNKNOWN_VALUES = {"", "unknown", "未知", "不详", "null", "none", "-"}
MONEY_RE = re.compile(r"^\d+(?:\.\d{1,2})?$")
ITEM_PATH_RE = re.compile(r"^/(?:itm/(?:[^/]+/)?|p/)?(\d{9,15})(?:/|$)")


def normalized_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def parse_money(value: Any) -> Decimal | None:
    if not isinstance(value, str):
        return None
    cleaned = unicodedata.normalize("NFKC", value).strip().replace(",", "")
    if normalized_text(cleaned) in UNKNOWN_VALUES:
        return None
    cleaned = re.sub(r"^(?:US|C|AU)?[$£€]\s*", "", cleaned, flags=re.IGNORECASE)
    if not MONEY_RE.fullmatch(cleaned):
        return None
    try:
        number = Decimal(cleaned)
    except InvalidOperation:
        return None
    return number if number >= 0 else None


def format_money(value: Decimal | None) -> str:
    if value is None:
        return "unknown"
    return format(value.quantize(Decimal("0.01")), "f")


def item_id_from_url(raw: Any) -> str | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        parsed = urlsplit(raw.strip())
    except ValueError:
        return None
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in ALLOWED_ITEM_HOSTS:
        return None
    match = ITEM_PATH_RE.match(re.sub(r"/+", "/", parsed.path or "/"))
    return match.group(1) if match else None


def canonical_item_url(raw: Any, item_id: Any = None) -> str | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        parsed = urlsplit(raw.strip())
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in ALLOWED_ITEM_HOSTS:
        return None
    identifier = str(item_id) if item_id is not None else item_id_from_url(raw)
    if not re.fullmatch(r"\d{9,15}", identifier or ""):
        return None
    return urlunsplit(("https", host, f"/itm/{identifier}", "", ""))


def official_search_url(marketplace: str, query: str, sort_mode: str = "best-match") -> str:
    host = MARKETPLACE_HOSTS.get(marketplace)
    if host is None:
        raise ValueError("unsupported eBay marketplace")
    sort_values = {
        "best-match": "12",
        "price-plus-shipping-ascending": "15",
        "newly-listed": "10",
    }
    return f"https://{host}/sch/i.html?_nkw={quote_plus(query)}&_sop={sort_values.get(sort_mode, '12')}"


def parse_aware_time(value: Any) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def time_is_fresh(value: Any, *, hours: int = 24) -> bool:
    parsed = parse_aware_time(value)
    if parsed is None:
        return False
    age = dt.datetime.now(dt.timezone.utc) - parsed.astimezone(dt.timezone.utc)
    return -dt.timedelta(minutes=5) <= age <= dt.timedelta(hours=hours)


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value
