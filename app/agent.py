from openai import OpenAI
from .config import OPENAI_API_KEY
from .calendarTools import create_event, list_events
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
                "start_iso": {"type": "string"},
                "end_iso": {"type": "string"},
            },
            "required": ["title", "start_iso", "end_iso"],
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
- If the user asks about schedule, call list_events
- Always return valid arguments
- Use ISO datetime format: YYYY-MM-DDTHH:MM:SS
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
            # get name of the function the agent wants to call
            name = item.name


            if isinstance(item.arguments, str):
                # convert into dictionary
                args = json.loads(item.arguments)
            else:
                args = item.arguments

            if name == "create_event":
                return create_event(**args)

            if name == "list_events":
                return list_events()

    return response.output_text