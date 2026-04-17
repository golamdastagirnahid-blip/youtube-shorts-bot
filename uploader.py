# ================================================================
# YOUTUBE SHORTS AUTO UPLOADER
# Version: 5.0 FINAL - FOREVER
# ================================================================
# FEATURES:
# ✅ Self-Scheduling (Rewrites own cron - same time everywhere)
# ✅ AI Titles + Descriptions (Llama 3.3 70B via Groq)
# ✅ Google Trends Integration (safe - won't crash bot)
# ✅ Anti Shadow Ban (hashtag + description + style rotation)
# ✅ Self Learning AI (reads Google Sheets performance)
# ✅ Competitor Title Spy (YouTube search based)
# ✅ Auto Category Detection (50+ keywords)
# ✅ Video Duplicate Checker (by name + size)
# ✅ Professional Telegram Reports (single consistent time)
# ✅ Email Alerts (backup notification)
# ✅ Google Sheets Logging (full history)
# ✅ Auto Retry on Failure (3 attempts)
# ✅ Human-like Scheduling (3-4 hour random gaps)
# ✅ Zero delay (instant upload at trigger time)
# ✅ Telegram char limit safe (max 4000 chars)
# ✅ All errors handled gracefully
# ================================================================

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


# ================================================================
# ENVIRONMENT VARIABLES
# ================================================================
CLIENT_ID         = os.environ.get('YOUTUBE_CLIENT_ID')
CLIENT_SECRET     = os.environ.get('YOUTUBE_CLIENT_SECRET')
REFRESH_TOKEN     = os.environ.get('YOUTUBE_REFRESH_TOKEN')
DRIVE_FOLDER_ID   = os.environ.get('DRIVE_FOLDER_ID')
SA_JSON           = os.environ.get('GOOGLE_SERVICE_ACCOUNT')
ALERT_EMAIL       = os.environ.get('ALERT_EMAIL', '')
ALERT_PASSWORD    = os.environ.get('ALERT_APP_PASSWORD', '')
GROQ_API_KEY      = os.environ.get('GROQ_API_KEY', '')
SPREADSHEET_ID    = os.environ.get('SPREADSHEET_ID', '')
TG_TOKEN          = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TG_CHAT           = os.environ.get('TELEGRAM_CHAT_ID', '')
GH_TOKEN          = os.environ.get('GH_TOKEN', '')
GITHUB_REPO       = os.environ.get('GITHUB_REPOSITORY', '')


# ================================================================
# CATEGORY MAP
# ================================================================
CATEGORY_MAP = {
    "film": "1", "animation": "1", "movie": "1", "cinema": "1",
    "car": "2", "vehicle": "2", "driving": "2", "motorcycle": "2",
    "music": "10", "song": "10", "singing": "10", "dance": "10",
    "concert": "10", "dj": "10", "beat": "10",
    "pet": "15", "animal": "15", "dog": "15", "cat": "15",
    "wildlife": "15", "nature": "15", "bird": "15", "fish": "15",
    "sport": "17", "fitness": "17", "gym": "17", "workout": "17",
    "football": "17", "basketball": "17", "soccer": "17",
    "cricket": "17", "tennis": "17", "yoga": "17",
    "travel": "19", "village": "19", "city": "19", "tourism": "19",
    "destination": "19", "landscape": "19", "monsoon": "19",
    "highland": "19", "scottish": "19", "medieval": "19",
    "riverside": "19", "mountain": "19", "forest": "19",
    "beach": "19", "island": "19", "desert": "19",
    "gaming": "20", "game": "20", "minecraft": "20",
    "fortnite": "20", "gta": "20", "playstation": "20",
    "vlog": "22", "blog": "22", "daily": "22", "lifestyle": "22",
    "motivation": "22", "inspire": "22", "success": "22",
    "asmr": "22", "satisfying": "22", "relaxing": "22",
    "comedy": "23", "funny": "23", "humor": "23",
    "meme": "23", "joke": "23", "prank": "23",
    "entertainment": "24", "challenge": "24", "reaction": "24",
    "news": "25", "politics": "25", "world": "25",
    "howto": "26", "tutorial": "26", "diy": "26",
    "tips": "26", "hack": "26", "food": "26",
    "cooking": "26", "recipe": "26", "kitchen": "26",
    "fashion": "26", "beauty": "26", "makeup": "26",
    "education": "27", "science": "27", "history": "27",
    "fact": "27", "knowledge": "27", "learning": "27",
    "tech": "28", "technology": "28", "phone": "28",
    "computer": "28", "ai": "28", "robot": "28", "iphone": "28",
}

