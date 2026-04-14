import os                                       # to interacrt w environment variables
from dotenv import load_dotenv                  # load variables from .env

# load env variables
load_dotenv()

# get api key from env variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# set timezone
TIMEZONE = "America/Phoenix"