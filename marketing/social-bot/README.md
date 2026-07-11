# Social content bot — Facebook + Instagram + TikTok + LINE

Daily GitHub Action (~09:00 Bangkok) that:

1. Picks the next rotating topic (`topics.py`)
2. Asks Gemini for captions (or uses Thai fallbacks)
3. Generates a fresh photorealistic background via Gemini, then composes feed 1:1 + stories 9:16 PNGs (genz-style overlay layout: brand, chip, headline, CTA — not stock from `ads-office-ondemand/genz/art`)
4. Renders Ken Burns MP4 for TikTok every day; also feed/stories video when `format: video`
5. Publishes to selected channels

## Formats

| Topic IDs | format | FB / IG | TikTok | LINE |
|-----------|--------|---------|--------|------|
| `office_ondemand`, `agency_focus`, `price_pack`, `affiliate` | video | video / Reels | 9:16 clip | Flex + still |
| others | image | photo | 9:16 clip | Flex + still |

Clips are mild zoom (not shaky). LINE does not broadcast video in this phase.

## Local dry-run

```bash
cd marketing/social-bot
pip install pillow requests imageio-ffmpeg
# system ffmpeg optional (imageio-ffmpeg bundles one)
set DRY_RUN=1
set CHANNELS=facebook,instagram,tiktok,line
python generate_social_post.py
```

Outputs land in `out/YYYYMMDD/` (`bg.png`/`bg.jpg`, `feed.png`, `stories.png`, `stories.mp4`, optional `feed.mp4`, `captions.json`). If image gen fails, overlays use a branded gradient fallback (never genz art files).

## GitHub Secrets

| Secret | Required for |
|--------|----------------|
| `GEMINI_API_KEY` | Captions **and** daily backgrounds. Comma-separate up to 3 keys; on 429 (text or image) the bot rotates to the next key automatically. Shared creative brief lives in repo-root `creative_standard.py`. |
| `FACEBOOK_PAGE_ID` | Facebook |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | Facebook + Instagram |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Instagram |
| `SOCIAL_ASSET_BASE_URL` | IG + LINE image/video public URLs (prefix serving `out/...`) |
| `TIKTOK_ACCESS_TOKEN` | TikTok (draft/inbox until audit) |
| `TIKTOK_CLIENT_KEY` / `TIKTOK_CLIENT_SECRET` / `TIKTOK_REFRESH_TOKEN` | Token refresh (manual for now) |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE OA broadcast |

Optional env:

- `DRY_RUN=1` — write assets + log only
- `CHANNELS=facebook,instagram` — subset
- `TIKTOK_PUBLISH_MODE=draft` (default) or `public` after audit
- `SOCIAL_FEED_IMAGE_URL` / `SOCIAL_REELS_VIDEO_URL` — explicit overrides

## Meta setup (once)

1. Create a long-lived **Page** access token with `pages_manage_posts`, `pages_read_engagement`, `instagram_basic`, `instagram_content_publish`
2. Link Instagram Business/Creator to the Page; copy IG user id
3. For IG publishing, media must be on a public HTTPS URL — point `SOCIAL_ASSET_BASE_URL` at raw GitHub / CDN that serves committed `out/` files, or host elsewhere and set overrides

## TikTok setup (once)

1. TikTok Developer app + Content Posting API
2. OAuth for a creator account; store access token
3. Until audit approval, bot uses **inbox/draft** upload (`TIKTOK_PUBLISH_MODE=draft`)

## LINE

Uses Messaging API **broadcast**. Same token style as `ops/webhook`. Flex includes website + LINE deep link buttons. Image hero only if a public URL is available.
