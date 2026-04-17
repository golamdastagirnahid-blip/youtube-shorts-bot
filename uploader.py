# ============================================================
# YOUTUBE SHORTS AUTO UPLOADER v4.0 - GOD MODE
# Features:
# ✅ Self-Scheduling (Rewrites own cron)
# ✅ AI Titles (Llama 3.3 70B)
# ✅ Google Trends Integration
# ✅ Anti Shadow Ban System
# ✅ Self Learning AI
# ✅ Google Sheets Logging
# ✅ Professional Telegram Reports
# ✅ Email Alerts
# ✅ Auto Retry on Failure
# ✅ Video Duplicate Checker
# ✅ Auto Category Detection
# ✅ Competitor Title Spy
# ✅ Human-like Scheduling
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
import time
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from groq import Groq


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================
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
# YOUTUBE CATEGORY MAP
# ============================================================
CATEGORY_MAP = {
    "film": "1", "animation": "1", "movie": "1",
    "car": "2", "vehicle": "2", "driving": "2",
    "music": "10", "song": "10", "singing": "10", "dance": "10",
    "pet": "15", "animal": "15", "dog": "15", "cat": "15",
    "wildlife": "15", "nature": "15",
    "sport": "17", "fitness": "17", "gym": "17", "workout": "17",
    "football": "17", "basketball": "17", "soccer": "17", "cricket": "17",
    "travel": "19", "village": "19", "city": "19", "tourism": "19",
    "destination": "19", "landscape": "19", "monsoon": "19",
    "gaming": "20", "game": "20", "minecraft": "20", "fortnite": "20",
    "vlog": "22", "blog": "22", "daily": "22", "lifestyle": "22",
    "comedy": "23", "funny": "23", "humor": "23", "meme": "23",
    "entertainment": "24", "challenge": "24", "reaction": "24",
    "news": "25", "politics": "25",
    "howto": "26", "tutorial": "26", "diy": "26", "tips": "26",
    "hack": "26", "food": "26", "cooking": "26", "recipe": "26",
    "fashion": "26", "beauty": "26", "makeup": "26",
    "education": "27", "science": "27", "history": "27", "fact": "27",
    "tech": "28", "technology": "28", "phone": "28", "computer": "28",
    "ai": "28", "robot": "28",
    "motivation": "22", "inspire": "22", "success": "22",
    "horror": "1", "scary": "1", "ghost": "1",
    "asmr": "22", "satisfying": "22", "relaxing": "22",
    "highland": "19", "scottish": "19", "medieval": "19",
    "riverside": "19", "mountain": "19", "forest": "19",
}

CATEGORY_NAMES = {
    "1": "Film & Animation", "2": "Autos & Vehicles",
    "10": "Music", "15": "Pets & Animals",
    "17": "Sports", "19": "Travel & Events",
    "20": "Gaming", "22": "People & Blogs",
    "23": "Comedy", "24": "Entertainment",
    "25": "News & Politics", "26": "Howto & Style",
    "27": "Education", "28": "Science & Technology",
}


# ============================================================
# ANTI SHADOW BAN CONFIG
# ============================================================
HASHTAG_POOLS = [
    ["shorts", "viral", "trending", "fyp", "explore"],
    ["shorts", "viralvideo", "trend", "foryou", "discover"],
    ["shortvideo", "viral", "trending2024", "fypage", "recommended"],
    ["shorts", "viralshorts", "trendingshorts", "fypシ", "mustwatch"],
    ["ytshorts", "viral", "trending", "foryoupage", "entertainment"],
    ["shorts", "viralcontent", "trending", "foryoupageシ", "watchthis"],
    ["shortsvideo", "viral", "trendingnow", "fyp", "videooftheday"],
]

DESCRIPTION_TEMPLATES = [
    "🔥 Watch till the end!\n\nLike & Subscribe for more! 👍\n\n{hashtags}",
    "😱 You won't believe this!\n\nSubscribe for daily content! 🔔\n\n{hashtags}",
    "💯 This is amazing!\n\nDrop a ❤️ if you agree!\n\n{hashtags}",
    "⚡ Wait for it...\n\nFollow for more! 🚀\n\n{hashtags}",
    "🎯 Don't miss this!\n\nShare with friends! 🔄\n\n{hashtags}",
    "👀 Watch this!\n\nNew content daily! ✨\n\n{hashtags}",
    "🤯 Mind blowing!\n\nTap ❤️ and Subscribe! 🔔\n\n{hashtags}",
    "🌟 This made my day!\n\nDouble tap if you loved it! ❤️\n\n{hashtags}",
    "🎬 Best video today!\n\nSave this for later! 🔖\n\n{hashtags}",
    "💥 Incredible!\n\nTag someone who needs to see this! 👇\n\n{hashtags}",
]

