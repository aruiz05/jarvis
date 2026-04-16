from openai import OpenAI
from .config import OPENAI_API_KEY
from .calendarTools import create_event, list_events
from .canvas import sync_canvas
from datetime import datetime, timedelta
from app.utils import has_explicit_time, parse_natural_time
import json

client = OpenAI(api_key=OPENAI_API_KEY)

# define the tools the agent is allowed to use
# what functions exist, what each function does, what args each needs
TOOLS = [
    {
        "type": "function",
        "name": "create_event",
        "description": "Create a calendar event",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "start_text": {"type": "string"},
                "end_text": {"type": "string"},
            },
            "required": ["title", "start_text"],
        },
    },
    {
        "type": "function",
        "name": "list_events",
        "description": "List upcoming events",
        "parameters": {
            "type": "object",
            "properties": {}
        },
    },
    {
        "type": "function",
        "name": "sync_canvas",
        "description": "sync canvas assignments into google calendar",
        "parameters": {
            "type": "object",
            "properties": {}
        },
    },
]

# prompt for ai
SYSTEM_PROMPT = """
You are a personal calendar assistant.

Rules:
- If the user wants to schedule something, call create_event
- If the user asks about their schedule, call list_events
- If the user asks to sync assignments or Canvas, call sync_canvas
- Extract a clear event title
- Extract the start time exactly as natural language (e.g., "tomorrow at 5pm")
- DO NOT generate ISO timestamps
- Only include fields that exist in the function schema
- Always return valid arguments
"""

# main function that sends user message to agent
def run_agent(user_input):
    # respond with either -
    # normal text reply
    # call one of the tools
    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        tools=TOOLS,
        tool_choice = "auto"
    )

    # walk through output and see whether it chose to call a tool
    # if there is a tool call, translate the models structured arguments into real function calls
    for item in response.output:
        if item.type == "function_call":
            name = item.name

            # can return tool args as either json string or parsed object, so normalize both cases into a dict
            if isinstance(item.arguments, str):
                args = json.loads(item.arguments)
            else:
                args = item.arguments

            if name == "create_event":
                # if did not provide any time text, stop and ask user for a clearer scheduling
                if "start_text" not in args:
                    return "I couldn't understand the time. Try something like 'tomorrow at 5pm'."
                # only create the event when the user gives a time
                # if given only date like "next wednesday", ask follow up
                if not has_explicit_time(args["start_text"]):
                    title = args.get("title", "that")
                    return f"What time should I schedule {title}?"
                # convert natural language into a concrete time then default the length to one hour
                start_iso = parse_natural_time(args["start_text"])

                start_dt = datetime.fromisoformat(start_iso)
                end_iso = (start_dt + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")

                # once the times are ready, call the google calendar helper and return its confirmation message
                return create_event(
                    title=args["title"],
                    start_iso=start_iso,
                    end_iso=end_iso
                )

            if name == "list_events":
                return list_events()

            if name == "sync_canvas":
                return sync_canvas()

    return response.output_text or "No response from agent"