CATEGORY_NAMES = {
    "1": "Film & Animation",    "2": "Autos & Vehicles",
    "10": "Music",              "15": "Pets & Animals",
    "17": "Sports",             "19": "Travel & Events",
    "20": "Gaming",             "22": "People & Blogs",
    "23": "Comedy",             "24": "Entertainment",
    "25": "News & Politics",    "26": "Howto & Style",
    "27": "Education",          "28": "Science & Technology",
}


# ================================================================
# ANTI SHADOW BAN POOLS
# ================================================================
HASHTAG_POOLS = [
    ["shorts", "viral", "trending", "fyp", "explore"],
    ["shorts", "viralvideo", "trend", "foryou", "discover"],
    ["shortvideo", "viral", "trending2024", "fypage", "recommended"],
    ["shorts", "viralshorts", "trendingshorts", "fypシ", "mustwatch"],
    ["ytshorts", "viral", "trending", "foryoupage", "entertainment"],
    ["shorts", "viralcontent", "trending", "foryoupageシ", "watchthis"],
    ["shortsvideo", "viral", "trendingnow", "fyp", "videooftheday"],
    ["shorts", "viralpost", "trending", "fyppage", "viral2024"],
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
    "🙌 Absolutely love this!\n\nHit Subscribe! 🔔\n\n{hashtags}",
    "😮 Did you see that?!\n\nLike if this surprised you! ❤️\n\n{hashtags}",
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
    "number-based listicle style with emoji",
    "cliffhanger style that demands watching",
]


# ================================================================
# TELEGRAM - SAFE SENDER (handles 4096 char limit)
# ================================================================
def send_telegram(message):
    if not TG_TOKEN or not TG_CHAT:
        return
    try:
        # Truncate safely if over Telegram limit
        if len(message) > 4000:
            message = message[:3997] + "..."
        text = urllib.parse.quote(message)
        url = (
            f"https://api.telegram.org/bot{TG_TOKEN}"
            f"/sendMessage?chat_id={TG_CHAT}"
            f"&text={text}&parse_mode=Markdown"
            f"&disable_web_page_preview=true"
        )
        urllib.request.urlopen(url, timeout=15)
        print("✅ Telegram sent")
    except Exception as e:
        print(f"Telegram failed: {e}")


# ================================================================
# TELEGRAM - PROFESSIONAL REPORTS
# ================================================================
def telegram_success(
    video_name, title, video_url, category,
    tags, remaining, trending, next_schedule,
    upload_seconds, file_size_mb
):
    tag_str   = " ".join([f"#{t}" for t in tags[:5]])
    trend_str = ", ".join(trending[:3]) if trending else "None"
    indicator = "🟢" if remaining > 10 else "🟡" if remaining > 3 else "🔴"
    days_left = remaining // 8
    now       = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

    msg = (
        f"╔══════════════════════════╗\n"
        f"║  ✅ UPLOAD SUCCESSFUL     ║\n"
        f"╚══════════════════════════╝\n\n"
        f"📹 *VIDEO INFO*\n"
        f"┣ File: `{video_name[:35]}`\n"
        f"┣ Size: `{file_size_mb:.1f} MB`\n"
        f"┣ Category: `{category}`\n"
        f"┗ Duration: `{upload_seconds:.0f} sec`\n\n"
        f"📝 *AI TITLE*\n"
        f"┗ {title}\n\n"
        f"🏷️ *TAGS*\n"
        f"┗ {tag_str}\n\n"
        f"📈 *TRENDS*\n"
        f"┗ `{trend_str}`\n\n"
        f"🔗 *URL*\n"
        f"┗ {video_url}\n\n"
        f"📊 *QUEUE*\n"
        f"┣ {indicator} Remaining: `{remaining} videos`\n"
        f"┣ Est. Days Left: `{days_left} days`\n"
        f"┗ Next Upload: `{next_schedule} UTC`\n\n"
        f"🕐 `{now}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _Shorts Bot v5.0 FINAL_"
    )
    send_telegram(msg)


