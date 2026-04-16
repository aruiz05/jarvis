import json
import os
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from ics import Calendar

from .calendarTools import create_event
from .config import TIMEZONE


# load environment variables
load_dotenv()

# read the canvas feed URL and file path
CANVAS_ICAL_URL = os.getenv("CANVAS_ICAL_URL")
SEEN_EVENTS_FILE = "seen_events.json"


def load_seen():
    # start with an empty list if the file doesnt exist yet
    if not os.path.exists(SEEN_EVENTS_FILE):
        return []

    try:
        # load the list of event UIDs that were already imported
        with open(SEEN_EVENTS_FILE, "r") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        # treat broken or unreadable files as empty state
        return []

    if isinstance(data, list):
        return data

    # ignore unexpected file contents
    return []


def save_seen(seen_uids):
    try:
        # save the updated UID list after syncing
        with open(SEEN_EVENTS_FILE, "w") as file:
            json.dump(seen_uids, file, indent=2)
    except OSError:
        return False

    return True


def normalize_canvas_time(event_begin, local_timezone):
    # treat midnight UTC assignment events as canvas due date placeholders
    if event_begin.tzinfo == timezone.utc and event_begin.time() == time(0, 0):
        return datetime.combine(
            event_begin.date(),
            time(23, 59),
            tzinfo=local_timezone
        )

    # else use the actual event time converted to the local timezone
    return event_begin.astimezone(local_timezone)


def sync_canvas():
    # stop early if the canvas ICS URL is missing
    if not CANVAS_ICAL_URL:
        return "Canvas iCal URL is not configured"

    try:
        # download the latest ICS feed from canvas
        response = requests.get(CANVAS_ICAL_URL, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        return f"Failed to fetch Canvas calendar: {exc}"

    try:
        # parse the ICS text into calendar events
        calendar = Calendar(response.text)
    except Exception as exc:
        return f"Failed to parse Canvas calendar: {exc}"

    # track current time and previously imported event IDs
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    local_timezone = ZoneInfo(TIMEZONE)
    seen_uids = set(load_seen())
    added_count = 0

    for event in calendar.events:
        # skip events with no UID or events already synced before
        uid = getattr(event, "uid", None)
        if not uid or uid in seen_uids:
            continue

        # normalize event start time so it can be compared
        event_begin = event.begin.datetime
        if event_begin.tzinfo is None:
            event_begin = event_begin.replace(tzinfo=timezone.utc)

        # ignore events that already happened
        if event_begin <= now:
            continue

        try:
            # convert the event time into the local timezone before saving
            local_begin = normalize_canvas_time(event_begin, local_timezone)

            # create the event in google calendar
            create_event(
                title=event.name,
                start_iso=local_begin.isoformat(),
                end_iso=local_begin.isoformat()
            )
        except Exception as exc:
            return f"Failed to create Canvas event '{event.name}': {exc}"

        # mark the event as seen after import
        seen_uids.add(uid)
        added_count += 1

    # save the updated UID list for the next sync run
    if not save_seen(sorted(seen_uids)):
        return "Failed to save seen Canvas events"

    # return a short summary of the sync result
    return f"Added {added_count} new events from Canvas"
