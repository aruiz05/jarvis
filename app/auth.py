import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# define what permissions the app requests
# give access to google calendar
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_credentials():
    creds = None

    # if theres already credentials saves, user logged in before
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)         # load credentials from file

    # if theres no credentials or theyre invalid
    if not creds or not creds.valid:
        # if they exists but theyre expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # if not open browser and let user log in
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # save credentials so user doesnt have to log in again
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds