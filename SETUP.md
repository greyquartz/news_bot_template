# Setup Guide — Build Your Own Daily News Bot

This guide is written for **someone who has never used GitHub or written code
before.** Follow it in order. It takes about **30–45 minutes** the first time.
Take it slowly — there's nothing here you can break.

By the end, your team will automatically receive a short, AI-written news brief
by email every day — for free.

---

## What you'll set up (the big picture)

You'll create/collect **three free things**, then paste them into GitHub:

1. A **GitHub account** — this stores the code and runs it on a timer, for free.
2. A **Gemini AI key** — a free key so the tool can use Google's AI to write the brief.
3. A **Gmail address + "App Password"** — the account the email is sent *from*.

Then you edit two lines (your news sources and who receives the email), and turn
it on. That's it.

> **Tip:** Have a notepad open. You'll collect a few values (a key and a
> password) that you'll paste into GitHub near the end.

---

## Part 1 — Create a GitHub account and copy this project

1. Go to **https://github.com** and sign up for a free account (if you don't have one).
2. Get your own copy of this project. You have two easy options:
   - **If someone shared this as a GitHub repository:** open it and click the
     **"Fork"** button (top-right). That instantly makes your own private copy.
   - **If you have these files on your computer:** go to
     **https://github.com/new**, give the repository a name (e.g.
     `my-news-bot`), choose **Private** for now, click **Create repository**,
     then use **"Add file → Upload files"** to upload all the files. Important:
     when uploading the timer file, keep its folder path exactly as
     `.github/workflows/daily_news.yml` (GitHub creates the folders for you when
     you type that path).

You now have your own copy. Everything below happens inside it.

---

## Part 2 — Get your free Gemini AI key

This lets the tool use Google's AI to write the summary.

1. Go to **https://aistudio.google.com** and sign in with a Google account.
2. Click **"Get API key"**, then **"Create API key"**.
3. **Important:** create it in a project with **no billing / no credit card
   attached**, so it uses the genuinely free tier.
4. Copy the key it shows you — a long string starting with `AIza…`.
5. **Paste it into your notepad** for later. (Treat it like a password — don't
   share it publicly.)

---

## Part 3 — Set up the sending Gmail

The tool sends the email *through* a Gmail account. Gmail will **not** let a
program log in with your normal password, so you create a special 16-character
"App Password" just for this.

> Consider using a **dedicated Gmail account** for this (not your personal one),
> so that if anything goes wrong it doesn't affect your main inbox.

1. On the sending Google account, turn on **2-Step Verification**:
   Google Account → **Security** → **2-Step Verification** → turn it on.
   (App Passwords don't exist until this is on.)
2. Then create the App Password. Go to Google Account → **Security**, and in the
   search box type **"App Passwords"**. Open it.
3. Give it a name like `News Bot` and click **Create**.
4. Google shows a 16-character password like `abcd efgh ijkl mnop`.
   **Copy it into your notepad, and remove the spaces** so it looks like
   `abcdefghijklmnop`. You'll paste this into GitHub next.

---

## Part 4 — Store your three secrets in GitHub

"Secrets" are where GitHub keeps passwords safely — encrypted, never shown in
the code. You'll add the three values you collected.

1. In your repository, click **Settings** (top tab).
2. In the left sidebar: **Secrets and variables → Actions**.
3. Click **"New repository secret"** and add these **three**, one at a time.
   The names must match **exactly** (capital letters, underscores):

   | Name (type exactly) | Value to paste |
   |---|---|
   | `GEMINI_API_KEY` | The `AIza…` key from Part 2 |
   | `GMAIL_ADDRESS` | The sending Gmail address (e.g. `you@gmail.com`) |
   | `GMAIL_APP_PASSWORD` | The 16-character App Password from Part 3, **no spaces** |

That's the sensitive part done.

---

## Part 5 — Tell the bot your sources and recipients

Now edit the one section you're meant to change.

1. In your repository, click the file **`news_bot.py`**.
2. Click the **pencil ✏️ icon** (top-right of the file) to edit it.
   - *Tip: this in-browser editor is fine for small edits. For bigger edits,
     press the `.` (full-stop) key while viewing the repo to open a full editor.*
3. Near the top you'll see a block marked **`>>> CONFIG <<<`**. Edit these four:
   - **`MARKET_NAME`** — the country/market, e.g. `"Malaysia"`.
   - **`AUDIENCE_DESC`** — who it's for, e.g. `"Singapore businesses"`.
   - **`RSS_FEEDS`** — your news sources. Each line is
     `("Display name", "https://the-rss-feed-url")`. To find a feed, search
     *"<news site> RSS"*. Keep the brackets, quotes, and commas exactly.
   - **`RECIPIENT_EMAILS`** — who gets the email. One address per line, each in
     quotes, separated by commas. Any email provider works for recipients.
4. Scroll down and click the green **"Commit changes"** button to save.

---

## Part 6 — Turn it on and test it

1. In your repository, click the **Actions** tab.
2. If GitHub shows a one-time message like *"I understand my workflows, enable
   them"*, click it. (This only appears the first time.)
3. On the left, click **"Daily News Digest"**.
4. Click **"Run workflow" → "Run workflow"**. This runs it immediately instead
   of waiting for the scheduled time.
5. Wait a minute or two, then refresh. A **green tick** means success — check
   the recipients' inboxes for the brief. A **red cross** means something failed
   — click into the run to read the logs, and see Troubleshooting below.

After this test, the bot runs itself **once a day** automatically. To change the
time, edit the `cron` line in `.github/workflows/daily_news.yml` (it's in UTC —
see the notes inside that file).

---

## Troubleshooting (the common ones)

**"535 … BadCredentials" / login failed when sending email.**
Gmail rejected the login. Usually the App Password is wrong, has spaces, or was
invalidated (e.g. the account's main password changed, or 2-Step Verification
was turned off). Redo Part 3 to create a fresh App Password and update the
`GMAIL_APP_PASSWORD` secret. Make sure `GMAIL_ADDRESS` is the same account.

**The AI step failed with a "404 / not found" model error.**
Google occasionally retires AI models. Open `news_bot.py` and, in the
`GEMINI_MODELS` list, put a current free model name at the top.

**"prepayment credits are depleted" from the AI.**
Your Gemini key belongs to a Google project with billing switched on. Create a
new key in a project with **no billing** (Part 2) and update `GEMINI_API_KEY`.

**The email arrives at a different time than scheduled.**
Normal. GitHub's free scheduler is "best-effort" and can delay runs, especially
on-the-hour times. It still runs each day.

**Your Gmail keeps getting suspended.**
Google may flag an account that sends automated daily email to many recipients
from a data centre. This is behaviour-based, so appealing is a temporary fix.
The durable solution is to switch from Gmail to a free **transactional email
service** built for automated sending — e.g. **Brevo** (300 emails/day free),
**Mailjet**, or **Amazon SES**. The code change is small (point the sending
step at their SMTP server with their key instead of Gmail's). If you hit this,
that's the recommended path.

---

## How to change things later

- **Add/remove recipients or sources:** edit the `>>> CONFIG <<<` section of
  `news_bot.py` (Part 5) and commit.
- **Change the send time:** edit the `cron` line in
  `.github/workflows/daily_news.yml` (UTC).
- **Change the writing style:** edit the instructions inside the `build_prompt`
  function in `news_bot.py`.

Every change you save (commit) takes effect on the next run. GitHub keeps a full
history of every version, so you can always look back.

---

*Built from a free, open template. Adapt it for your own market and team.*
