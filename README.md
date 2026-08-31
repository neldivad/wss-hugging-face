# wss-hugging-face — Hugging Face Adoption History

A GitHub Actions pipeline that captures Hugging Face adoption data **every
day** — model and dataset downloads, likes, trending scores, new arrivals,
and daily-paper votes — and publishes it in this repo as clean, append-only
CSVs. The Hugging Face API only ever shows a rolling 30-day window and a
running total; **no history endpoint exists, so every uncaptured day is gone
for good**. This repo is the history.

![Most downloaded text-generation models](examples/charts/leaderboard.svg)

![Adoption curves](examples/charts/adoption-curves.svg)

*Both charts come from [examples/visualize.py](examples/visualize.py). The
leaderboard is the latest real capture; the curves are rendered from a
synthetic stand-in archive (captioned as such) until ≥ 8 real capture days
exist, then the script switches to real history automatically.*

## The data you get

The files to query are `derived/observations/<YYYY-MM>.csv` — one row per
entity, per metric, per day:

```
series_id, entity_id, observed_at, captured_at, metric, value, unit, source_id, raw_ref, parser_version
```

- `series_id` — which collection stream (see Coverage below)
- `entity_id` — the model / dataset / paper (e.g. `Qwen/Qwen3-0.6B`, arxiv `2608.26105`)
- `metric` — `downloads_30d`, `downloads_all_time`, `likes`,
  `trending_score`, `upvotes`, `comments`
- `observed_at` / `captured_at` — when the fact was true / when we saw it
- `raw_ref` — the exact archived API response the row was parsed from, so
  every number is checkable back to bytes

Three ways in:

```bash
# 1. just read the CSVs — no tooling required
head derived/observations/2026-08.csv

# 2. sqlite + ready-made queries (leaderboard, 28-day growth, lifespans)
python examples/load_observations.py

# 3. duckdb one-liner
duckdb -c "SELECT * FROM read_csv_auto('derived/observations/*.csv') LIMIT 5"
```

More detail: [docs/data-layout.md](docs/data-layout.md) ·
[examples/queries.sql](examples/queries.sql)

## Coverage

Every series' date range, human-readable here and machine-readable in
[health/health.csv](health/health.csv) (`first_success_at` →
`last_success_at`, live-updated daily):

| series | what it lists | covered since | status |
| --- | --- | --- | --- |
| `hf.models.top-downloads` | top 1,000 models by 30-day downloads (with tags, task, library) | 2026-08-31 | ongoing |
| `hf.models.top-likes` | top 1,000 models by likes | 2026-08-31 | ongoing |
| `hf.models.trending` | top 1,000 models by trending score | 2026-08-31 | ongoing |
| `hf.models.newest` | the 1,000 most recently created models (daily birth sample) | 2026-08-31 | ongoing |
| `hf.models.text-generation` | top 1,000 text-generation models by downloads | 2026-08-31 | ongoing |
| `hf.datasets.top-downloads` | top 1,000 datasets by 30-day downloads | 2026-08-31 | ongoing |
| `hf.datasets.top-likes` | top 1,000 datasets by likes | 2026-08-31 | ongoing |
| `hf.datasets.trending` | top 1,000 datasets by trending score | 2026-08-31 | ongoing |
| `hf.datasets.newest` | the 1,000 most recently created datasets | 2026-08-31 | ongoing |
| `hf.papers.daily` | the daily-papers feed (100-item window, upvotes + comments) | 2026-08-31 | ongoing |

Every listing is captured at the API's maximum size (1,000 items; the papers
feed caps at 100) and unfiltered — slicing by task, library, or tags happens
at query time. The rules of this table:

- **A new series** gets a new row with the date its coverage starts.
- **A discontinued series** keeps its row with a *covered until* date and
  status *discontinued* — its archive, manifest, and observations stay in
  the repo forever. Nothing already published is ever removed.
- One caveat, recorded per source in `registry/`: the `newest` streams are
  daily *samples* (HF sees ~3–5K births/day, more than one page), consistent
  window every day — good for cohort comparisons, not a complete census.

## What you can build from it

- **Adoption / decline curves** per model, dataset, task, or library — the
  chart above (see `examples/visualize.py`)
- **Daily leaderboards and rank-change feeds** — who entered, who fell out
- **Hype-vs-usage gaps** — likes and trending score diverging from actual
  downloads flags overrated and sleeper assets
- **Birth-cohort survival** — of the models/datasets born each week, how
  many ever find users; which kinds underperform
- **Paper over/underrated index** — upvote trajectories from
  `hf.papers.daily` joined to real adoption via the `arxiv:` tags captured
  in `hf.models.top-downloads`
- **Topic waves** — the raw papers feed carries titles, abstracts, and
  keywords per paper, so trend analysis needs no PDF downloads

Ready-made starting points: [examples/queries.sql](examples/queries.sql)
(leaderboard, 28-day growth, lifespans, interval volumes).

## What's in the repo

| Folder | One-liner |
| --- | --- |
| `derived/` | **the CSVs you query** — rebuilt from the archive, never hand-edited |
| `raw/` | archived API responses, byte-for-byte, forever |
| `manifest/` | log of every fetch, even no-change ones — the provenance record |
| `registry/` | one YAML file per collection stream; adding a stream = adding one file |
| `parsers/` | turns raw JSON into CSV rows |
| `health/` | per-series coverage range + liveness, worst first |
| `state/` | heartbeat of the last run |
| `examples/` | queries, loaders, charts |
| `docs/` | [how-it-works](docs/how-it-works.md) · [data-layout](docs/data-layout.md) |
| `.github/` | the cron workflows |

## How it runs

Three scheduled GitHub Actions a day — capture (22:10 UTC), health (23:40),
derive (00:20). The bot commits **data only** (`raw/`, `manifest/`,
`derived/`, `health/`, `state/`) — it never changes code or workflows; the
one config it may touch is flipping a repeatedly-failing stream's `status`
in `registry/` to `auto_disabled`, with a GitHub issue explaining why.
Failures are loud (red runs). Operational details, adding a stream, and
running it locally or as your own fork:
[docs/how-it-works.md](docs/how-it-works.md).

## Licences

Two separate files, on purpose: code (parsers, scripts) is MIT
([LICENSE](LICENSE)); data (`raw/`, `manifest/`, `derived/`) is CC-BY-4.0
([LICENSE-DATA](LICENSE-DATA)), citation in [CITATION.cff](CITATION.cff).
Captured content originates from the Hugging Face Hub API and remains
subject to Hugging Face's terms.

Topics: `git-scraping` · `open-data` · `point-in-time-data` · `dataset`
