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
        "function": {
            "name": "create_event",
            "description": "Create a calendar event",
            "parameters": {
                "type": "object",
                "properties": {
                    # event title
                    "title": {"type": "string"},
                    # start date/time in ISO format
                    "start_iso": {"type": "string"},
                    # end date/time in ISO format
                    "end_iso": {"type": "string"},
                },
                # 3 required fields requred if create_event is called
                "required": ["title", "start_iso", "end_iso"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_events",
            "description": "List upcoming events",
            "parameters": {
                "type": "object",
                "properties": {}
            },
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
            # give the agent its instructions
            {"role": "system", "content": SYSTEM_PROMPT},

            # give the users actual message
            {"role": "user", "content": user_input}
        ],
        tools=TOOLS,
    )

    # loot thru to check ehat the agent decided to do
    for item in response.output:
        if item.type == "tool_call":
            # get name of the function the agent wants to call
            name = item.function.name


            if isinstance(item.function.arguments, str):
                # convert into dictionary
                args = json.loads(item.function.arguments)
            else:
                args = item.function.arguments

            if name == "create_event":
                return create_event(**args)

            if name == "list_events":
                return list_events()

    return response.output_text