def telegram_scheduled(next_schedule, remaining):
    msg = (
        f"╔══════════════════════════╗\n"
        f"║  📅 SCHEDULE UPDATED      ║\n"
        f"╚══════════════════════════╝\n\n"
        f"⏰ Next Run: `{next_schedule} UTC`\n"
        f"📊 Remaining: `{remaining} videos`\n"
        f"⏳ Gap: `3-4 hours (random)`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _Shorts Bot v5.0 FINAL_"
    )
    send_telegram(msg)


def telegram_no_videos():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    msg = (
        f"╔══════════════════════════╗\n"
        f"║  📭 NO VIDEOS LEFT        ║\n"
        f"╚══════════════════════════╝\n\n"
        f"⚠️ *Action Required!*\n\n"
        f"📁 Add videos to:\n"
        f"┗ Drive → YouTubeShorts → pending\n\n"
        f"💡 *Requirements:*\n"
        f"┣ Under 60 seconds\n"
        f"┣ Vertical format (9:16)\n"
        f"┗ MP4 format\n\n"
        f"🕐 `{now}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _Shorts Bot v5.0 FINAL_"
    )
    send_telegram(msg)


def telegram_error(video_name, error_msg):
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    msg = (
        f"╔══════════════════════════╗\n"
        f"║  ❌ UPLOAD FAILED         ║\n"
        f"╚══════════════════════════╝\n\n"
        f"📹 `{video_name[:40]}`\n\n"
        f"🔴 *Error:*\n"
        f"┗ `{str(error_msg)[:200]}`\n\n"
        f"🔧 *Check:*\n"
        f"┣ GitHub Actions logs\n"
        f"┣ YouTube API quota\n"
        f"┗ Token expiry\n\n"
        f"🕐 `{now}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _Shorts Bot v5.0 FINAL_"
    )
    send_telegram(msg)


def telegram_token_expired():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    msg = (
        f"╔══════════════════════════╗\n"
        f"║  🚨 TOKEN EXPIRED         ║\n"
        f"╚══════════════════════════╝\n\n"
        f"⛔ YouTube token expired!\n\n"
        f"🔧 *Fix (3 steps):*\n"
        f"┣ 1️⃣ Open Google Colab\n"
        f"┣ 2️⃣ Run token code\n"
        f"┗ 3️⃣ Update GitHub Secret\n\n"
        f"✅ Bot auto-resumes after fix!\n\n"
        f"🕐 `{now}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _Shorts Bot v5.0 FINAL_"
    )
    send_telegram(msg)


def telegram_duplicate(video_name, remaining):
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    msg = (
        f"╔══════════════════════════╗\n"
        f"║  ⚠️ DUPLICATE SKIPPED     ║\n"
        f"╚══════════════════════════╝\n\n"
        f"📹 `{video_name[:40]}`\n"
        f"Already uploaded before!\n"
        f"Moved to duplicates folder.\n\n"
        f"📊 Remaining: `{remaining} videos`\n"
        f"🕐 `{now}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 _Shorts Bot v5.0 FINAL_"
    )
    send_telegram(msg)


