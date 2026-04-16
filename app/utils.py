from datetime import datetime, timedelta
from dateutil import parser
import difflib
import re

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

TIME_PATTERNS = [
    r"\b\d{1,2}:\d{2}\s*(am|pm)?\b",
    r"\b\d{1,2}\s*(am|pm)\b",
    r"\b(noon|midnight)\b",
    r"\b(morning|afternoon|evening|tonight)\b",
    r"\bin \d+\s+(minutes?|hours?)\b",
]


def _normalize_weekday_typos(text: str) -> str:
    parts = text.split()
    normalized = []

    for part in parts:
        cleaned = re.sub(r"[^a-z]", "", part)
        if cleaned:
            match = difflib.get_close_matches(cleaned, WEEKDAYS.keys(), n=1, cutoff=0.75)
            if match:
                suffix = part[len(cleaned):] if part.startswith(cleaned) else ""
                normalized.append(match[0] + suffix)
                continue
        normalized.append(part)

    return " ".join(normalized)


def _parse_with_base(text: str, base: datetime) -> datetime:
    normalized_base = base.replace(hour=0, minute=0, second=0, microsecond=0)
    return parser.parse(text, default=normalized_base)


def has_explicit_time(text: str) -> bool:
    text = _normalize_weekday_typos(text.lower().strip())
    return any(re.search(pattern, text) for pattern in TIME_PATTERNS)


def parse_natural_time(text: str) -> str:
    text = _normalize_weekday_typos(text.lower().strip())
    now = datetime.now()

    # "in X hours"
    match = re.search(r"in (\d+) hours?", text)
    if match:
        hours = int(match.group(1))
        dt = now + timedelta(hours=hours)
        return dt.strftime("%Y-%m-%dT%H:%M:%S")

    # "tomorrow"
    if "tomorrow" in text:
        base = now + timedelta(days=1)
        text = text.replace("tomorrow", "").strip()
        if not text:
            return base.strftime("%Y-%m-%dT%H:%M:%S")
        dt = _parse_with_base(text, base)
        return dt.strftime("%Y-%m-%dT%H:%M:%S")

    # "today"
    if "today" in text:
        text = text.replace("today", "").strip()
        if not text:
            return now.strftime("%Y-%m-%dT%H:%M:%S")
        dt = _parse_with_base(text, now)
        return dt.strftime("%Y-%m-%dT%H:%M:%S")

    # "next <weekday>"
    for day in WEEKDAYS:
        if f"next {day}" in text:
            target = WEEKDAYS[day]
            # "next Wednesday" should mean the Wednesday in the following week,
            # not the nearest upcoming Wednesday.
            days_ahead = (target - now.weekday() + 7) % 7 + 7
            base = now + timedelta(days=days_ahead)

            text = text.replace(f"next {day}", "").strip()
            if not text:
                return base.strftime("%Y-%m-%dT%H:%M:%S")
            dt = _parse_with_base(text, base)
            return dt.strftime("%Y-%m-%dT%H:%M:%S")

    # fallback
    dt = _parse_with_base(text, now)
    return dt.strftime("%Y-%m-%dT%H:%M:%S")
