"""
Daily News Bot — Template
-------------------------
Fetches articles from RSS feeds, sends them to Google's free Gemini AI for
summarisation, and emails the resulting brief (with a full AI log attached).

Runs once a day, automatically, using GitHub Actions. Reads its secret
credentials from environment variables (set as GitHub Secrets — never written
in this file).

===========================================================================
 TO ADAPT THIS FOR YOUR TEAM, YOU ONLY NEED TO EDIT THE  >>> CONFIG <<<
 SECTION BELOW. You do not need to understand or change anything after it.
===========================================================================
"""

import feedparser
import os
import re
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import markdown as markdown_lib


# ===========================================================================
#  >>> CONFIG <<<   —   EDIT THESE FOUR THINGS FOR YOUR OWN TEAM
# ===========================================================================

# 1) The market / country your brief is about. This appears in the email
#    heading, e.g. "Briefing on Malaysia Current Affairs".
MARKET_NAME = "Malaysia"

# 2) Who the brief is written for. The AI uses this to decide what's relevant.
#    Example: "Singapore businesses", or "our investors", or "our members".
AUDIENCE_DESC = "businesses in your region"

# 3) The news sources. Each line is:  ("Display name", "the RSS feed URL")
#    Replace these with RSS feeds for YOUR market. To find a feed, search
#    "<news site name> RSS". Keep the round brackets, quotes, and commas.
#    Any line starting with a "#", like this one, is just a comment —
#    a note for humans. Python ignores it and does not run it.
#    The 2 news sites below are just an example of how you can add your news sources.
#    Please look for and include your own news sources' RSS links, based on your market of interest.
RSS_FEEDS = [
    ("Malay Mail",   "https://www.malaymail.com/feed/rss/malaysia"),
    ("Malaysiakini", "https://www.malaysiakini.com/rss/en/news.rss"),
    # ("Your source", "https://example.com/rss"),
]

# 4) Who receives the daily email. Add each address in quotes, separated by
#    commas. Recipients can be ANY email provider — only the SENDER (set up
#    later as a Gmail App Password) has to be Gmail.
#    ensure that all the email addresses follow the example format below, with "#" in front of it.
RECIPIENT_EMAILS = [
    "you@example.com",
    # Remember to remove ^ this invalid example email from your final script as well before you save it.
    # "teammate@example.com",
    # "another.person@example.com",
]

# ===========================================================================
#  END OF CONFIG. You don't need to change anything below this line.
# ===========================================================================


# Gemini models are tried IN ORDER. The first that responds is used; if one is
# retired (404) or out of quota (429), the code falls back to the next. As of
# mid-2026 only the "flash" / "flash-lite" models have a free tier.
GEMINI_MODELS = [
    "gemini-2.5-flash",       # primary: free tier, good quality
    "gemini-2.5-flash-lite",  # fallback: free tier, most generous limits
]


# ---------------------------------------------------------------------------
# Step 1: Fetch articles from RSS feeds
# ---------------------------------------------------------------------------

def fetch_articles(feeds):
    """Download each RSS feed and collect every article's title, description,
    and link. Returns a list of article dictionaries."""
    articles = []
    for source_name, url in feeds:
        print(f"  Fetching from {source_name}...")
        feed = feedparser.parse(url)
        count_before = len(articles)
        for entry in feed.entries:
            articles.append({
                "source":      source_name,
                "title":       entry.get("title",   "No title"),
                "description": entry.get("summary", "No description available"),
                "link":        entry.get("link",    ""),
            })
        print(f"  -> {len(articles) - count_before} articles fetched from {source_name}")
    return articles


# ---------------------------------------------------------------------------
# Step 2: Build the prompt to send to Gemini
# ---------------------------------------------------------------------------