TITLE_STYLES = [
    "catchy and curiosity-driven with emoji",
    "shocking and surprising with emoji",
    "question-based that makes people curious",
    "bold statement that creates debate",
    "emotional and relatable with emoji",
    "funny and entertaining with emoji",
    "inspiring and motivational with emoji",
    "mysterious and intriguing with emoji",
    "educational but exciting with emoji",
    "storytelling hook that draws people in",
]


# ============================================================
# TELEGRAM - BASIC SENDER
# ============================================================
def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        text = urllib.parse.quote(message)
        url = (
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
            f"/sendMessage?chat_id={TELEGRAM_CHAT_ID}"
            f"&text={text}&parse_mode=Markdown"
            f"&disable_web_page_preview=false"
        )
        urllib.request.urlopen(url, timeout=10)
        print("✅ Telegram sent")
    except Exception as e:
        print(f"Telegram failed: {e}")


# ============================================================
# TELEGRAM - PROFESSIONAL REPORT
# ============================================================
def send_telegram_report(
    status,
    video_name="",
    title="",
    video_url="",
    category="",
    tags=None,
    remaining=0,
    trending=None,
    next_schedule="",
    upload_time=0,
    file_size_mb=0,
):
    if tags is None:
        tags = []
    if trending is None:
        trending = []

    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

    if status == "success":
        tag_list = " ".join([f"#{t}" for t in tags[:5]])
        trend_list = ", ".join(trending[:3]) if trending else "None detected"
        total_indicator = (
            "🟢" if remaining > 10
            else "🟡" if remaining > 3
            else "🔴"
        )
        days_left = remaining // 6

        message = (
            f"╔══════════════════════════╗\n"
            f"║  ✅ UPLOAD SUCCESSFUL     ║\n"
            f"╚══════════════════════════╝\n\n"
            f"📹 *VIDEO DETAILS*\n"
            f"┣ File: `{video_name[:35]}`\n"
            f"┣ Size: `{file_size_mb:.1f} MB`\n"
            f"┣ Category: `{category}`\n"
            f"┗ Upload Time: `{upload_time:.1f} sec`\n\n"
            f"📝 *AI GENERATED TITLE*\n"
            f"┗ {title}\n\n"
            f"🏷️ *TAGS USED*\n"
            f"┗ {tag_list}\n\n"
            f"📈 *TRENDS MATCHED*\n"
            f"┗ `{trend_list}`\n\n"
            f"🔗 *YOUTUBE URL*\n"
            f"┗ {video_url}\n\n"
            f"📊 *QUEUE STATUS*\n"
            f"┣ {total_indicator} Remaining: `{remaining} videos`\n"
            f"┣ Est. Days Left: `{days_left} days`\n"
            f"┗ Next Upload: `{next_schedule} UTC`\n\n"
            f"⏰ *TIMESTAMP*\n"
            f"┗ `{now}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 _YouTube Shorts Bot v4.0_"
        )

    elif status == "scheduled":
        message = (
            f"╔══════════════════════════╗\n"
            f"║  📅 SCHEDULE UPDATED      ║\n"
            f"╚══════════════════════════╝\n\n"
            f"🎲 *Next Upload Scheduled!*\n\n"
            f"⏰ Next Run: `{next_schedule} UTC`\n"
            f"📊 Remaining: `{remaining} videos`\n"
            f"⏳ Gap: `3-4 hours (random)`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 _YouTube Shorts Bot v4.0_"
        )

    elif status == "no_videos":
        message = (
            f"╔══════════════════════════╗\n"
            f"║  📭 NO VIDEOS LEFT        ║\n"
            f"╚══════════════════════════╝\n\n"
            f"⚠️ *Action Required!*\n\n"
            f"Your pending folder is empty!\n\n"
            f"📁 *Add videos to:*\n"
            f"┗ Drive → YouTubeShorts → pending\n\n"
            f"💡 *Tips:*\n"
            f"┣ Videos must be under 60 seconds\n"
            f"┣ Vertical format (9:16) preferred\n"
            f"┗ MP4 format recommended\n\n"
            f"⏰ `{now}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 _YouTube Shorts Bot v4.0_"
        )

    elif status == "error":
        message = (
            f"╔══════════════════════════╗\n"
            f"║  ❌ UPLOAD FAILED         ║\n"
            f"╚══════════════════════════╝\n\n"
            f"📹 File: `{video_name[:35]}`\n\n"
            f"🔴 *Error Details:*\n"
            f"┗ `{str(title)[:200]}`\n\n"
            f"🔧 *Action Required:*\n"
            f"┣ Check GitHub Actions logs\n"
            f"┣ Verify YouTube API quota\n"
            f"┗ Check token expiry\n\n"
            f"⏰ `{now}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 _YouTube Shorts Bot v4.0_"
        )

    elif status == "token_expired":
        message = (
            f"╔══════════════════════════╗\n"
            f"║  🚨 TOKEN EXPIRED         ║\n"
            f"╚══════════════════════════╝\n\n"
            f"⛔ *YouTube token has expired!*\n\n"
            f"🔧 *Fix in 3 steps:*\n"
            f"┣ 1️⃣ Open Google Colab\n"
            f"┣ 2️⃣ Run token generation code\n"
            f"┗ 3️⃣ Update YOUTUBE_REFRESH_TOKEN\n\n"
            f"✅ Bot resumes automatically after fix!\n\n"
            f"⏰ `{now}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 _YouTube Shorts Bot v4.0_"
        )

    elif status == "duplicate":
        message = (
            f"╔══════════════════════════╗\n"
            f"║  ⚠️ DUPLICATE SKIPPED     ║\n"
            f"╚══════════════════════════╝\n\n"
            f"📹 File: `{video_name[:35]}`\n\n"
            f"This video was already uploaded!\n"
            f"Moved to duplicates folder.\n\n"
            f"📊 Remaining: `{remaining} videos`\n"
            f"⏰ `{now}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 _YouTube Shorts Bot v4.0_"
        )

    send_telegram(message)


