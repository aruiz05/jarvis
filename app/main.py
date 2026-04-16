from fastapi import FastAPI
from pydantic import BaseModel
from .agent import run_agent
from .config import OPENAI_API_KEY
from app.calendarTools import list_events
from app.canvas import sync_canvas

# create instance
app = FastAPI()

# make sure user enters a string
class ChatRequest(BaseModel):
    message: str

# test route to check if server is runnung
# visit local host
@app.get("/")
def root():
    return {"status": "running"}

# main endpoint
@app.post("/chat")
def chat(req: ChatRequest):
    # take message from request and pass to agent
    result = run_agent(req.message)
    return {"response": result}

# event endpoiny
@app.get("/events")
def get_events():
    return list_events()


# sync canvas endpoint
@app.post("/sync-canvas")
def run_canvas_sync():
    return sync_canvas()

