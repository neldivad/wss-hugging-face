"""Parser for schema adoption.v1 — Hugging Face `/api/models` listings.

Pure function of the archived bytes. A bug here is fixed by bumping
PARSER_VERSION and re-running `snapshotter derive` over the raw archive —
never by re-fetching.

Run: snapshotter derive --parsers parsers.adoption_v1
"""

import json

from snapshotter import derive

PARSER_VERSION = "1"

# (response key, metric name, unit) — keys verified against the live API 2026-08-31
METRICS = (
    ("downloads", "downloads_30d", "count/30d"),
    ("downloadsAllTime", "downloads_all_time", "count"),
    ("likes", "likes", "count"),
)


def parse(body: bytes, ctx: derive.ParseContext):
    models = json.loads(body)
    if not isinstance(models, list):
        raise ValueError(f"{ctx.raw_ref}: expected a JSON list from /api/models")
    for model in models:
        entity_id = model["id"]
        for key, metric, unit in METRICS:
            if key in model and model[key] is not None:
                yield derive.Observation(
                    entity_id=entity_id,
                    metric=metric,
                    value=int(model[key]),
                    unit=unit,
                )


derive.register("adoption.v1", parse, PARSER_VERSION)
