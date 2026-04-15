from datetime import datetime, timedelta
from dateutil import parser
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

def parse_natural_time(text: str) -> str:
    text = text.lower().strip()
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
        dt = parser.parse(text, default=base)
        return dt.strftime("%Y-%m-%dT%H:%M:%S")

    # "today"
    if "today" in text:
        text = text.replace("today", "").strip()
        dt = parser.parse(text, default=now)
        return dt.strftime("%Y-%m-%dT%H:%M:%S")

    # "next <weekday>"
    for day in WEEKDAYS:
        if f"next {day}" in text:
            target = WEEKDAYS[day]
            days_ahead = (target - now.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            base = now + timedelta(days=days_ahead)

            text = text.replace(f"next {day}", "").strip()
            dt = parser.parse(text, default=base)
            return dt.strftime("%Y-%m-%dT%H:%M:%S")

    # fallback
    dt = parser.parse(text, default=now)
    return dt.strftime("%Y-%m-%dT%H:%M:%S")