# ================================================================
# EMAIL ALERT
# ================================================================
def send_email(subject, body):
    if not ALERT_EMAIL or not ALERT_PASSWORD:
        return
    try:
        msg = MIMEText(body)
        msg['Subject'] = f"YouTube Bot: {subject}"
        msg['From']    = ALERT_EMAIL
        msg['To']      = ALERT_EMAIL
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(ALERT_EMAIL, ALERT_PASSWORD)
        s.send_message(msg)
        s.quit()
        print(f"✅ Email: {subject}")
    except Exception as e:
        print(f"Email failed: {e}")


# ================================================================
# SELF-SCHEDULING ENGINE
# ================================================================
def update_schedule(next_run_dt, remaining):
    """Rewrites upload.yml cron with the exact same next_run_dt"""
    if not GH_TOKEN or not GITHUB_REPO:
        print("⚠️ GH_TOKEN or GITHUB_REPO missing")
        return

    try:
        new_cron     = f"{next_run_dt.minute} {next_run_dt.hour} * * *"
        next_time_str = f"{next_run_dt.hour:02d}:{next_run_dt.minute:02d}"
        path         = ".github/workflows/upload.yml"
        url          = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
        headers      = {
            "Authorization": f"token {GH_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }

        # GET current file
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as r:
            data    = json.loads(r.read().decode())
            sha     = data['sha']
            content = base64.b64decode(data['content']).decode('utf-8')

        # Replace only first cron line
        updated = re.sub(r"cron: '[^']*'", f"cron: '{new_cron}'", content, count=1)

        # PUT updated file
        payload = json.dumps({
            "message": f"🤖 Bot scheduled: {next_time_str} UTC",
            "content": base64.b64encode(updated.encode('utf-8')).decode('utf-8'),
            "sha": sha,
        }).encode('utf-8')
        req_put = urllib.request.Request(url, data=payload, headers=headers, method='PUT')
        with urllib.request.urlopen(req_put):
            print(f"✅ Cron updated → {new_cron}")

        # Send scheduled telegram with SAME time
        telegram_scheduled(next_time_str, remaining)

    except Exception as e:
        print(f"❌ Schedule update failed: {e}")


# ================================================================
# ANTI SHADOW BAN CONFIG
# ================================================================
def get_anti_ban_config(filename):
    seed = int(hashlib.md5(filename.encode()).hexdigest()[:8], 16)
    random.seed(seed + int(datetime.utcnow().strftime('%Y%m%d%H')))

    hashtag_set = random.choice(HASHTAG_POOLS)
    desc_tmpl   = random.choice(DESCRIPTION_TEMPLATES)
    title_style = random.choice(TITLE_STYLES)

    extra = random.sample([
        "amazing", "wow", "unbelievable", "insane", "epic",
        "cool", "awesome", "incredible", "mindblowing", "satisfying",
        "beautiful", "perfect", "outstanding", "brilliant", "stunning",
    ], 4)

    all_tags  = list(set(hashtag_set + extra))
    hashtags  = " ".join([f"#{t}" for t in hashtag_set])
    desc      = desc_tmpl.format(hashtags=hashtags)

    print(f"🛡️ Style: {title_style[:45]}")
    return title_style, desc, all_tags


# ================================================================
# AUTO CATEGORY DETECTION
# ================================================================
def detect_category(filename):
    clean = (
        filename.rsplit('.', 1)[0]
        .replace('_', ' ')
        .replace('-', ' ')
        .lower()
    )
    words = clean.split()

    cat_id = "22"  # Default: People & Blogs
    for word in words:
        if word in CATEGORY_MAP:
            cat_id = CATEGORY_MAP[word]
            break

    cat_name = CATEGORY_NAMES.get(cat_id, "People & Blogs")
    print(f"🏷️ Category: {cat_name} ({cat_id})")
    return cat_id, cat_name


# ================================================================
# GOOGLE TRENDS (SAFE - WON'T CRASH BOT)
# ================================================================
def get_trends():
    try:
        from pytrends.request import TrendReq
        pt      = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        topics  = pt.trending_searches(pn='united_states')[0].tolist()[:10]
        print(f"📈 Trends: {', '.join(topics[:5])}")
        return topics
    except Exception as e:
        print(f"Trends unavailable (non-critical): {e}")
        return []


# ================================================================
# SELF-LEARNING (READS SHEETS PERFORMANCE)
# ================================================================
def get_learning_data():
    if not SPREADSHEET_ID or not SA_JSON:
        return ""
    try:
        creds  = service_account.Credentials.from_service_account_info(
            json.loads(SA_JSON),
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        sheets = build('sheets', 'v4', credentials=creds)
        result = sheets.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A:J'
        ).execute()
        rows = result.get('values', [])
        if len(rows) < 3:
            return ""

        # Column G (index 6) = Views
        data   = rows[1:]
        best   = sorted(
            [r for r in data if len(r) > 6],
            key=lambda x: int(x[6]) if x[6].isdigit() else 0,
            reverse=True
        )[:3]

        if not best:
            return ""

        out = "\n\nLEARN FROM BEST PERFORMING TITLES:\n"
        for r in best:
            out += f"- '{r[2]}' → {r[6]} views\n"
        print(f"🧠 Learning from {len(best)} videos")
        return out
    except Exception as e:
        print(f"Learning failed (non-critical): {e}")
        return ""


# ================================================================
# COMPETITOR SPY (QUOTA-SAFE: only 1 API call)
# ================================================================
def spy_competitors(yt_service, filename):
    try:
        clean     = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
        stopwords = {
            'a','an','the','in','on','at','to','for',
            'of','with','by','from','is','are','was','and','or'
        }
        words     = [w for w in clean.lower().split() if w not in stopwords and len(w) > 2]
        query     = ' '.join(words[:3]) + ' shorts'

        print(f"🕵️ Competitor search: {query}")
        res   = yt_service.search().list(
            q=query, part='snippet', type='video',
            videoDuration='short', order='viewCount', maxResults=3
        ).execute()

        titles = [i['snippet']['title'] for i in res.get('items', [])]
        if not titles:
            return ""

        out = "\n\nTOP COMPETITOR TITLES (Create something BETTER):\n"
        for t in titles:
            out += f'- "{t}"\n'
        print(f"🕵️ {len(titles)} competitor titles found")
        return out
    except Exception as e:
        print(f"Competitor spy failed (non-critical): {e}")
        return ""


# ================================================================
# GOOGLE SHEETS LOGGING
# ================================================================
def log_to_sheets(video_name, title, url, tags, trending, category_name):
    if not SPREADSHEET_ID or not SA_JSON:
        return
    try:
        creds  = service_account.Credentials.from_service_account_info(
            json.loads(SA_JSON),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        sheets = build('sheets', 'v4', credentials=creds)
        row    = [[
            datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),  # A
            video_name,                                          # B
            title,                                               # C
            url,                                                 # D
            ', '.join(tags[:10]),                               # E
            ', '.join(trending[:3]) if trending else 'None',   # F
            "0",    # G Views  (update manually)
            "0",    # H Likes
            "0",    # I Comments
            category_name,                                       # J
        ]]
        sheets.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range='Sheet1!A:J',
            valueInputOption='RAW',
            body={'values': row}
        ).execute()
        print("📊 Logged to Sheets")
    except Exception as e:
        print(f"Sheets log failed (non-critical): {e}")


