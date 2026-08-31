# Data layout

```
registry/    one YAML file per source — the fleet's steering wheel
raw/         archived response bytes, verbatim, forever
manifest/    append-only fetch log — the provenance record
derived/     observation tables rebuilt from raw/ (never hand-edited)
health/      health.csv, worst-first, rebuilt daily
cohorts/     frozen cohort vintages (manual, quarterly)
state/       heartbeat + auto-disable report
```

## raw/

```
raw/<source_id>/<YYYY>/<MM>/<YYYYMMDDTHHMMSSZ>-<sha256[:12]>.json
```

Bytes exactly as the publisher sent them. Year/month partitioning keeps every
directory under GitHub's 3,000-entry cap. Identical responses are stored
once; the manifest records every look.

## manifest/

`manifest/<source_id>/<YYYY-MM>.csv`, append-only:

```
source_id, url, fetched_at, http_status, content_type, content_length,
content_sha256, etag, last_modified, outcome, raw_ref, reason, warnings
```

`outcome` ∈ `first_capture | changed | unchanged | quarantined | error |
skipped`. An `unchanged` row's `raw_ref` points at the capture it matched.

## derived/

`derived/observations/<YYYY-MM>.csv` — long format:

```
series_id, entity_id, observed_at, captured_at,
metric, value, unit, source_id, raw_ref, parser_version
```

- `observed_at` — when the fact was true; `captured_at` — when we saw it.
  The separation is the point-in-time guarantee (bitemporal / SCD Type 2).
- Metrics here: `downloads_30d` (rolling window), `downloads_all_time`,
  `likes`.
- Every row cites the raw file it came from (`raw_ref`) and the parser
  version that read it — full provenance from chart back to bytes.

CSV conventions (enforced by the engine, checked byte-for-byte in CI):
append-only, ISO-8601 dates, UTF-8, LF, stable column order, explicit
header, sorted rows, trailing newline, no locale formatting. Never
hand-edit — fix the parser and rebuild.

## What the numbers mean (and don't)

Hugging Face's public API exposes `downloads` as a **rolling last-30-days
count** and `downloadsAllTime` as a running total, with no historical
breakdown. Point-in-time capture of those values is the only public way to
reconstruct adoption curves — and days that weren't captured are gone for
good. `downloads_30d` observations overlap day to day (each covers the
trailing 30 days); difference `downloads_all_time` between dates for exact
interval volumes.
