-- Example analysis over derived/observations/*.csv, loaded into a table
-- observations(series_id, entity_id, observed_at, captured_at, metric,
--              value, unit, source_id, raw_ref, parser_version).
-- Works in sqlite (see load_observations.py) and, with trivial changes, DuckDB:
--   duckdb -c "SELECT ... FROM read_csv_auto('derived/observations/*.csv')"

-- Latest snapshot: today's leaderboard
WITH obs AS (
  SELECT entity_id, observed_at, CAST(value AS REAL) AS v
  FROM observations WHERE metric = 'downloads_30d'
)
SELECT entity_id, CAST(v AS INTEGER) AS downloads_30d
FROM obs
WHERE observed_at = (SELECT MAX(observed_at) FROM obs)
ORDER BY v DESC
LIMIT 25;

-- 28-day growth per model: who is accelerating, who is decaying
WITH obs AS (
  SELECT entity_id, observed_at, CAST(value AS REAL) AS v
  FROM observations WHERE metric = 'downloads_30d'
),
latest AS (
  SELECT entity_id, observed_at AS latest_at, v AS latest_v,
         ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY observed_at DESC) AS rn
  FROM obs
),
past AS (
  SELECT o.entity_id, o.v AS past_v,
         ROW_NUMBER() OVER (PARTITION BY o.entity_id ORDER BY o.observed_at DESC) AS rn
  FROM obs o
  JOIN latest l ON l.entity_id = o.entity_id AND l.rn = 1
  WHERE o.observed_at <= datetime(l.latest_at, '-28 days')
)
SELECT l.entity_id,
       CAST(l.latest_v AS INTEGER) AS latest,
       CAST(p.past_v AS INTEGER)   AS four_weeks_ago,
       ROUND((l.latest_v - p.past_v) * 100.0 / p.past_v, 1) AS growth_pct
FROM latest l
JOIN past p ON p.entity_id = l.entity_id AND p.rn = 1
WHERE l.rn = 1
ORDER BY growth_pct DESC;

-- Lifespans: first/last sighting per model — models whose last_seen falls
-- before the series end have left the top listing (or died)
WITH obs AS (
  SELECT entity_id, observed_at FROM observations WHERE metric = 'downloads_30d'
)
SELECT entity_id,
       MIN(observed_at) AS first_seen,
       MAX(observed_at) AS last_seen
FROM obs
GROUP BY entity_id
HAVING MAX(observed_at) < (SELECT MAX(observed_at) FROM obs)
ORDER BY last_seen DESC;

-- Exact interval volume from the running total (no 30-day overlap):
-- downloads between two capture dates
WITH totals AS (
  SELECT entity_id, observed_at, CAST(value AS REAL) AS v
  FROM observations WHERE metric = 'downloads_all_time'
)
SELECT a.entity_id,
       CAST(b.v - a.v AS INTEGER) AS downloads_in_interval
FROM totals a
JOIN totals b ON b.entity_id = a.entity_id
WHERE a.observed_at = (SELECT MIN(observed_at) FROM totals)
  AND b.observed_at = (SELECT MAX(observed_at) FROM totals)
ORDER BY downloads_in_interval DESC;