# ================================================================
# AI METADATA GENERATION
# ================================================================
def generate_metadata(filename, yt_service, trending):
    cat_id, cat_name = detect_category(filename)
    title_style, base_desc, base_tags = get_anti_ban_config(filename)

    if not GROQ_API_KEY:
        print("No Groq key → fallback metadata")
        title = (
            filename.rsplit('.', 1)[0]
            .replace('_', ' ').replace('-', ' ').title()
        )
        if "#Shorts" not in title:
            title = f"{title} #Shorts"
        return title[:100], base_desc, base_tags, cat_id, cat_name

    try:
        clean    = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
        learning = get_learning_data()
        spy_data = spy_competitors(yt_service, filename)

        trend_text = ""
        if trending:
            trend_text = (
                f"\n\nToday's trending: {', '.join(trending[:5])}"
                "\nInclude relevant trend ONLY if it naturally fits."
            )

        prompt = f"""You are a world-class YouTube Shorts viral expert.

Video filename: "{clean}"
Category: {cat_name}
Title style: {title_style}{trend_text}{learning}{spy_data}

TITLE RULES:
- Use style: {title_style}
- Max 80 characters total
- Must end with #Shorts
- 1-2 emojis maximum
- Make viewer NEED to click instantly

DESCRIPTION RULES:
- 2-3 lines only
- Strong call to action
- NO hashtags in description

TAGS RULES:
- Exactly 5 tags
- Relevant to video + category
- No spaces in tags

Reply ONLY valid JSON (no extra text):
{{"title":"title here #Shorts","description":"description here","tags":["t1","t2","t3","t4","t5"]}}"""

        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.85,
            max_tokens=350,
        )

        raw = response.choices[0].message.content.strip()

        # Clean code blocks if any
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        meta  = json.loads(raw)
        title = meta.get("title", "").strip()
        desc  = meta.get("description", "").strip()
        tags  = meta.get("tags", [])

        # Validate
        if not title or len(title) < 5:
            raise ValueError("Empty/short title")

        if "#Shorts" not in title:
            title = f"{title} #Shorts"
        if len(title) > 100:
            title = title[:97] + "..."

        # Merge AI tags with anti-ban base tags
        all_tags = list(dict.fromkeys(tags + base_tags))[:30]

        # Add hashtags block to description
        hashtag_block = " ".join([f"#{t}" for t in base_tags[:6]])
        full_desc     = f"{desc}\n\n{hashtag_block}"

        print(f"🤖 Title: {title}")
        print(f"🏷️ Tags: {', '.join(all_tags[:6])}")
        return title, full_desc, all_tags, cat_id, cat_name

    except Exception as e:
        print(f"AI failed ({e}) → fallback")
        title = (
            filename.rsplit('.', 1)[0]
            .replace('_', ' ').replace('-', ' ').title()
        )
        if "#Shorts" not in title:
            title = f"{title} #Shorts"
        if len(title) > 100:
            title = title[:97] + "..."
        return title, base_desc, base_tags, cat_id, cat_name


