# wss-hugging-face — Hugging Face Adoption History

Daily point-in-time capture of Hugging Face model adoption metrics
(downloads, likes). The public API only ever shows a rolling 30-day window
and a running total — **no history endpoint exists, so every uncaptured day
is gone for good**. This repo captures those numbers every day, keeps the
raw API responses verbatim, and rebuilds clean CSVs from that archive.

![Most downloaded text-generation models](examples/charts/leaderboard.svg)

![Adoption curves](examples/charts/adoption-curves.svg)

*Both charts come from [examples/visualize.py](examples/visualize.py). The
leaderboard is the latest real capture; the curves are the engine sandbox's
synthetic archive (captioned as such) until ≥ 8 real capture days exist,
then the script switches to real history automatically.*

## Use the data

The files you want are `derived/observations/<YYYY-MM>.csv` — one row per
model, per metric, per day:

```
series_id, entity_id, observed_at, captured_at, metric, value, unit, source_id, raw_ref, parser_version
```

- `entity_id` — the model (e.g. `Qwen/Qwen3-0.6B`)
- `metric` — `downloads_30d`, `downloads_all_time`, or `likes`
- `observed_at` / `captured_at` — when the fact was true / when we saw it
- `raw_ref` — the exact archived API response this row was parsed from

Three ways in:

```bash
# 1. just read the CSVs — no tooling required
head derived/observations/2026-08.csv

# 2. sqlite + ready-made queries (leaderboard, 28-day growth, lifespans)
python examples/load_observations.py

# 3. duckdb one-liner
duckdb -c "SELECT * FROM read_csv_auto('derived/observations/*.csv') LIMIT 5"
```

More detail: [docs/data-layout.md](docs/data-layout.md). Charts:
[examples/visualize.py](examples/visualize.py). Queries:
[examples/queries.sql](examples/queries.sql).

## What we track, and why

The repo exists to answer five questions, and every registry source maps to
at least one of them:

1. **Dataset interest & trends** — `hf.datasets.top-downloads`, `.top-likes`
2. **Model interest & trends** — `hf.models.top-downloads`, `.top-likes`,
   `hf.models.text-generation`
3. **Leading indicators** (what's about to be wanted, incl. which datasets
   are worth building) — `hf.models.trending`, `hf.datasets.trending`
4. **What underperforms** — `hf.models.newest`, `hf.datasets.newest`: daily
   birth-cohort samples; joined against later top lists they show which
   newcomers took off and which never found users
5. **Paper trends, over/underrated** — `hf.papers.daily` (upvote and comment
   trajectories), linked to real adoption through the `arxiv:` tags captured
   in `hf.models.top-downloads`

Every listing is captured globally and unfiltered (top 1,000 per sort) —
filtering happens at query time via `pipeline_tag`, `library_name`, and
`tags` in the raw payloads, never at capture time. Each source's registry
file carries a `notes:` line saying which question it serves.

## What's in the repo

| Folder | One-liner |
| --- | --- |
| `derived/` | **the CSVs you query** — rebuilt from the archive, never hand-edited |
| `raw/` | archived API responses, byte-for-byte, forever |
| `manifest/` | log of every fetch, even no-change ones — the provenance record |
| `registry/` | one YAML file per tracked source; **adding a source = adding one file** |
| `parsers/` | turns raw JSON into CSV rows (runs at derive time, never at capture time) |
| `health/` | one CSV saying whether every source is still alive, worst first |
| `state/` | heartbeat of the last run + auto-disable report |
| `examples/` | queries, loaders, charts |
| `docs/` | [how-it-works](docs/how-it-works.md) · [data-layout](docs/data-layout.md) |
| `.github/` | the cron workflows (capture → health → derive, daily) |

## How it runs

Three scheduled workflows a day — capture (22:10 UTC), health (23:40),
derive (00:20) — all powered by the
[snapshotter](https://github.com/OWNER/snapshotter) engine, pinned to one
version. No workflow ever names a source: capture shards whatever
`registry/` marks active, so the infrastructure never changes when sources
do. Failures are loud (red runs), sources that fail 5 days straight are
auto-disabled with a GitHub issue, and a heartbeat commit proves the cron is
alive even on quiet days.

Full walkthrough, including how to add/pause a source and what to do when
something breaks: [docs/how-it-works.md](docs/how-it-works.md).

## Run it yourself

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt            # or: pip install -e ../snapshotter
export SNAPSHOTTER_CONTACT="you@example.com"

snapshotter validate                       # check the registry
snapshotter doctor hf.models.text-generation   # dry-run one source, see raw bytes
snapshotter capture --cadence daily        # fetch + archive + manifest
snapshotter derive --parsers parsers.adoption_v1   # archive → CSVs
```

To go live on GitHub: push this repo and the engine repo under the same
owner (tag the engine `v0.1.0`, replace `OWNER` in `requirements.txt`), set
the repo secret `SNAPSHOTTER_CONTACT`, run the `capture-daily` workflow once
by hand, then let the cron take over.

## Licences

Two separate files, on purpose: code (parsers, scripts) is MIT
([LICENSE](LICENSE)); data (`raw/`, `manifest/`, `derived/`) is CC-BY-4.0
([LICENSE-DATA](LICENSE-DATA)), citation in [CITATION.cff](CITATION.cff).
Captured content originates from the Hugging Face Hub API and remains
subject to Hugging Face's terms.

Topics: `git-scraping` · `open-data` · `point-in-time-data` · `dataset`