# ============================================================
# EMAIL ALERT
# ============================================================
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
            print(f"✅ Email sent: {subject}")
        except Exception as e:
            print(f"Email failed: {e}")
    send_telegram(f"⚠️ *{subject}*\n\n{message}")


# ============================================================
# SELF-SCHEDULING ENGINE
# ============================================================
def get_next_schedule_time():
    random_gap = random.randint(180, 240)
    next_run = datetime.utcnow() + timedelta(minutes=random_gap)
    return f"{next_run.hour:02d}:{next_run.minute:02d}", next_run, random_gap


def update_next_schedule(remaining=0):
    if not GH_TOKEN:
        print("⚠️ GH_TOKEN missing. Skipping auto-schedule.")
        return

    try:
        random_gap = random.randint(180, 240)
        next_run = datetime.utcnow() + timedelta(minutes=random_gap)
        new_cron = f"{next_run.minute} {next_run.hour} * * *"

        repo = os.environ.get('GITHUB_REPOSITORY')
        path = ".github/workflows/upload.yml"
        url = f"https://api.github.com/repos/{repo}/contents/{path}"

        headers = {
            "Authorization": f"token {GH_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Get current file
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read().decode())
            sha = data['sha']
            content = base64.b64decode(data['content']).decode()

        # Replace cron line
        updated_content = re.sub(
            r"cron: '.*'",
            f"cron: '{new_cron}'",
            content,
            count=1
        )

        # Push update
        update_data = {
            "message": f"🤖 Auto-Schedule: {next_run.hour:02d}:{next_run.minute:02d} UTC",
            "content": base64.b64encode(updated_content.encode()).decode(),
            "sha": sha
        }

        req_put = urllib.request.Request(
            url,
            data=json.dumps(update_data).encode(),
            headers=headers,
            method='PUT'
        )
        with urllib.request.urlopen(req_put):
            print(f"✅ Schedule updated: {new_cron}")

        send_telegram_report(
            status="scheduled",
            remaining=remaining,
            next_schedule=f"{next_run.hour:02d}:{next_run.minute:02d}",
        )

    except Exception as e:
        print(f"❌ Schedule update failed: {e}")


