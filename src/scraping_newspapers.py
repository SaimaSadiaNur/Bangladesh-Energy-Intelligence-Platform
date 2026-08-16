import os
import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


# ─────────────────────────────────────────────
# PROTHOM ALO
# ─────────────────────────────────────────────

def prothom_alo():
    data = []

    response = requests.get(
        "https://en.prothomalo.com/topic/Energy"
    )
    soup = BeautifulSoup(response.content, "html.parser")

    news_on_page = soup.find_all("div", class_="content-area")

    if not news_on_page:
        print("Prothom Alo: No news found")
        return data

    newspaper = "Prothom Alo"
    cutoff_date = datetime.today() - timedelta(days=365)

    for news in news_on_page:

        link_tag = news.find("a", class_="title-link")
        title_span = news.find(
            "span",
            class_="tilte-no-link-parent"
        )
        date_tag = news.find(
            "time",
            class_="published-time"
        )

        if not (link_tag and title_span and date_tag):
            continue

        kicker = title_span.find("span", class_="sub-title")

        if kicker:
            headline = (
                title_span
                .get_text(strip=True)
                .replace(
                    kicker.get_text(strip=True),
                    "",
                    1
                )
                .strip()
            )
        else:
            headline = title_span.get_text(strip=True)

        try:
            article_date = datetime.strptime(
                date_tag.text.strip(),
                "%d %b %Y"
            )
        except ValueError:
            continue

        if article_date < cutoff_date:
            continue

        data.append({
            "Newspaper": newspaper,
            "title": headline,
            "date": article_date,
            "url": link_tag["href"]
        })

    return data


# ─────────────────────────────────────────────
# THE BUSINESS STANDARD
# ─────────────────────────────────────────────

def get_tbs_article_date(url):

    try:
        resp = requests.get(
            url,
            timeout=10
        )

        soup = BeautifulSoup(
            resp.content,
            "html.parser"
        )

        meta_tag = soup.find(
            "meta",
            property="article:published_time"
        )

        if meta_tag and meta_tag.get("content"):
            return datetime.fromisoformat(
                meta_tag["content"]
            )

    except Exception as e:
        print(
            f"TBS: Could not fetch date for {url}: {e}"
        )

    return None


def tbs_news():

    data = []

    response = requests.get(
        "https://www.tbsnews.net/bangladesh/energy"
    )

    soup = BeautifulSoup(
        response.content,
        "html.parser"
    )

    cards = soup.find_all(
        "div",
        class_="card"
    )

    if not cards:
        print("TBS: No news found")
        return data

    newspaper = "The Business Standard"
    cutoff_date = datetime.today() - timedelta(days=365)

    for card in cards:

        title_tag = card.find(
            ["h2", "h3"],
            class_="card-title"
        )

        if not title_tag:
            continue

        link_tag = title_tag.find("a")

        if not link_tag or not link_tag.get("href"):
            continue

        headline = link_tag.get_text(strip=True)

        url = link_tag["href"]

        if not url.startswith("http"):
            url = "https://www.tbsnews.net" + url

        time.sleep(0.5)

        article_date = get_tbs_article_date(url)

        if article_date is None:
            continue

        if article_date.tzinfo is not None:
            article_date = article_date.replace(
                tzinfo=None
            )

        if article_date < cutoff_date:
            continue

        data.append({
            "Newspaper": newspaper,
            "title": headline,
            "date": article_date,
            "url": url
        })

    return data


# ─────────────────────────────────────────────
# THE DAILY STAR
# ─────────────────────────────────────────────

def parse_daily_star_date(text, now=None):

    text = text.strip()

    now = now or datetime.now()

    relative_match = re.match(
        r"(\d+)\s*(minute|hour|day)\(s\)\s*ago",
        text,
        re.IGNORECASE
    )

    if relative_match:

        amount = int(
            relative_match.group(1)
        )

        unit = relative_match.group(2).lower()

        if unit == "minute":
            return now - timedelta(
                minutes=amount
            )

        elif unit == "hour":
            return now - timedelta(
                hours=amount
            )

        elif unit == "day":
            return now - timedelta(
                days=amount
            )

        return None

    cleaned = re.sub(
        r"\s*(AM|PM)\s*$",
        "",
        text,
        flags=re.IGNORECASE
    )

    try:
        return datetime.strptime(
            cleaned,
            "%d %B %Y, %H:%M"
        )

    except ValueError:
        return None


