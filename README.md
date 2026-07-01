[![Daily X Auto-Post (Autonomous)](https://github.com/nazrulislambhat/bot/actions/workflows/autonomous_daily.yml/badge.svg)](https://github.com/nazrulislambhat/bot/actions/workflows/autonomous_daily.yml)


# How to Go Live — Step by Step
## Autonomous X Auto-Poster on GitHub Actions

Follow these steps exactly, in order. Total time: ~25 minutes.

---

## PART 1 — Get Your X (Twitter) API Keys
*You need 4 keys from the X developer portal.*

### Step 1.1 — Apply for a developer account
1. Go to **https://developer.x.com**
2. Sign in with your @nazrulislambhat account.
3. Click **"Sign up for Free Account"** (the Basic tier is free and enough for 1 post/day).
4. Fill in the use case form. Write something like:
   > "I'm building a personal project to automate posting my own content about AI and software engineering to my own account. I will only post original content to my own account and will comply with all platform rules."
5. Accept the developer agreement. Approval is usually instant.

### Step 1.2 — Create a Project and App
1. Once inside the developer portal, click **"Projects & Apps"** → **"Overview"**.
2. Click **"+ Add App"** → name it something like `nazrulislambhat-autoposter`.
3. You'll see your **API Key** and **API Key Secret** on screen. **Copy both immediately — they are only shown once.**

### Step 1.3 — Set App permissions to Read + Write
> **Critical — do this BEFORE generating Access Tokens or they'll be read-only.**

1. In your App page, go to **"Settings"** tab.
2. Click **"Edit"** on "User authentication settings".
3. Set:
   - **App permissions**: Read and Write
   - **Type of App**: Web App, Automated App or Bot
   - **Callback URI**: `https://localhost` (placeholder, not actually used)
   - **Website URL**: `https://x.com/nazrulislambhat`
4. Click **Save**.

### Step 1.4 — Generate Access Token and Secret (for YOUR account)
1. Go to the **"Keys and Tokens"** tab of your app.
2. Under **"Authentication Tokens"**, click **"Generate"** next to *Access Token and Secret*.
3. Copy both the **Access Token** and **Access Token Secret** immediately — shown once only.

You now have 4 values — keep them somewhere safe (a password manager):
```
API Key             → goes in secret: X_API_KEY
API Key Secret      → goes in secret: X_API_SECRET
Access Token        → goes in secret: X_ACCESS_TOKEN
Access Token Secret → goes in secret: X_ACCESS_SECRET
```

---

## PART 2 — Set Up the GitHub Repository

### Step 2.1 — Create a new private repo
1. Go to **https://github.com/new**
2. Name it: `x-autoposter` (or whatever you want)
3. Set it to **Private**
4. Do NOT initialize with a README (you'll upload the files yourself)
5. Click **Create repository**

### Step 2.2 — Upload the files
You need to get these files into the repo root:
```
autonomous_poster.py
post_log.txt          (empty file)
```
And this file in the path `.github/workflows/`:
```
.github/workflows/autonomous_daily.yml
```

**Easiest way — using GitHub's web UI:**

1. In your new empty repo, click **"uploading an existing file"** link.
2. Drag and drop `autonomous_poster.py` and `post_log.txt`.
3. Click **"Commit changes"**.
4. Now click **"Add file"** → **"Create new file"**.
5. In the filename box at the top, type exactly: `.github/workflows/autonomous_daily.yml`
   (GitHub will auto-create the folders when you include slashes in the name.)
6. Paste the full contents of `autonomous_daily.yml` into the editor.
7. Click **"Commit new file"**.

**Alternative — using git on your terminal (if you have git installed):**
```bash
# Clone the empty repo
git clone https://github.com/YOUR_USERNAME/x-autoposter.git
cd x-autoposter

# Copy files in
cp /path/to/autonomous_poster.py .
touch post_log.txt
mkdir -p .github/workflows
cp /path/to/autonomous_daily.yml .github/workflows/

# Commit and push
git add .
git commit -m "Initial setup"
git push origin main
```

---

## PART 3 — Add Your API Keys as GitHub Secrets

Secrets are encrypted — nobody can read them, including you, after you paste them in. They're injected as environment variables when the Action runs.

1. In your GitHub repo, click **"Settings"** (top nav bar of the repo, not your profile settings).
2. In the left sidebar: **"Secrets and variables"** → **"Actions"**.
3. Click **"New repository secret"** and add each of these 5 secrets one at a time:

| Secret name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (starts with `sk-ant-`) |
| `X_API_KEY` | From Step 1.2 |
| `X_API_SECRET` | From Step 1.2 |
| `X_ACCESS_TOKEN` | From Step 1.4 |
| `X_ACCESS_SECRET` | From Step 1.4 |

After adding all 5, you should see them listed under "Repository secrets" (values are hidden, names are visible).

---

## PART 4 — Test It Manually Before Waiting for the Schedule

Don't wait until 19:30 IST to find out something's broken. Test it now:

1. In your repo, click the **"Actions"** tab.
2. In the left sidebar, click **"Daily X Auto-Post (Autonomous)"**.
3. Click the **"Run workflow"** button (top right of the workflow list) → **"Run workflow"**.
4. Watch the run. Click into it once it starts. You'll see each step in real time.
5. If it succeeds: check your @nazrulislambhat timeline — a tweet should appear within 30 seconds.
6. Check `post_log.txt` in the repo — it should have an entry for today's post.

### What to do if the run fails
Click the failed step (it'll be red) to see the logs. Common issues:

| Error in logs | Fix |
|---|---|
| `401 Unauthorized` from X API | Your Access Token was generated before you set Read+Write permissions. Go back to Step 1.3, set the permissions, then re-generate the Access Token in Step 1.4. |
| `403 Forbidden` from X API | The app doesn't have Write permission. Re-check Step 1.3. |
| `ANTHROPIC_API_KEY not set` | Secret name is wrong — it must be exactly `ANTHROPIC_API_KEY`. Check spelling in Settings → Secrets. |
| `tweepy not found` or `requests not found` | The `pip install` step failed. Check the "Install dependencies" step logs. |
| `403` from GitHub push step | The Actions workflow doesn't have write access to the repo. Go to repo Settings → Actions → General → "Workflow permissions" → set to "Read and write permissions". |

---

## PART 5 — Let It Run on Autopilot

Once the manual test succeeds, you're done. The workflow fires automatically every day at **14:00 UTC (19:30 IST)**.

What happens each day:
1. GitHub spins up a runner (free, takes ~10 seconds).
2. Python installs tweepy + requests.
3. `autonomous_poster.py` looks at today's date, picks the right content pillar and topic from the rotation bank (no repeats for 6 months), calls the Anthropic API to generate a natural-sounding tweet with a single niche hashtag, and posts it to X.
4. The post log is committed back to the repo so you have a record.
5. Runner shuts down.

Total runtime per day: ~30–45 seconds. Total GitHub Actions minutes used: ~1 min/day. Free tier gives you 2,000 min/month — you're using ~30.

---

## PART 6 — Optional: Add Your Anthropic API Key

If you don't have an Anthropic API key yet:
1. Go to **https://console.anthropic.com**
2. Sign up / sign in.
3. Go to **"API Keys"** → **"Create Key"**.
4. Copy the key (starts with `sk-ant-`) and add it as the `ANTHROPIC_API_KEY` GitHub secret.

The free tier credits are enough for months of daily tweets (each tweet call costs a fraction of a cent).

---

## PART 7 — Ongoing Maintenance (Almost Zero)

- **Check once a week**: glance at the Actions tab to confirm recent runs are green. If one goes red, click it to read the error — usually a temporary API hiccup that fixes itself next day.
- **Add balance to Anthropic**: the API isn't free beyond the initial credits, but at ~$0.001–0.003 per tweet, $5 lasts months. Set up a payment method at console.anthropic.com so it doesn't lapse.
- **X API free tier**: the free developer tier allows 1,500 posts/month. You're posting ~30/month — well within limits.
- **Change the posting time**: edit the `cron: "0 14 * * *"` line in `autonomous_daily.yml`. Use https://crontab.guru to calculate the right UTC time for any IST slot.

---

## Summary Checklist

- [ ] Developer account approved at developer.x.com
- [ ] App created, permissions set to Read+Write, all 4 keys copied
- [ ] GitHub repo created (private)
- [ ] `autonomous_poster.py`, `post_log.txt`, and `.github/workflows/autonomous_daily.yml` uploaded
- [ ] All 5 secrets added (ANTHROPIC_API_KEY, X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET)
- [ ] Repo workflow permissions set to "Read and write"
- [ ] Manual test run succeeded — tweet appeared on timeline
- [ ] Done. Nothing else to touch.
