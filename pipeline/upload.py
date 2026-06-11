"""Step 6 — Upload to YouTube (Data API v3).

One-time setup:
  1. In Google Cloud Console, create OAuth 2.0 Desktop credentials,
     download the JSON to state/yt_client_secret.json.
  2. Run `python -m pipeline.upload` once locally to do the browser
     consent flow; it writes state/yt_token.json (a refresh token).
  3. After that, runs are headless (works in cron / GitHub Actions
     if you commit the token securely or store it as a secret).
"""
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import config

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _service():
    creds = None
    try:
        creds = Credentials.from_authorized_user_file(config.YOUTUBE_TOKEN_FILE, SCOPES)
    except FileNotFoundError:
        pass
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.YOUTUBE_CLIENT_SECRET_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(config.YOUTUBE_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload(video_path, script):
    youtube = _service()
    tags = script.get("hashtags", [])
    # #Shorts in the title/description helps YouTube classify it as a Short
    title = f"{script['title']} #Shorts"
    desc = script.get("description", "") + "\n\n" + " ".join(f"#{t}" for t in tags)

    body = {
        "snippet": {
            "title": title[:100],
            "description": desc[:4900],
            "tags": tags,
            "categoryId": config.YT_CATEGORY_ID,
        },
        "status": {"privacyStatus": config.YT_PRIVACY, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = req.execute()
    return resp["id"]


if __name__ == "__main__":
    # Run once to authorize.
    _service()
    print("Authorized. Token saved to", config.YOUTUBE_TOKEN_FILE)