# ================================================================
# GOOGLE SERVICES
# ================================================================
def get_drive():
    try:
        creds = service_account.Credentials.from_service_account_info(
            json.loads(SA_JSON),
            scopes=['https://www.googleapis.com/auth/drive']
        )
        svc = build('drive', 'v3', credentials=creds)
        print("✅ Drive ready")
        return svc
    except Exception as e:
        send_email("Drive Auth Failed", str(e))
        send_telegram(f"❌ Drive auth failed: {e}")
        sys.exit(1)


def get_youtube():
    try:
        creds = Credentials(
            token=None,
            refresh_token=REFRESH_TOKEN,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_uri='https://oauth2.googleapis.com/token',
        )
        creds.refresh(Request())
        svc = build('youtube', 'v3', credentials=creds)
        print("✅ YouTube ready")
        return svc
    except Exception as e:
        telegram_token_expired()
        send_email("TOKEN EXPIRED", str(e))
        sys.exit(1)


# ================================================================
# DRIVE HELPERS
# ================================================================
def get_or_create_folder(drive, parent, name):
    q   = (
        f"'{parent}' in parents and name='{name}' and "
        f"mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    res = drive.files().list(q=q, fields="files(id)").execute()
    lst = res.get('files', [])
    if lst:
        return lst[0]['id']
    f = drive.files().create(
        body={
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent],
        },
        fields='id'
    ).execute()
    print(f"📁 Created: {name}")
    return f['id']


def count_videos(drive, folder_id):
    res = drive.files().list(
        q=(
            f"'{folder_id}' in parents and trashed=false "
            f"and (mimeType contains 'video/')"
        ),
        fields="files(id)",
        pageSize=1000,
    ).execute()
    return len(res.get('files', []))


