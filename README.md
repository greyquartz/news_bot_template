# Daily News Bot — Template

A small, **free** tool that emails your team a short daily news brief.

Every day it automatically:
1. **Collects** the latest headlines from news sites you choose (via their RSS feeds),
2. **Summarises** them with a free Google Gemini AI model into a business-focused brief,
3. **Emails** that brief to your team — with a log of exactly what the AI did attached.

There is **no server and no database.** GitHub runs it on a timer, for free. You
don't need to leave a computer on.

---

## 👉 New here? Start with [`SETUP.md`](SETUP.md)

`SETUP.md` is a complete, click-by-click guide written for **someone who has
never used GitHub or written code before.** Follow it top to bottom and you'll
have your own working news bot.

---

## What you'll edit

You only ever edit the **`>>> CONFIG <<<`** section at the top of `news_bot.py`:

| Setting | What it is |
|---|---|
| `MARKET_NAME` | The country/market your brief is about (e.g. `"Malaysia"`). |
| `AUDIENCE_DESC` | Who the brief is for (e.g. `"Singapore businesses"`). |
| `RSS_FEEDS` | The news sources — each an RSS feed URL. |
| `RECIPIENT_EMAILS` | Who receives the daily email. |

Everything else works as-is.

## The files in this project

| File | What it is |
|---|---|
| `news_bot.py` | The whole program: fetch → summarise → email. |
| `requirements.txt` | The free add-on tools the script needs (installed automatically). |
| `.github/workflows/daily_news.yml` | The daily timer (GitHub Actions). |
| `SETUP.md` | The full step-by-step setup guide. |
| `README.md` | This file. |

## Cost

Designed to run entirely on **free tiers**: Free retrieval of news articles/headlines via RSS, 
GitHub Actions (free scheduling), the Gemini API (free `flash` models), and Gmail. 
No subscriptions and no server needed.

## A note on email reliability

This template sends the brief/newsletter through **Gmail**. That's the simplest to start with, but
Google may **suspend** the Gmail account that sends automated daily email to many
recipients from a data centre due to suspicious activity. 
Following the suspension, you will need to send in an appeal to recover your account before it can be used again. 
If that happens repeatedly, consider switching to use a free **transactional email service** (e.g. Brevo, Mailjet, Amazon SES) — they're built for automated sending and won't suspend you. See `SETUP.md` for details.
