# ============================================================
# YOUTUBE SHORTS AUTO UPLOADER v4.0 - GOD MODE
# Features: Self-Scheduling, AI Titles, Anti-Ban, Trends, Telegram
# ============================================================

import os
import json
import sys
import random
import tempfile
import smtplib
import hashlib
import urllib.request
import urllib.parse
import base64
import re
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from groq import Groq

# Secrets
CLIENT_ID = os.environ.get('YOUTUBE_CLIENT_ID')
CLIENT_SECRET = os.environ.get('YOUTUBE_CLIENT_SECRET')
REFRESH_TOKEN = os.environ.get('YOUTUBE_REFRESH_TOKEN')
DRIVE_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID')
SERVICE_ACCOUNT_JSON = os.environ.get('GOOGLE_SERVICE_ACCOUNT')
ALERT_EMAIL = os.environ.get('ALERT_EMAIL', '')
ALERT_APP_PASSWORD = os.environ.get('ALERT_APP_PASSWORD', '')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
GH_TOKEN = os.environ.get('GH_TOKEN')

# ============================================================
# SELF-SCHEDULING ENGINE (REWRITES UPLOAD.YML)
# ============================================================
def update_next_schedule():
    if not GH_TOKEN:
        print("⚠️ GH_TOKEN missing. Skipping auto-schedule.")
        return

    try:
        # Calculate random gap: 180 to 240 minutes (3-4 hours)
        random_gap = random.randint(180, 240)
        next_run = datetime.utcnow() + timedelta(minutes=random_gap)
        
        new_cron = f"{next_run.minute} {next_run.hour} * * *"
        
        repo = os.environ.get('GITHUB_REPOSITORY')
        path = ".github/workflows/upload.yml"
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        
        headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}

        # 1. Get current workflow file
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read().decode())
            sha = data['sha']
            content = base64.b64decode(data['content']).decode()

        # 2. Replace ONLY the first cron line found
        updated_content = re.sub(r"cron: '.*'", f"cron: '{new_cron}'", content, count=1)

        # 3. Update GitHub
        update_data = {
            "message": f"🤖 Schedule Update: Next run at {next_run.hour}:{next_run.minute} UTC",
            "content": base64.b64encode(updated_content.encode()).decode(),
            "sha": sha
        }
        
        req_put = urllib.request.Request(url, data=json.dumps(update_data).encode(), headers=headers, method='PUT')
        with urllib.request.urlopen(req_put):
            print(f"✅ Auto-Schedule Set: {new_cron}")
            send_telegram(f"📅 *Next Upload Scheduled*\nTime: `{next_run.hour:02d}:{next_run.minute:02d}` UTC\nGap: {random_gap} minutes")

    except Exception as e:
        print(f"❌ Scheduling failed: {e}")

# ============================================================
# CORE FUNCTIONS (TELEGRAM, AI, DRIVE, YOUTUBE)
# ============================================================

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        text = urllib.parse.quote(message)
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={text}&parse_mode=Markdown"
        urllib.request.urlopen(url, timeout=10)
    except: pass

def send_alert(subject, message):
    if ALERT_EMAIL and ALERT_APP_PASSWORD:
        try:
            msg = MIMEText(message); msg['Subject'] = f"YT Bot: {subject}"; msg['From'] = ALERT_EMAIL; msg['To'] = ALERT_EMAIL
            server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(ALERT_EMAIL, ALERT_APP_PASSWORD)
            server.send_message(msg); server.quit()
        except: pass
    send_telegram(f"⚠️ *{subject}*\n{message}")

def get_trending_topics():
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=360)
        return pytrends.trending_searches(pn='united_states')[0].tolist()[:10]
    except: return []

def generate_ai_metadata(filename):
    client = Groq(api_key=GROQ_API_KEY)
    clean_name = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
    trending = get_trending_topics()
    
    prompt = f"Act as a viral YouTube expert. Filename: {clean_name}. Trends: {trending[:3]}. Create a catchy title under 80 chars ending with #Shorts, a 2-line description, and 5 tags. Respond in JSON format: {{\"title\":\"\", \"description\":\"\", \"tags\":[]}}"
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"}
    )
    res = json.loads(chat_completion.choices[0].message.content)
    return res['title'], res['description'] + "\n\n#shorts #viral", res['tags']

# ============================================================
# GOOGLE & DRIVE HELPERS
# ============================================================

def get_drive_service():
    creds = service_account.Credentials.from_service_account_info(json.loads(SERVICE_ACCOUNT_JSON), scopes=['https://www.googleapis.com/auth/drive'])
    return build('drive', 'v3', credentials=creds)

def get_youtube_service():
    creds = Credentials(None, refresh_token=REFRESH_TOKEN, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, token_uri='https://oauth2.googleapis.com/token')
    creds.refresh(Request())
    return build('youtube', 'v3', credentials=creds)

def main():
    try:
        drive_service = get_drive_service()
        yt_service = get_youtube_service()

        # Find folders
        res = drive_service.files().list(q=f"'{DRIVE_FOLDER_ID}' in parents and name='pending'", fields="files(id)").execute()
        pending_id = res.get('files')[0]['id']
        
        res = drive_service.files().list(q=f"'{DRIVE_FOLDER_ID}' in parents and name='uploaded'", fields="files(id)").execute()
        uploaded_id = res.get('files')[0]['id']

        # Get next video
        res = drive_service.files().list(q=f"'{pending_id}' in parents and trashed=false", fields="files(id, name)", pageSize=1).execute()
        files = res.get('files', [])
        
        if not files:
            send_alert("Empty Folder", "No videos left in pending!")
            return

        video = files[0]
        print(f"Processing: {video['name']}")

        # Download
        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        request = drive_service.files().get_media(fileId=video['id'])
        downloader = MediaIoBaseDownload(temp, request)
        done = False
        while not done: _, done = downloader.next_chunk()
        temp.close()

        # Metadata & Upload
        title, desc, tags = generate_ai_metadata(video['name'])
        
        body = {'snippet': {'title': title, 'description': desc, 'tags': tags, 'categoryId': '22'}, 'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}}
        media = MediaFileUpload(temp.name, mimetype='video/mp4', resumable=True)
        upload = yt_service.videos().insert(part='snippet,status', body=body, media_body=media).execute()

        # Move file
        drive_service.files().update(fileId=video['id'], addParents=uploaded_id, removeParents=pending_id).execute()
        
        print(f"Done! https://youtu.be/{upload['id']}")
        send_telegram(f"✅ *Uploaded*\nTitle: {title}\nURL: https://youtube.com/shorts/{upload['id']}")
        
        # 🔥 THE MAGIC: Update schedule for next time
        update_next_schedule()

    except Exception as e:
        send_alert("Upload Error", str(e))
    finally:
        if 'temp' in locals(): os.unlink(temp.name)

if __name__ == "__main__":
    main()