def get_next_video(drive, folder_id):
    res = drive.files().list(
        q=(
            f"'{folder_id}' in parents and trashed=false "
            f"and (mimeType contains 'video/')"
        ),
        fields="files(id, name, size)",
        orderBy="name",
        pageSize=1,
    ).execute()
    files = res.get('files', [])
    return files[0] if files else None


def is_duplicate(drive, file_info, uploaded_id):
    try:
        # Check by filename
        res = drive.files().list(
            q=(
                f"'{uploaded_id}' in parents and "
                f"name='{file_info['name']}' and trashed=false"
            ),
            fields="files(id)"
        ).execute()
        if res.get('files'):
            return True

        # Check by size
        my_size = file_info.get('size', '0')
        if my_size != '0':
            res2 = drive.files().list(
                q=(
                    f"'{uploaded_id}' in parents and trashed=false "
                    f"and (mimeType contains 'video/')"
                ),
                fields="files(id, size)",
                pageSize=200,
            ).execute()
            for f in res2.get('files', []):
                if f.get('size') == my_size:
                    return True
        return False
    except:
        return False


def move_file(drive, file_id, from_id, to_id):
    drive.files().update(
        fileId=file_id,
        addParents=to_id,
        removeParents=from_id,
        fields='id'
    ).execute()


def download_video(drive, file_info):
    print(f"⬇️ Downloading: {file_info['name']}")
    req    = drive.files().get_media(fileId=file_info['id'])
    tmp    = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    loader = MediaIoBaseDownload(tmp, req)
    done   = False
    while not done:
        status, done = loader.next_chunk()
        if status:
            print(f"   {int(status.progress() * 100)}%")
    tmp.close()
    mb = os.path.getsize(tmp.name) / (1024 * 1024)
    print(f"✅ Downloaded: {mb:.1f} MB")
    return tmp.name, mb


# ================================================================
# YOUTUBE UPLOAD (3 auto-retries)
# ================================================================
def upload_to_youtube(yt_service, path, filename, trending):
    title, desc, tags, cat_id, cat_name = generate_metadata(
        filename, yt_service, trending
    )

    body = {
        'snippet': {
            'title':       title,
            'description': desc,
            'tags':        tags,
            'categoryId':  cat_id,
        },
        'status': {
            'privacyStatus':          'public',
            'selfDeclaredMadeForKids': False,
        },
    }

    for attempt in range(1, 4):
        try:
            print(f"📤 Upload attempt {attempt}/3 ...")
            media = MediaFileUpload(
                path,
                mimetype='video/mp4',
                resumable=True,
                chunksize=2 * 1024 * 1024,  # 2MB chunks
            )
            req      = yt_service.videos().insert(
                part='snippet,status', body=body, media_body=media
            )
            response = None
            while response is None:
                status, response = req.next_chunk()
                if status:
                    print(f"   {int(status.progress() * 100)}%")

            vid_id  = response['id']
            vid_url = f"https://youtube.com/shorts/{vid_id}"
            print(f"✅ Live: {vid_url}")
            return vid_url, title, tags, cat_name

        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
            if attempt < 3:
                wait = attempt * 30
                print(f"   Retrying in {wait}s ...")
                time.sleep(wait)
            else:
                raise


