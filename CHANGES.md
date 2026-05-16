# Bulletproof / Self-Healing Patch — v6.0

## Why the old bot stopped retrying

The bot self-reschedules by rewriting `upload.yml`'s cron after every **successful** run. When an upload failed, three things broke:

1. `update_schedule()` was **only called on success** — so cron stayed at the old value, and the next run only fired ~24h later instead of ~3-4h.
2. Auth failures (`get_drive()` / `get_youtube()`) called `sys.exit(1)` immediately, killing the bot before it could reschedule itself.
3. One bad video poisoned the queue forever: `get_next_video()` always picked the same alphabetically-first file. If that file failed, it kept failing, every run, forever.

## What's fixed

### `uploader.py`

- **Always reschedules.** `main()` wraps `run_once()` in try/except and `update_schedule()` runs unconditionally, even after auth failure, crash, or unexpected exception.
- **Per-video retry tracking.** Failed videos are renamed in Drive with a `retry<N>_` prefix. After `MAX_VIDEO_RETRIES` (default 3) the file is moved to a new `failed/` folder and the bot continues with the next video — queue never gets stuck.
- **Smart error classification** (`classify_error`):
  - `quota` → wait ~12h (quota resets daily)
  - `auth` → wait ~6h (gives you time to refresh token; watchdog cron will keep checking)
  - `permanent` (HTTP 400) → don't retry, move to `failed/`
  - `retryable` → exponential backoff
- **Download retries** (3 attempts with backoff) — the old version had none.
- **No more `sys.exit(1)`** on auth/upload failure. The bot logs, alerts, and reschedules instead of dying.
- Stripped `retry<N>_` prefix when generating titles/categories so the AI sees the real filename.

### `.github/workflows/upload.yml`

- **Watchdog cron** `17 */6 * * *` fires every 6 hours regardless of self-reschedule status. Belt-and-braces safety net — if GitHub's API is down or the self-reschedule step ever fails, the bot still wakes up.
- **`concurrency` group** prevents two workflow runs from colliding (watchdog + scheduled).
- **Emergency reschedule step** (`if: failure()`) — if the Python uploader dies before it can rewrite the cron itself (e.g. segfault, OOM, network kill), this final step rewrites the cron via a small inline Python script and sends a Telegram alert. Now there is no scenario where the bot can permanently stop scheduling itself.
- `timeout-minutes` bumped to 25.

## Deploy

```bash
cd C:\Users\golam\CascadeProjects\youtube-shorts-bot
# Copy these two files over the ones in your GitHub repo, commit, push.
git add uploader.py .github/workflows/upload.yml
git commit -m "v6.0 bulletproof: always-reschedule + per-video retry + watchdog cron"
git push
```

Then manually run the workflow once from the GitHub Actions tab to verify.

## New Drive folders created automatically

- `failed/` — videos that failed `MAX_VIDEO_RETRIES` times. Inspect manually.
- (existing) `pending/`, `uploaded/`, `duplicates/` unchanged.

## Manually recovering a "given up" video

Just rename the file in Drive (remove the `retry3_` prefix if any) and move it back from `failed/` to `pending/`. The bot will try again from scratch.
