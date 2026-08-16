# Bangladesh Energy Intelligence Platform

An automated business intelligence system that monitors Bangladesh's energy sector by scraping, structuring, and analyzing news from major English-language newspapers — then surfacing the insights in an executive-ready dashboard.

## What It Does

1. **Scrapes** energy news from major English newspapers.
2. **Cleans and structures** the raw data automatically.
3. **Loads and transforms** it using Power Query and the Excel Data Model.
4. **Analyzes** it with advanced DAX measures.
5. **Presents** insights in an executive dashboard.
6. **Updates** the dataset automatically through Python.

The result is a self-refreshing pipeline that turns scattered news coverage into a structured, queryable dataset — and a dashboard that answers "what happened, and what needs attention."

## Data Sources

News is currently scraped from each outlet's dedicated energy/power section:

| Newspaper | Section Scraped |
|---|---|
| Prothom Alo (English) | [Energy topic page](https://en.prothomalo.com/topic/Energy) |
| The Business Standard | [Bangladesh / Energy](https://www.tbsnews.net/bangladesh/energy) |
| The Daily Star | [Environment / Natural Resources / Energy](https://www.thedailystar.net/news/environment/natural-resources/energy) |

Each scraper extracts a common schema — **Date, Newspaper, Headline, URL** — regardless of how each source formats its articles or dates internally.

## Classification Engine

Rather than hardcoding logic for every entity, technology, country, or topic that might appear in the news, the dashboard uses a **rule-based keyword classification system**. Articles are tagged (company, topic, sentiment, etc.) by matching against keyword mapping tables inside the Data Model.

This means: as new entities, technologies, countries, or energy topics emerge in the news cycle, the keyword mapping tables can simply be updated — **no changes to the ETL pipeline or dashboard logic required.**

## How the Pipeline Works

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  Python Scrapers │ ──▶ │  staging_data.csv │ ──▶ │  Power Query (ETL) │
│ (requests + bs4) │     │  (deduplicated,    │     │  clean + shape     │
└─────────────────┘     │   cutoff-filtered) │     └─────────┬──────────┘
                          └──────────────────┘               │
                                                               ▼
                                              ┌────────────────────────────┐
                                              │  Data Model + DAX Measures  │
                                              │  keyword classification,    │
                                              │  sentiment, star schema     │
                                              └─────────────┬──────────────┘
                                                             ▼
                                              ┌────────────────────────────┐
                                              │   Executive Dashboard        │
                                              │   (Excel)                    │
                                              └────────────────────────────┘
```

**Step by step:**

1. `scraping_newspapers.py` runs three independent scrapers (one per newspaper), each handling that source's unique HTML structure and date format.
2. Articles older than 365 days are filtered out at collection time.
3. All results are combined into a single DataFrame, standardized to `Date | Newspaper | Headline | URL`, and deduplicated by URL.
4. New data is merged into `staging_data.csv` — only genuinely new articles (by URL) are appended, so re-running the script is safe and idempotent.
5. Both old (`DD/MM/YY`) and new (`YYYY-MM-DD`) date formats in the staging file are reconciled into a single consistent format on every run.
6. A timestamp is written to `refresh_log.csv` so the dashboard can always display "last updated."
7. Excel (via Power Query) picks up `staging_data.csv`, applies further cleaning and the keyword classification tables, and feeds the Data Model that powers the dashboard.

## Project Structure

```
Bangladesh-Energy-Intelligence-Platform/
├── src/
│   ├── scraping_newspapers.py   # Python scrapers + staging pipeline
│   ├── staging_data.csv          # Accumulated, deduplicated article dataset
│   ├── refresh_log.csv           # Timestamp of the last successful refresh
│   ├── DAX.txt                   # DAX measures used in the Data Model
│   └── README.md
└── dashboard/
    └── dashboard_preview.PNG     # Screenshot of the executive dashboard
```

## Tech Stack

- **Python** — `requests`, `BeautifulSoup4`, `pandas` for scraping and data staging
- **Excel Power Query (M)** — ETL, cleaning, and keyword classification
- **Excel Data Model** — star-schema relationships across news, companies, and topics
- **DAX** — analytical measures powering the dashboard
- **Excel** — final executive dashboard and visualization layer

## Running the Scraper

```bash
pip install requests beautifulsoup4 pandas
python src/scraping_newspapers.py
```

On first run, this creates `staging_data.csv`. On subsequent runs, it appends only new articles and updates `refresh_log.csv` with the latest refresh time.

## Automation

The pipeline runs unattended via a `.bat` file wired into **Windows Task Scheduler**. The scheduled task triggers `scraping_newspapers.py`, which refreshes `staging_data.csv` and updates `refresh_log.csv` — so the Excel dashboard always reflects a recent "Last Data Update" timestamp without any manual intervention.

## Dashboard Preview

![Dashboard Preview](../dashboard/dashboard_preview.PNG)

The executive dashboard includes:
- KPI cards for Article Coverage, Negative News, Crisis & Disruption, Policy & Regulatory activity, Coverage MoM, and Energy Transition mentions
- Breakdowns by Energy Topic, Top Entities, Sentiment, and Event Type
- A filterable news table (Date, Headline, Entity, Topic, Sentiment, Event Type)
- An Energy Coverage Trend line chart
- Slicers for Year-Month, Entity Type, Sentiment, Topic, and Event Type

DAX measures powering these visuals are documented in `src/DAX.txt`.

## Roadmap

- [ ] Add remaining newspaper sources (New Age, Dhaka Tribune, The Financial Express)
- [ ] Expand keyword mapping tables for company/topic/sentiment classification


