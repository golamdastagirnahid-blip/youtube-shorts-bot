import os
import json
import sys
import random
import tempfile
import smtplib
import hashlib
import urllib.request
import urllib.parse
from email.mime.text import MIMEText
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from groq import Groq

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


# ============================================
# ALERTS: EMAIL + TELEGRAM
# ============================================
def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        text = urllib.parse.quote(message)
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={text}&parse_mode=Markdown"
        urllib.request.urlopen(url)
        print("Telegram alert sent")
    except Exception as e:
        print(f"Telegram alert failed: {e}")


def send_alert(subject, message):
    if ALERT_EMAIL and ALERT_APP_PASSWORD:
        try:
            msg = MIMEText(message)
            msg['Subject'] = f"YouTube Bot: {subject}"
            msg['From'] = ALERT_EMAIL
            msg['To'] = ALERT_EMAIL
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(ALERT_EMAIL, ALERT_APP_PASSWORD)
            server.send_message(msg)
            server.quit()
            print(f"Email alert sent: {subject}")
        except Exception as e:
            print(f"Email alert failed: {e}")

    send_telegram(f"*{subject}*\n\n{message}")


# ============================================
# ANTI SHADOW BAN SYSTEM
# ============================================
HASHTAG_POOLS = [
    ["shorts", "viral", "trending", "fyp", "explore"],
    ["shorts", "viralvideo", "trend", "foryou", "discover"],
    ["shortvideo", "viral", "trending2024", "fypage", "recommended"],
    ["shorts", "viralshorts", "trendingshorts", "fypシ", "mustwatch"],
    ["ytshorts", "viral", "trending", "foryoupage", "entertainment"],
]

DESCRIPTION_TEMPLATES = [
    "🔥 Watch till the end!\n\nLike & Subscribe for more! 👍\n\n{hashtags}",
    "😱 You won't believe this!\n\nSubscribe for daily content! 🔔\n\n{hashtags}",
    "💯 This is amazing!\n\nDrop a ❤️ if you agree!\n\n{hashtags}",
    "⚡ Wait for it...\n\nFollow for more! 🚀\n\n{hashtags}",
    "🎯 Don't miss this!\n\nShare with friends! 🔄\n\n{hashtags}",
    "👀 Watch this!\n\nNew content daily! ✨\n\n{hashtags}",
    "🤯 Mind blowing!\n\nTap ❤️ and Subscribe! 🔔\n\n{hashtags}",
]

TITLE_STYLES = [
    "catchy and curiosity-driven with emoji",
    "shocking and surprising with emoji",
    "question-based that makes people curious",
    "bold statement that creates debate",
    "emotional and relatable with emoji",
    "funny and entertaining with emoji",
    "inspiring and motivational with emoji",
]


def get_anti_ban_config(filename):
    seed = int(hashlib.md5(filename.encode()).hexdigest()[:8], 16)
    random.seed(seed + int(datetime.now().strftime('%Y%m%d')))

    hashtag_set = random.choice(HASHTAG_POOLS)
    description_template = random.choice(DESCRIPTION_TEMPLATES)
    title_style = random.choice(TITLE_STYLES)
    extra_tags = random.sample(["amazing", "wow", "unbelievable", "insane",
                                 "epic", "cool", "awesome", "incredible",
                                 "mindblowing", "satisfying"], 3)
    all_tags = hashtag_set + extra_tags
    hashtags = " ".join([f"#{tag}" for tag in all_tags])
    description = description_template.format(hashtags=hashtags)

    return title_style, description, all_tags


# ============================================
# GOOGLE TRENDS
# ============================================
def get_trending_topics():
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=360)
        trending = pytrends.trending_searches(pn='united_states')
        topics = trending[0].tolist()[:10]
        print(f"Trending topics: {', '.join(topics[:5])}")
        return topics
    except Exception as e:
        print(f"Trends fetch failed: {e}")
        return []


# ============================================
# GOOGLE SHEETS LOGGING
# ============================================
def log_to_sheets(video_name, title, video_url, tags, trending):
    if not SPREADSHEET_ID:
        print("No spreadsheet ID, skipping sheets log")
        return
    try:
        sa_info = json.loads(SERVICE_ACCOUNT_JSON)
        creds = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        sheets = build('sheets', 'v4', credentials=creds)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        trends_used = ', '.join(trending[:3]) if trending else 'None'
        tags_str = ', '.join(tags)

        row = [[now, video_name, title, video_url, tags_str, trends_used, "0", "0", "0"]]

        sheets.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A:I',
            valueInputOption='RAW',
            body={'values': row}
        ).execute()
        print("Logged to Google Sheets")
    except Exception as e:
        print(f"Sheets logging failed: {e}")