# ================================================================
# MAIN
# ================================================================
def main():
    print("=" * 60)
    print("🤖 YOUTUBE SHORTS BOT v5.0 FINAL")
    print(f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)

    # Validate required secrets
    missing = [
        v for v in [
            'YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET',
            'YOUTUBE_REFRESH_TOKEN', 'DRIVE_FOLDER_ID',
            'GOOGLE_SERVICE_ACCOUNT',
        ]
        if not os.environ.get(v)
    ]
    if missing:
        msg = f"Missing secrets: {', '.join(missing)}"
        print(f"❌ {msg}")
        send_telegram(f"❌ Bot cannot start!\n{msg}")
        sys.exit(1)

    # ── Calculate next run time ONCE (used everywhere) ──────────
    gap_minutes  = random.randint(180, 240)
    next_run_dt  = datetime.utcnow() + timedelta(minutes=gap_minutes)
    next_time_str = f"{next_run_dt.hour:02d}:{next_run_dt.minute:02d}"
    print(f"⏭️ Next run planned: {next_time_str} UTC (+{gap_minutes} min)")

    # ── Init services ────────────────────────────────────────────
    drive = get_drive()
    yt    = get_youtube()

    # ── Folders ──────────────────────────────────────────────────
    pending_id   = get_or_create_folder(drive, DRIVE_FOLDER_ID, 'pending')
    uploaded_id  = get_or_create_folder(drive, DRIVE_FOLDER_ID, 'uploaded')
    duplicate_id = get_or_create_folder(drive, DRIVE_FOLDER_ID, 'duplicates')

    # ── Trends (fetch once, pass everywhere) ─────────────────────
    trending = get_trends()

    # ── Find next video ──────────────────────────────────────────
    video = get_next_video(drive, pending_id)
    if not video:
        print("📭 Pending folder is empty")
        telegram_no_videos()
        send_email("No Videos Left", "Add more to Drive → pending")
        # Still update schedule so bot keeps running
        update_schedule(next_run_dt, 0)
        return

    total_pending = count_videos(drive, pending_id)
    print(f"📹 Queue: {total_pending} | Next: {video['name']}")

    # ── Duplicate check ──────────────────────────────────────────
    if is_duplicate(drive, video, uploaded_id):
        print(f"⚠️ Duplicate: {video['name']}")
        move_file(drive, video['id'], pending_id, duplicate_id)
        remaining_after_dup = count_videos(drive, pending_id)
        telegram_duplicate(video['name'], remaining_after_dup)
        # Try scheduling and exit (next run will pick next video)
        update_schedule(next_run_dt, remaining_after_dup)
        return

    # ── Download ─────────────────────────────────────────────────
    t0 = time.time()
    temp_path, file_mb = download_video(drive, video)

    try:
        # ── Upload ───────────────────────────────────────────────
        vid_url, title, tags, cat_name = upload_to_youtube(
            yt, temp_path, video['name'], trending
        )
        upload_seconds = time.time() - t0

        # ── Move to uploaded ─────────────────────────────────────
        move_file(drive, video['id'], pending_id, uploaded_id)

        # ── Count remaining ──────────────────────────────────────
        remaining = count_videos(drive, pending_id)

        # ── Log to Sheets ─────────────────────────────────────────
        log_to_sheets(
            video['name'], title, vid_url,
            tags, trending, cat_name
        )

        # ── Print summary ────────────────────────────────────────
        print("=" * 60)
        print("🎉 SUCCESS!")
        print(f"📝 {title}")
        print(f"🔗 {vid_url}")
        print(f"📊 Remaining: {remaining}")
        print(f"⏭️ Next: {next_time_str} UTC")
        print("=" * 60)

        # ── Telegram success (uses SAME next_time_str) ───────────
        telegram_success(
            video_name     = video['name'],
            title          = title,
            video_url      = vid_url,
            category       = cat_name,
            tags           = tags,
            remaining      = remaining,
            trending       = trending,
            next_schedule  = next_time_str,   # ← consistent
            upload_seconds = upload_seconds,
            file_size_mb   = file_mb,
        )

        # ── Self-schedule (uses SAME next_run_dt) ────────────────
        update_schedule(next_run_dt, remaining)  # ← consistent

    except Exception as e:
        err = str(e)
        print(f"❌ Upload failed: {err}")
        telegram_error(video['name'], err)
        send_email("Upload Failed", f"{video['name']}\n{err}")
        sys.exit(1)

    finally:
        # Always clean temp file
        try:
            os.unlink(temp_path)
            print("🧹 Temp cleaned")
        except:
            pass


# ================================================================
# ENTRY POINT
# ================================================================
if __name__ == '__main__':
    main()
