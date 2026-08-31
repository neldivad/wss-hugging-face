"""Parser for schema adoption-member.v1 — a single model's `/api/models/<id>`.

Used by the cohort-members source. A dead member's endpoint returns a 404
JSON body; the gate archives it as the death record, and this parser emits no
observations for it — absence from the observation table after its last_seen
date IS the death, provable from the raw archive.
"""

import json

from snapshotter import derive

PARSER_VERSION = "1"

METRICS = (
    ("downloads", "downloads_30d", "count/30d"),
    ("downloadsAllTime", "downloads_all_time", "count"),
    ("likes", "likes", "count"),
)


def parse(body: bytes, ctx: derive.ParseContext):
    model = json.loads(body)
    if not isinstance(model, dict):
        raise ValueError(f"{ctx.raw_ref}: expected a JSON object from /api/models/<id>")
    if "id" not in model:  # 404 body — a recorded death, not an observation
        return
    for key, metric, unit in METRICS:
        if key in model and model[key] is not None:
            yield derive.Observation(
                entity_id=model["id"],
                metric=metric,
                value=int(model[key]),
                unit=unit,
            )


derive.register("adoption-member.v1", parse, PARSER_VERSION)