def daily_star():

    data = []

    response = requests.get(
        "https://www.thedailystar.net/news/environment/natural-resources/energy"
    )

    soup = BeautifulSoup(
        response.content,
        "html.parser"
    )

    newspaper = "The Daily Star"

    cutoff_date = datetime.today() - timedelta(days=365)

    title_tags = soup.find_all(
        "h3",
        class_="card-title"
    )

    if not title_tags:
        print("Daily Star: No news found")
        return data

    for title_tag in title_tags:

        link_tag = title_tag.find("a")

        if not link_tag or not link_tag.get("href"):
            continue

        headline = link_tag.get_text(strip=True)

        url = link_tag["href"]

        if not url.startswith("http"):
            url = (
                "https://www.thedailystar.net"
                + url
            )

        row = title_tag.find_parent(
            "div",
            class_="row"
        )

        if not row:
            continue

        info_div = row.find(
            "div",
            class_="card-info"
        )

        if not info_div:
            continue

        article_date = parse_daily_star_date(
            info_div.get_text(strip=True)
        )

        if article_date is None:
            continue

        if article_date < cutoff_date:
            continue

        data.append({
            "Newspaper": newspaper,
            "title": headline,
            "date": article_date,
            "url": url
        })

    return data


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():

    scrapers = [
        prothom_alo,
        tbs_news,
        daily_star
    ]

    all_data = []

    for scraper in scrapers:

        try:

            results = scraper()

            print(
                f"{scraper.__name__}: "
                f"{len(results)} articles collected"
            )

            all_data.extend(results)

        except Exception as e:

            print(
                f"{scraper.__name__} failed: {e}"
            )

    if not all_data:

        print(
            "No data collected from any source."
        )

        return

    df = pd.DataFrame(all_data)

    # ─────────────────────────────────────────
    # STANDARDIZE COLUMN NAMES
    # ─────────────────────────────────────────

    df = df.rename(
        columns={
            "title": "Headline",
            "date": "Date",
            "url": "URL"
        }
    )

    df = df[
        [
            "Date",
            "Newspaper",
            "Headline",
            "URL"
        ]
    ]

    # ─────────────────────────────────────────
    # DEDUPLICATE NEWLY SCRAPED DATA
    # ─────────────────────────────────────────

    df = df.drop_duplicates(
        subset="URL"
    )

    # ─────────────────────────────────────────
    # STANDARDIZE NEW DATA DATE
    # YYYY-MM-DD
    # ─────────────────────────────────────────

    df["Date"] = pd.to_datetime(
        df["Date"]
    ).dt.floor("min")

    df = df.sort_values(
        "Date",
        ascending=False
    ).reset_index(drop=True)

    df["Date"] = df["Date"].dt.strftime(
        "%Y-%m-%d"
    )

    # ─────────────────────────────────────────
    # FILE LOCATION
    # ─────────────────────────────────────────

    staging_file = (
        r"D:\PORTFOLIO PROJECT EXCEL\OneDrive"
        r"\Bangladesh-Energy-Intelligence-Platform"
        r"\staging_data.csv"
    )

    # ─────────────────────────────────────────
    # ACCUMULATE DATA
    # ─────────────────────────────────────────

    if os.path.exists(staging_file):

        existing = pd.read_csv(
            staging_file
        )

        # Find genuinely new articles
        new_rows = df[
            ~df["URL"].isin(
                existing["URL"]
            )
        ]

        if new_rows.empty:

            print(
                "No new articles to add."
            )

            return

        # Combine existing + new data
        combined = pd.concat(
            [
                existing,
                new_rows
            ],
            ignore_index=True
        )

        # ─────────────────────────────────────
        # HANDLE BOTH OLD AND NEW DATE FORMATS
        #
        # Old data:
        # DD/MM/YY
        #
        # New data:
        # YYYY-MM-DD
        #
        # Then convert everything to:
        # YYYY-MM-DD
        # ─────────────────────────────────────

        combined["Date"] = pd.to_datetime(
            combined["Date"],
            dayfirst=True,
            format="mixed",
            errors="coerce"
        )

        # Check for invalid dates
        invalid_dates = combined[
            combined["Date"].isna()
        ]

        if not invalid_dates.empty:

            print(
                f"Warning: "
                f"{len(invalid_dates)} "
                f"invalid date(s) found."
            )

        combined["Date"] = (
            combined["Date"]
            .dt.floor("min")
            .dt.strftime("%Y-%m-%d")
        )

        # Sort newest first
        combined = combined.sort_values(
            "Date",
            ascending=False
        ).reset_index(drop=True)

        # Save
        combined.to_csv(
            staging_file,
            index=False
        )

        print(
            f"Added {len(new_rows)} new articles. "
            f"Total: {len(combined)}"
        )

    else:

        df.to_csv(
            staging_file,
            index=False
        )

        print(
            f"Created {staging_file} "
            f"with {len(df)} articles."
        )
    refresh_log_file = r"D:\PORTFOLIO PROJECT EXCEL\OneDrive\Bangladesh-Energy-Intelligence-Platform\refresh_log.csv"

    refresh_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pd.DataFrame({
        "LastRefresh": [refresh_time]
    }).to_csv(refresh_log_file, index=False)

    print(f"Last refresh recorded: {refresh_time}")


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    main()
