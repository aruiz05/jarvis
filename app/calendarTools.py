from googleapiclient.discovery import build
from datetime import datetime
from .auth import get_credentials
from .config import TIMEZONE


# create and return google calendar object
def get_service():
    creds = get_credentials()
    return build("calendar", "v3", credentials=creds)

# list upcoming events from calendar
def list_events():
    service = get_service()
    # get current time in utc
    now = datetime.utcnow().isoformat() + "Z"

    # call google calendar api to fetch events
    events = service.events().list(
        calendarId="primary",       # main calendar
        timeMin=now,                # only events after current time
        maxResults=10,              # limit to 10 events
        singleEvents=True,          # expand recurring events
        orderBy="startTime"         # sort by start time
    ).execute()

    # return a simplified list of events
    return [
        {
            "title": e.get("summary"),
            "start": e["start"].get("dateTime", e["start"].get("date"))
        }
        for e in events.get("items", [])
    ]

# delete the first upcoming event that matches the title
def delete_event(title: str):
    service = get_service()
    now = datetime.utcnow().isoformat() + "Z"

    # get upcoming events from the primary calendar
    events = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=50,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    # find the first title match
    for e in events.get("items", []):
        if e.get("summary", "").lower() == title.lower():
            service.events().delete(
                calendarId="primary",
                eventId=e["id"]
            ).execute()
            return f"Deleted event: {title}"

    return f"No event found with title: {title}"

# create new calendar event
def create_event(title, start_iso, end_iso):
    service = get_service()

    # build event object how google expects
    event = {
        "summary": title,       # event name

        "start": {"dateTime": start_iso, "timeZone": TIMEZONE},     # start time w timezone
        "end": {"dateTime": end_iso, "timeZone": TIMEZONE},         # end time w timezone
    }

    # rend request to google calendar to create event
    created = service.events().insert(
        calendarId="primary",
        body=event
    ).execute()

    # return confirmation details
    return {
        "status": "created",
        "title": title,
        "link": created.get("htmlLink")
    }