def build_prompt(articles):
    """Format all fetched articles into a single instruction prompt for Gemini."""
    articles_text = ""
    for i, article in enumerate(articles, 1):
        articles_text += f"""
Article {i} [{article['source']}]
Title: {article['title']}
Description: {article['description']}
URL: {article['link']}
"""

    prompt = f"""You are a senior analyst briefing a reader who uses your brief to
assess risks and opportunities relevant to {AUDIENCE_DESC}. Below are today's
news articles covering {MARKET_NAME} and the region. Each has a title, a
description (which may be full text or only a short preview), and a URL.

STEP 1 — TRIAGE (internal, do not print):
Read every article. Keep those material to economics, business, trade,
investment, finance, property, energy/commodities, technology,
manufacturing/supply chains, logistics, or regulation/policy. IMPORTANT:
also treat political, electoral, governmental, and policy-stability
developments as relevant, because they shape the business climate, policy
direction, and investment certainty — even when the economic impact is
indirect. Judge materiality by whether a story plausibly bears on the
economy, policy, or the business environment; discard only clearly trivial
items (crime, sports, entertainment, lifestyle, human-interest) with no such
bearing. Do not inflate genuinely trivial stories into significant ones.

STEP 2 — ANALYSE the material items. Group related articles into coherent
themes. Let the day's news decide how many themes there are — rather than
forcing a fixed number — so the report covers the full picture. Within each
theme, synthesise ALL the related articles together, so the theme reflects the
whole situation on that topic, not just one article's angle.

For EACH theme, write a tight analytical passage that covers:
  • What is actually being reported (the facts, briefly) — drawing on all the
    articles that belong to the theme.
  • Why it matters: the implications for {AUDIENCE_DESC} — reason through the
    relevant channels (trade, supply chains, exchange rates, regulation,
    investment flows, labour, or named companies where applicable).
  • Sector outlook over three horizons, only where you can say something
    substantive. This MUST be a Markdown bullet list: leave a blank line, then
    put each horizon on ITS OWN LINE starting with "- " (hyphen + space) and a
    bold label. It must render as three separate lines — never a single
    paragraph, and never inline "*" separators. Use EXACTLY this shape:

    - **Short-term (0–3 months):** ...
    - **Medium-term (3–12 months):** ...
    - **Long-term (1–3 years):** ...

    Do not write "Sector outlook:" followed by the three items on one line.

STEP 3 — STRUCTURE THE OUTPUT:
Do NOT write your own title and do NOT restate the audience or purpose — the
email template adds the title automatically. Start directly with the Executive
Summary. Structure the report in this order:
  1. "## Executive Summary" — present as 3 to 4 concise bullet points, each
     leading with the key takeaway (not a background wind-up).
  2. The main themes, each starting with a "### <Theme title>" heading, analysed
     as described in Step 2.
  3. "## Other Notable Developments" — brief one-line bullets of any other
     material stories not covered above, each ending with a clickable source
     link. Omit this section if there are none.

Keep the number of headings to a MINIMUM: only the section headings above and
one "### " heading per theme. Do NOT create sub-headings inside a theme — weave
"what is reported" and "why it matters" into flowing text with short inline
bold labels, never as their own headings.

RULES:
  • Distinguish clearly between what the source REPORTS (fact) and your
    ANALYSIS (inference). Label inference as such.
  • If a source gives only a headline or short teaser, say the evidence is
    limited and keep your claims proportionate. Do NOT invent figures,
    named companies, or specifics that the source does not support.
  • Give the most consequential themes the deepest analysis, but cover every
    material theme rather than dropping any. Group smaller related items
    together instead of discarding them, and list any standalone material story
    that doesn't fit a theme under "Other Notable Developments". Reserve
    outright omission for genuinely trivial items only.
  • Be concrete and specific; avoid generic filler like "this could have
    various impacts."
  • FORMAT IN MARKDOWN — the output is rendered into a styled HTML email, so use
    Markdown: "## " for the section headings and "### " for each theme title,
    "-" for bullet points, and "**bold**" ONLY for short inline labels
    (e.g. "**What is reported:**", "**Why it matters:**"). Do not bold whole
    sentences.

LINKS — follow these rules exactly, every time, for consistent output:
  • Do NOT put any links, URLs, or bracketed article references INSIDE the
    analysis paragraphs. Keep the prose clean and citation-free.
  • Cite sources ONLY in a "Sources:" line at the end of each theme, and inline
    at the end of each "Other Notable Developments" bullet.
  • EVERY link must be a COMPLETE Markdown link in the form
    [Article Headline](https://full-url) — the real URL always in parentheses.
  • The "Sources:" line lists the theme's article links separated by " | ", e.g.
    Sources: [Headline one](https://...) | [Headline two](https://...)

Here are today's articles:
{articles_text}"""

    return prompt