# ============================================================
# ANTI SHADOW BAN
# ============================================================
def get_anti_ban_config(filename):
    seed = int(hashlib.md5(filename.encode()).hexdigest()[:8], 16)
    random.seed(seed + int(datetime.now().strftime('%Y%m%d%H')))

    hashtag_set = random.choice(HASHTAG_POOLS)
    description_template = random.choice(DESCRIPTION_TEMPLATES)
    title_style = random.choice(TITLE_STYLES)

    extra_tags = random.sample([
        "amazing", "wow", "unbelievable", "insane", "epic",
        "cool", "awesome", "incredible", "mindblowing", "satisfying",
        "beautiful", "perfect", "outstanding", "brilliant", "stunning"
    ], 4)

    all_tags = hashtag_set + extra_tags
    hashtags = " ".join([f"#{tag}" for tag in all_tags])
    description = description_template.format(hashtags=hashtags)

    print(f"🛡️ Anti-ban style: {title_style[:40]}")
    return title_style, description, all_tags


# ============================================================
# AUTO CATEGORY DETECTION
# ============================================================
def detect_category(filename):
    clean = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').lower()
    words = clean.split()

    category_id = "22"
    for word in words:
        if word in CATEGORY_MAP:
            category_id = CATEGORY_MAP[word]
            break

    category_name = CATEGORY_NAMES.get(category_id, "People & Blogs")
    print(f"🏷️ Category: {category_name}")
    return category_id, category_name


# ============================================================
# GOOGLE TRENDS
# ============================================================
def get_trending_topics():
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=360)
        topics = pytrends.trending_searches(pn='united_states')[0].tolist()[:10]
        print(f"📈 Trending: {', '.join(topics[:5])}")
        return topics
    except Exception as e:
        print(f"Trends failed (non-critical): {e}")
        return []


# ============================================================
# SELF LEARNING
# ============================================================
def get_learning_data():
    if not SPREADSHEET_ID:
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
        best = sorted(
            data_rows,
            key=lambda x: int(x[6]) if len(x) > 6 and x[6].isdigit() else 0,
            reverse=True
        )[:3]
        if not best:
            return ""
        learning = "\n\nBEST PERFORMING TITLES (Learn from these):\n"
        for v in best:
            if len(v) > 6:
                learning += f"- '{v[2]}' → {v[6]} views\n"
        print(f"🧠 Learning from {len(best)} top videos")
        return learning
    except Exception as e:
        print(f"Learning failed (non-critical): {e}")
        return ""


# ============================================================
# COMPETITOR SPY
# ============================================================
def spy_competitor_titles(youtube_service, filename):
    try:
        clean = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
        stop = ['a', 'an', 'the', 'in', 'on', 'at', 'to', 'for', 'of',
                'with', 'by', 'from', 'is', 'are', 'was', 'and', 'or']
        words = [w for w in clean.lower().split() if w not in stop and len(w) > 2]
        query = ' '.join(words[:4]) + ' shorts'

        print(f"🕵️ Spying: {query}")
        res = youtube_service.search().list(
            q=query, part='snippet', type='video',
            videoDuration='short', order='viewCount', maxResults=5
        ).execute()

        titles = [i['snippet']['title'] for i in res.get('items', [])]
        if not titles:
            return ""

        spy = "\n\nTOP COMPETITOR TITLES (Beat these):\n"
        for t in titles[:3]:
            spy += f"- \"{t}\"\n"
        print(f"🕵️ Found {len(titles)} competitor titles")
        return spy
    except Exception as e:
        print(f"Competitor spy failed (non-critical): {e}")
        return ""


# ============================================================
# GOOGLE SHEETS LOGGING
# ============================================================
def log_to_sheets(video_name, title, video_url, tags, trending, category_name):
    if not SPREADSHEET_ID:
        return
    try:
        sa_info = json.loads(SERVICE_ACCOUNT_JSON)
        creds = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        sheets = build('sheets', 'v4', credentials=creds)
        row = [[
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            video_name,
            title,
            video_url,
            ', '.join(tags),
            ', '.join(trending[:3]) if trending else 'None',
            "0",  # Views
            "0",  # Likes
            "0",  # Comments
            category_name,
        ]]
        sheets.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A:J',
            valueInputOption='RAW',
            body={'values': row}
        ).execute()
        print("📊 Logged to Sheets")
    except Exception as e:
        print(f"Sheets failed (non-critical): {e}")