# ============================================
# SELF LEARNING - CHECK PAST PERFORMANCE
# ============================================
def get_learning_data():
    if not SPREADSHEET_ID or not SERVICE_ACCOUNT_JSON:
        return ""
    try:
        sa_info = json.loads(SERVICE_ACCOUNT_JSON)
        creds = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        sheets = build('sheets', 'v4', credentials=creds)

        result = sheets.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A:I'
        ).execute()

        rows = result.get('values', [])
        if len(rows) < 3:
            return ""

        data_rows = rows[1:]
        best_videos = sorted(data_rows, key=lambda x: int(x[6]) if len(x) > 6 and x[6].isdigit() else 0, reverse=True)[:3]

        if not best_videos:
            return ""

        learning = "\n\nLEARNING FROM PAST PERFORMANCE:\n"
        learning += "These title styles got the most views:\n"
        for v in best_videos:
            if len(v) > 6:
                learning += f"- Title: {v[2]} (Views: {v[6]})\n"

        print(f"Learning from {len(best_videos)} past videos")
        return learning

    except Exception as e:
        print(f"Learning data fetch failed: {e}")
        return ""


# ============================================
# AI TITLE GENERATION WITH TRENDS + LEARNING
# ============================================
def generate_ai_metadata(filename):
    if not GROQ_API_KEY:
        print("No Groq API key, using filename as title")
        return fallback_metadata(filename)

    try:
        client = Groq(api_key=GROQ_API_KEY)
        clean_name = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')

        title_style, description_base, base_tags = get_anti_ban_config(filename)
        trending = get_trending_topics()
        learning = get_learning_data()

        trends_text = ""
        if trending:
            trends_text = f"\n\nToday's trending topics: {', '.join(trending[:5])}\nIf any trend relates to the video, cleverly include it in the title."

        prompt = f"""You are a YouTube Shorts viral expert.

Video filename: "{clean_name}"
Title style: {title_style}{trends_text}{learning}

Rules for TITLE:
- Style: {title_style}
- Under 80 characters
- Must end with #Shorts
- Make people NEED to click
- Use 1-2 emojis max

Rules for DESCRIPTION:
- 2-3 engaging lines
- Call to action
- Do NOT include hashtags (I add them separately)

Rules for TAGS:
- 5 specific tags related to video content
- Mix broad and niche tags

Respond ONLY in this JSON format:
{{"title": "your title #Shorts", "description": "your description", "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]}}"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=300,
        )

        result = response.choices[0].message.content.strip()

        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()

        metadata = json.loads(result)
        title = metadata.get("title", "")
        ai_description = metadata.get("description", "")
        ai_tags = metadata.get("tags", [])

        if "#Shorts" not in title:
            title = f"{title} #Shorts"
        if len(title) > 100:
            title = title[:97] + "..."

        all_tags = list(set(ai_tags + base_tags))
        hashtags = " ".join([f"#{tag}" for tag in base_tags])
        full_description = f"{ai_description}\n\n{hashtags}"

        print(f"AI Title: {title}")
        print(f"Style: {title_style}")
        print(f"Tags: {', '.join(all_tags)}")
        return title, full_description, all_tags

    except Exception as e:
        print(f"AI generation failed: {e}")
        return fallback_metadata(filename)


def fallback_metadata(filename):
    title = filename.rsplit('.', 1)[0]
    title = title.replace('_', ' ').replace('-', ' ').title()
    if "#Shorts" not in title:
        title = f"{title} #Shorts"
    if len(title) > 100:
        title = title[:97] + "..."
    _, description, tags = get_anti_ban_config(filename)
    return title, description, tags


# ============================================
# CORE SERVICES
# ============================================
def get_drive_service():
    sa_info = json.loads(SERVICE_ACCOUNT_JSON)
    creds = service_account.Credentials.from_service_account_info(
        sa_info,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    service = build('drive', 'v3', credentials=creds)
    print("Drive authenticated")
    return service


def get_youtube_service():
    try:
        creds = Credentials(
            token=None,
            refresh_token=REFRESH_TOKEN,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_uri='https://oauth2.googleapis.com/token',
        )
        creds.refresh(Request())
        service = build('youtube', 'v3', credentials=creds)
        print("YouTube authenticated")
        return service
    except Exception as e:
        error_msg = str(e)
        print(f"YouTube auth FAILED: {error_msg}")
        send_alert(
            "TOKEN EXPIRED - ACTION NEEDED",
            f"YouTube refresh token expired!\n\nError: {error_msg}\n\nFix: Run token code in Colab and update GitHub secret\nTime: {datetime.now()}"
        )
        sys.exit(1)


# ============================================
# DRIVE OPERATIONS
# ============================================
def get_pending_folder_id(drive_service):
    query = (
        f"'{DRIVE_FOLDER_ID}' in parents and "
        f"name = 'pending' and "
        f"mimeType = 'application/vnd.google-apps.folder' and "
        f"trashed = false"
    )
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    folders = results.get('files', [])
    if not folders:
        return None
    return folders[0]['id']


def get_uploaded_folder_id(drive_service):
    query = (
        f"'{DRIVE_FOLDER_ID}' in parents and "
        f"name = 'uploaded' and "
        f"mimeType = 'application/vnd.google-apps.folder' and "
        f"trashed = false"
    )
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    folders = results.get('files', [])
    if not folders:
        folder_metadata = {
            'name': 'uploaded',
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [DRIVE_FOLDER_ID]
        }
        folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
        return folder['id']
    return folders[0]['id']


def get_next_video(drive_service, pending_folder_id):
    query = (
        f"'{pending_folder_id}' in parents and "
        f"trashed = false and "
        f"(mimeType contains 'video/')"
    )
    results = drive_service.files().list(
        q=query,
        fields="files(id, name, size)",
        orderBy="name",
        pageSize=1
    ).execute()
    files = results.get('files', [])
    if not files:
        return None
    return files[0]


def count_pending(drive_service, pending_folder_id):
    query = (
        f"'{pending_folder_id}' in parents and "
        f"trashed = false and "
        f"(mimeType contains 'video/')"
    )
    results = drive_service.files().list(
        q=query,
        fields="files(id)",
        pageSize=1000
    ).execute()
    return len(results.get('files', []))


def download_video(drive_service, file_info):
    request = drive_service.files().get_media(fileId=file_info['id'])
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file_info['name'])
    with open(temp_path, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Downloaded {int(status.progress() * 100)}%")
    print(f"Downloaded: {file_info['name']}")
    return temp_path


def move_to_uploaded(drive_service, file_info, pending_folder_id, uploaded_folder_id):
    drive_service.files().update(
        fileId=file_info['id'],
        addParents=uploaded_folder_id,
        removeParents=pending_folder_id,
        fields='id, parents'
    ).execute()
    print("Moved to uploaded folder")


# ============================================
# YOUTUBE UPLOAD
# ============================================
def upload_to_youtube(youtube_service, video_path, filename):
    title, description, tags = generate_ai_metadata(filename)

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '22',
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False,
        }
    }

    media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True, chunksize=1024*1024)
    request = youtube_service.videos().insert(part='snippet,status', body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    video_id = response['id']
    video_url = f"https://youtube.com/shorts/{video_id}"
    print(f"Uploaded: {video_url}")
    return video_id, video_url, title, tags


# ============================================
# MAIN
# ============================================
def main():
    print(f"Bot started: {datetime.now()}")
    print("=" * 50)

    required = ['YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET', 'YOUTUBE_REFRESH_TOKEN', 'DRIVE_FOLDER_ID', 'GOOGLE_SERVICE_ACCOUNT']
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"Missing: {', '.join(missing)}")
        sys.exit(1)

    drive_service = get_drive_service()
    youtube_service = get_youtube_service()

    pending_folder_id = get_pending_folder_id(drive_service)
    if not pending_folder_id:
        print("No pending folder. Exiting.")
        return

    video_info = get_next_video(drive_service, pending_folder_id)
    if not video_info:
        print("No videos to upload. Exiting.")
        send_alert("No Videos Left", f"Add more videos to Drive pending folder.\nTime: {datetime.now()}")
        return

    remaining = count_pending(drive_service, pending_folder_id)
    print(f"Videos in queue: {remaining}")
    print(f"Next video: {video_info['name']}")

    temp_path = download_video(drive_service, video_info)
    trending = get_trending_topics()

    try:
        video_id, video_url, title, tags = upload_to_youtube(youtube_service, temp_path, video_info['name'])
        uploaded_folder_id = get_uploaded_folder_id(drive_service)
        move_to_uploaded(drive_service, video_info, pending_folder_id, uploaded_folder_id)
        log_to_sheets(video_info['name'], title, video_url, tags, trending)

        print("=" * 50)
        print("SUCCESS!")
        print(f"Title: {title}")
        print(f"URL: {video_url}")
        print(f"Remaining: {remaining - 1}")
        print("=" * 50)

        send_telegram(f"✅ *Uploaded!*\n\n📹 {title}\n🔗 {video_url}\n📊 Remaining: {remaining - 1}")

    except Exception as e:
        error_msg = str(e)
        print(f"Upload failed: {error_msg}")
        send_alert("Upload Failed", f"Video: {video_info['name']}\nError: {error_msg}\nTime: {datetime.now()}")
        sys.exit(1)

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            os.rmdir(os.path.dirname(temp_path))


if __name__ == '__main__':
    main()