# ---------------------------------------------------------------------------
# Step 3: Send the prompt to Gemini and get the report back
# ---------------------------------------------------------------------------

def call_gemini(prompt, api_key):
    """Authenticate with Gemini and try each model in GEMINI_MODELS until one
    succeeds. Returns (report_text, model_name_that_worked)."""
    genai.configure(api_key=api_key)
    last_error = None
    for model_name in GEMINI_MODELS:
        try:
            print(f"  Trying model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            print(f"  -> Success with {model_name}")
            return response.text, model_name
        except (google_exceptions.NotFound, google_exceptions.ResourceExhausted) as e:
            print(f"  -> {model_name} unavailable ({type(e).__name__}); trying next model...")
            last_error = e

    raise RuntimeError(f"All configured Gemini models failed. Last error: {last_error}")


# ---------------------------------------------------------------------------
# Step 4: Build the AI log (for quality checks / debugging)
# ---------------------------------------------------------------------------

def build_log(articles, prompt, response, date_str, model_used):
    """Create a plain-text record of exactly what was sent to the AI and what it
    returned. Attached to the email so you can review the output."""
    separator = "=" * 60
    log = f"""DAILY NEWS BOT — RUN LOG
Date: {date_str}
Model: {model_used}
Articles fetched: {len(articles)}

{separator}
SOURCES BREAKDOWN
{separator}
"""
    source_counts = {}
    for article in articles:
        source_counts[article["source"]] = source_counts.get(article["source"], 0) + 1
    for source, count in source_counts.items():
        log += f"  {source}: {count} articles\n"

    log += f"""
{separator}
FULL PROMPT SENT TO GEMINI (INPUT)
{separator}
{prompt}

{separator}
GEMINI RESPONSE (OUTPUT)
{separator}
{response}
"""
    return log


# ---------------------------------------------------------------------------
# Step 5a: Turn the AI's Markdown report into a styled HTML email
# ---------------------------------------------------------------------------

def normalize_outlook_lines(md):
    """Force the three sector-outlook horizons onto their own bullet lines, so
    they render cleanly regardless of how the AI formatted them."""
    horizon = re.compile(
        r'[ \t]*[-*•]?[ \t]*(?:\*\*)?\s*'
        r'(Short-term|Medium-term|Long-term)\s*\(([^)]*)\)\s*:\s*(?:\*\*)?',
        re.IGNORECASE,
    )
    md = horizon.sub(lambda m: f"\n- **{m.group(1)} ({m.group(2)}):** ", md)
    md = re.sub(r'\n- \*\*Short-term', r'\n\n- **Short-term', md, count=1, flags=re.IGNORECASE)
    md = re.sub(r'\n{3,}', '\n\n', md)
    return md


def build_html_email(report_markdown, date_str):
    """Convert the AI's Markdown report into a styled HTML email. All styling is
    applied here in code (not by the AI), so it costs no extra tokens."""
    report_markdown = normalize_outlook_lines(report_markdown)

    report_markdown = re.sub(
        r'[ \t]*\n?[ \t]*(\*{0,2}(?:What is reported|Why it matters)\b[^:\n]{0,20}:\*{0,2})',
        r'\n\n\1',
        report_markdown,
    )
    report_markdown = re.sub(r'\*+\s*Sources:\s*\**', 'Sources:', report_markdown)
    report_markdown = re.sub(r'[ \t]*\n?[ \t]*Sources:', '\n\nSources:', report_markdown)
    report_markdown = re.sub(r'\n{3,}', '\n\n', report_markdown)

    body_html = markdown_lib.markdown(report_markdown, extensions=["extra", "sane_lists"])

    body_html = re.sub(
        r'<p>\s*Sources:\s*(.*?)</p>',
        r'<p style="font-style:italic; font-size:13px; margin:2px 0 18px; '
        r'color:#000000;"><strong>Sources:</strong> \1</p>',
        body_html, flags=re.DOTALL | re.IGNORECASE,
    )

    masthead = f"Briefing on {MARKET_NAME} Current Affairs"
    footer_scope = f"covering {MARKET_NAME} and the region"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{ margin:0; padding:0; background:#e7eaee; }}
  .nb-content {{ font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
    color:#17222e; line-height:1.6; font-size:15px; }}
  .nb-content h2 {{ font-size:13px; letter-spacing:.10em; text-transform:uppercase;
    color:#1c4e6b; font-weight:700; margin:28px 0 8px; padding-bottom:6px;
    border-bottom:2px solid #1c4e6b; }}
  .nb-content h3 {{ font-family:Georgia,'Times New Roman',serif; font-size:19px;
    line-height:1.25; margin:22px 0 8px; color:#17222e; }}
  .nb-content p {{ margin:0 0 12px; }}
  .nb-content ul {{ margin:8px 0 14px; padding-left:22px; }}
  .nb-content li {{ margin:0 0 7px; }}
  .nb-content a {{ color:#1c4e6b; }}
  .nb-content strong {{ color:#123a52; }}
</style>
</head>
<body>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#e7eaee;">
  <tr><td align="center" style="padding:24px 12px;">
    <table role="presentation" width="640" cellpadding="0" cellspacing="0"
      style="max-width:640px; width:100%; background:#ffffff; border:1px solid #dde2e8; border-radius:10px;">
      <tr><td style="padding:30px 34px 20px; border-bottom:3px solid #1c4e6b;
        font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
        <div style="font-family:Georgia,'Times New Roman',serif; font-size:28px;
          color:#17222e;">{masthead}</div>
        <div style="font-size:12px; letter-spacing:.04em; text-transform:uppercase;
          color:#8b97a3; margin-top:10px;">{date_str}</div>
      </td></tr>
      <tr><td class="nb-content" style="padding:6px 34px 26px;">
        {body_html}
      </td></tr>
      <tr><td style="background:#f3f6f8; border-top:1px solid #dde2e8; padding:20px 34px;
        font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
        font-size:12px; color:#586572; line-height:1.6;">
        <p style="margin:0 0 10px;">Automatically compiled from several news outlets
        {footer_scope}, and summarised by AI. Analysis is machine-generated —
        please verify specifics against the linked sources before relying on them.</p>
        <p style="margin:0;">A full AI log is attached, showing exactly what was
        sent to the AI and the output it produced.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Step 5b: Send the email (plain text + styled HTML) with the log attached
# ---------------------------------------------------------------------------

def send_email(report, log, date_str, sender_email, app_password):
    """Send the brief via Gmail's SMTP server as both plain text and styled HTML,
    with the full AI log attached as a .txt file."""
    subject = f"{MARKET_NAME} News Digest — {date_str}"
    log_filename = f"ai_log_{date_str}.txt"

    msg = MIMEMultipart("mixed")
    msg["From"]    = sender_email
    msg["To"]      = ", ".join(RECIPIENT_EMAILS)
    msg["Subject"] = subject

    body = MIMEMultipart("alternative")
    body.attach(MIMEText(report, "plain", "utf-8"))
    body.attach(MIMEText(build_html_email(report, date_str), "html", "utf-8"))
    msg.attach(body)

    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(log.encode("utf-8"))
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", f"attachment; filename={log_filename}")
    msg.attach(attachment)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, RECIPIENT_EMAILS, msg.as_string())


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"\n=== {MARKET_NAME} News Bot starting — {date_str} ===\n")

    gemini_api_key     = os.environ["GEMINI_API_KEY"]
    gmail_address      = os.environ["GMAIL_ADDRESS"]
    gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]

    print("Step 1: Fetching articles from RSS feeds...")
    articles = fetch_articles(RSS_FEEDS)
    print(f"Total articles fetched: {len(articles)}\n")

    print("Step 2: Building prompt...")
    prompt = build_prompt(articles)
    print(f"Prompt length: {len(prompt)} characters\n")

    print("Step 3: Calling Gemini API...")
    response, model_used = call_gemini(prompt, gemini_api_key)
    print(f"Gemini response received (model: {model_used}).\n")

    print("Step 4: Building AI log...")
    log = build_log(articles, prompt, response, date_str, model_used)

    print("Step 5: Sending email...")
    send_email(response, log, date_str, gmail_address, gmail_app_password)
    print(f"Email sent to {', '.join(RECIPIENT_EMAILS)}.")

    print("\n=== Run complete ===\n")


if __name__ == "__main__":
    main()