# ============================================================
# AI METADATA GENERATION
# ============================================================
def generate_ai_metadata(filename, youtube_service):
    category_id, category_name = detect_category(filename)

    if not GROQ_API_KEY:
        title, desc, tags = fallback_metadata(filename)
        return title, desc, tags, category_id, category_name

    try:
        client = Groq(api_key=GROQ_API_KEY)
        clean = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')

        title_style, desc_base, base_tags = get_anti_ban_config(filename)
        trending = get_trending_topics()
        learning = get_learning_data()
        competitor = spy_competitor_titles(youtube_service, filename)

        trends_text = ""
        if trending:
            trends_text = (
                f"\n\nToday's trends: {', '.join(trending[:5])}"
                f"\nNaturally include relevant trends if they fit."
            )

        prompt = f"""You are a world-class YouTube Shorts viral expert.

Video: "{clean}"
Category: {category_name}
Style: {title_style}{trends_text}{learning}{competitor}

TITLE RULES:
- Style: {title_style}
- Max 80 characters
- End with #Shorts
- Make viewers NEED to click
- 1-2 emojis max

DESCRIPTION RULES:
- 2-3 engaging lines
- Strong call to action
- NO hashtags (added separately)

TAGS RULES:
- Exactly 5 tags
- Specific to content
- Mix broad and niche

Respond ONLY in valid JSON:
{{"title": "title #Shorts", "description": "description", "tags": ["t1","t2","t3","t4","t5"]}}"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=400,
        )

        result = response.choices[0].message.content.strip()
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()

        meta = json.loads(result)
        title = meta.get("title", "")
        ai_desc = meta.get("description", "")
        ai_tags = meta.get("tags", [])

        if not title or len(title) < 5:
            raise ValueError("Bad title")

        if "#Shorts" not in title:
            title = f"{title} #Shorts"
        if len(title) > 100:
            title = title[:97] + "..."

        all_tags = list(set(ai_tags + base_tags))[:30]
        hashtags = " ".join([f"#{t}" for t in base_tags])
        full_desc = f"{ai_desc}\n\n{hashtags}"

        print(f"🤖 AI Title: {title}")
        return title, full_desc, all_tags, category_id, category_name

    except Exception as e:
        print(f"AI failed: {e}, using fallback")
        title, desc, tags = fallback_metadata(filename)
        return title, desc, tags, category_id, category_name


def fallback_metadata(filename):
    title = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
    if "#Shorts" not in title:
        title = f"{title} #Shorts"
    if len(title) > 100:
        title = title[:97] + "..."
    _, description, tags = get_anti_ban_config(filename)
    return title, description, tags


# ============================================================
# GOOGLE SERVICES
# ============================================================
def get_drive_service():
    try:
        creds = service_account.Credentials.from_service_account_info(
            json.loads(SERVICE_ACCOUNT_JSON),
            scopes=['https://www.googleapis.com/auth/drive']
        )
        service = build('drive', 'v3', credentials=creds)
        print("✅ Drive authenticated")
        return service
    except Exception as e:
        send_alert("Drive Auth Failed", str(e))
        sys.exit(1)


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
        print("✅ YouTube authenticated")
        return service
    except Exception as e:
        send_telegram_report(status="token_expired")
        send_alert("TOKEN EXPIRED", str(e))
        sys.exit(1)


# ============================================================
# DRIVE HELPERS
# ============================================================
def get_or_create_folder(drive_service, parent_id, name):
    query = (
        f"'{parent_id}' in parents and name='{name}' and "
        f"mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    res = drive_service.files().list(q=query, fields="files(id)").execute()
    folders = res.get('files', [])
    if folders:
        return folders[0]['id']
    folder = drive_service.files().create(
        body={
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        },
        fields='id'
    ).execute()
    print(f"📁 Created folder: {name}")
    return folder['id']


def count_videos(drive_service, folder_id):
    res = drive_service.files().list(
        q=f"'{folder_id}' in parents and trashed=false and (mimeType contains 'video/')",
        fields="files(id)",
        pageSize=1000
    ).execute()
    return len(res.get('files', []))


def get_next_video(drive_service, folder_id):
    res = drive_service.files().list(
        q=f"'{folder_id}' in parents and trashed=false and (mimeType contains 'video/')",
        fields="files(id, name, size)",
        orderBy="name",
        pageSize=1
    ).execute()
    files = res.get('files', [])
    return files[0] if files else None


def is_duplicate(drive_service, file_info, uploaded_id):
    try:
        res = drive_service.files().list(
            q=f"'{uploaded_id}' in parents and name='{file_info['name']}' and trashed=false",
            fields="files(id)"
        ).execute()
        return len(res.get('files', [])) > 0
    except:
        return False


def download_video(drive_service, file_info):
    print(f"⬇️ Downloading: {file_info['name']}")
    request = drive_service.files().get_media(fileId=file_info['id'])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    downloader = MediaIoBaseDownload(tmp, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            print(f"   {int(status.progress() * 100)}%")
    tmp.close()
    size = os.path.getsize(tmp.name) / (1024 * 1024)
    print(f"✅ Downloaded: {size:.1f} MB")
    return tmp.name, size


def move_file(drive_service, file_id, from_folder, to_folder):
    drive_service.files().update(
        fileId=file_id,
        addParents=to_folder,
        removeParents=from_folder,
        fields='id'
    ).execute()


# ============================================================
# YOUTUBE UPLOAD
# ============================================================
def upload_video(youtube_service, video_path, filename, retry=3):
    title, description, tags, category_id, category_name = generate_ai_metadata(
        filename, youtube_service
    )

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id,
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False,
        }
    }

    for attempt in range(1, retry + 1):
        try:
            print(f"📤 Attempt {attempt}/{retry}...")
            media = MediaFileUpload(
                video_path, mimetype='video/mp4',
                resumable=True, chunksize=1024 * 1024
            )
            request = youtube_service.videos().insert(
                part='snippet,status', body=body, media_body=media
            )
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"   {int(status.progress() * 100)}%")

            video_id = response['id']
            url = f"https://youtube.com/shorts/{video_id}"
            print(f"✅ Uploaded: {url}")
            return url, title, tags, category_name

        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
            if attempt < retry:
                time.sleep(attempt * 30)
            else:
                raise e


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("🤖 YOUTUBE SHORTS BOT v4.0 - GOD MODE")
    print(f"📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)

    # Validate secrets
    required = [
        'YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET',
        'YOUTUBE_REFRESH_TOKEN', 'DRIVE_FOLDER_ID',
        'GOOGLE_SERVICE_ACCOUNT'
    ]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"❌ Missing: {', '.join(missing)}")
        sys.exit(1)

    # Init services
    drive_service = get_drive_service()
    youtube_service = get_youtube_service()

    # Get folders
    pending_id = get_or_create_folder(drive_service, DRIVE_FOLDER_ID, 'pending')
    uploaded_id = get_or_create_folder(drive_service, DRIVE_FOLDER_ID, 'uploaded')
    duplicate_id = get_or_create_folder(drive_service, DRIVE_FOLDER_ID, 'duplicates')

    # Get trending early
    trending = get_trending_topics()

    # Find next video
    video = get_next_video(drive_service, pending_id)
    if not video:
        print("📭 No videos in pending folder")
        send_telegram_report(status="no_videos")
        return

    remaining = count_videos(drive_service, pending_id)
    print(f"📹 Queue: {remaining} videos")
    print(f"🎬 Next: {video['name']}")

    # Duplicate check
    if is_duplicate(drive_service, video, uploaded_id):
        print(f"⚠️ Duplicate: {video['name']}")
        move_file(drive_service, video['id'], pending_id, duplicate_id)
        send_telegram_report(
            status="duplicate",
            video_name=video['name'],
            remaining=remaining - 1,
        )
        return

    # Download
    upload_start = time.time()
    temp_path, file_size = download_video(drive_service, video)

    try:
        # Upload
        video_url, title, tags, category_name = upload_video(
            youtube_service, temp_path, video['name']
        )
        upload_duration = time.time() - upload_start

        # Move to uploaded
        move_file(drive_service, video['id'], pending_id, uploaded_id)

        # Log to sheets
        log_to_sheets(video['name'], title, video_url, tags, trending, category_name)

        # Count remaining after move
        remaining_after = count_videos(drive_service, pending_id)

        # Get next schedule
        next_time, _, _ = get_next_schedule_time()

        print("=" * 60)
        print("🎉 SUCCESS!")
        print(f"📝 {title}")
        print(f"🔗 {video_url}")
        print(f"📊 Remaining: {remaining_after}")
        print("=" * 60)

        # Professional Telegram report
        send_telegram_report(
            status="success",
            video_name=video['name'],
            title=title,
            video_url=video_url,
            category=category_name,
            tags=tags,
            remaining=remaining_after,
            trending=trending,
            next_schedule=next_time,
            upload_time=upload_duration,
            file_size_mb=file_size,
        )

        # Self-schedule next run
        update_next_schedule(remaining_after)

    except Exception as e:
        error = str(e)
        print(f"❌ Failed: {error}")
        send_telegram_report(
            status="error",
            video_name=video['name'],
            title=error,
        )
        send_alert("Upload Failed", f"{video['name']}\n{error}")
        sys.exit(1)

    finally:
        try:
            os.unlink(temp_path)
        except:
            pass


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == '__main__':
    main()
