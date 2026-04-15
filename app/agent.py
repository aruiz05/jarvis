from openai import OpenAI
from .config import OPENAI_API_KEY
from .calendarTools import create_event, list_events
from datetime import datetime, timedelta
from app.utils import parse_natural_time
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
]

# prompt for ai
SYSTEM_PROMPT = """
You are a personal calendar assistant.

Rules:
- If the user wants to schedule something, call create_event
- If the user asks about their schedule, call list_events
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

    # loot thru to check ehat the agent decided to do
    for item in response.output:
        if item.type == "function_call":
            name = item.name

            if isinstance(item.arguments, str):
                args = json.loads(item.arguments)
            else:
                args = item.arguments

            if name == "create_event":
                if "start_text" not in args:
                    return "I couldn't understand the time. Try something like 'tomorrow at 5pm'."
                start_iso = parse_natural_time(args["start_text"])

                start_dt = datetime.fromisoformat(start_iso)
                end_iso = (start_dt + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")

                return create_event(
                    title=args["title"],
                    start_iso=start_iso,
                    end_iso=end_iso
                )

            if name == "list_events":
                return list_events()

    return response.output_text or "No response from agent"