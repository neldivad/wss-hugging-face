"""Parser for schema adoption.v1 — Hugging Face `/api/models` listings.

Pure function of the archived bytes. A bug here is fixed by bumping
PARSER_VERSION and re-running `wss derive` over the raw archive —
never by re-fetching.

Emits two layers from the same response:

  per-entity   downloads / likes / trending score for each model or dataset
  aggregate    how many models in the listing use each library, serve each
               task, and implement each arXiv paper

The aggregate layer is the substitution measure. Citation counts track
academic attention; `paper:<id> models_implementing` tracks how many models
people actually download were built on that idea — production adoption, and
the thing that says an idea won rather than merely trended.

Run: wss derive
"""

import json
from collections import Counter

from wss import derive

PARSER_VERSION = "2"

# (response key, metric name, unit) — keys verified against the live API 2026-08-31.
# Only keys present in the payload are emitted, so one parser serves every
# listing source (models and datasets, whatever mix of expand[] it requests).
METRICS = (
    ("downloads", "downloads_30d", "count/30d"),
    ("downloadsAllTime", "downloads_all_time", "count"),
    ("likes", "likes", "count"),
    ("trendingScore", "trending_score", "score"),
)

# entity_id is namespaced because several kinds of entity share one table:
# a model id, a library, a task and a paper must not collide.
ARXIV_PREFIX = "arxiv:"


def parse(body: bytes, ctx: derive.ParseContext):
    items = json.loads(body)
    if not isinstance(items, list):
        raise ValueError(f"{ctx.raw_ref}: expected a JSON list from the listing endpoint")

    libraries: Counter = Counter()
    tasks: Counter = Counter()
    papers: Counter = Counter()

    for item in items:
        entity_id = item["id"]
        for key, metric, unit in METRICS:
            if key in item and item[key] is not None:
                yield derive.Observation(
                    entity_id=entity_id, metric=metric, value=int(item[key]), unit=unit
                )

        if item.get("library_name"):
            libraries[item["library_name"]] += 1
        if item.get("pipeline_tag"):
            tasks[item["pipeline_tag"]] += 1
        # One model can cite several papers; count each at most once per model.
        for paper in {t for t in item.get("tags", []) if t.startswith(ARXIV_PREFIX)}:
            papers[paper[len(ARXIV_PREFIX) :]] += 1

    listing_size = len(items)
    if listing_size:
        yield derive.Observation(
            entity_id="listing", metric="entities_listed", value=listing_size, unit="count"
        )
    for library, count in sorted(libraries.items()):
        yield derive.Observation(
            entity_id=f"library:{library}", metric="models_using", value=count, unit="count"
        )
    for task, count in sorted(tasks.items()):
        yield derive.Observation(
            entity_id=f"task:{task}", metric="models_serving", value=count, unit="count"
        )
    for paper, count in sorted(papers.items()):
        yield derive.Observation(
            entity_id=f"paper:arxiv:{paper}",
            metric="models_implementing",
            value=count,
            unit="count",
        )


derive.register("adoption.v1", parse, PARSER_VERSION)
