"""Parser for schema papers.v1 — the Hugging Face `/api/daily_papers` feed.

Each item wraps a paper object; the entity is the arxiv id. Community
upvotes and comment counts are the interest signals; their trajectories
across daily captures are what makes over/underrated calls defensible.
"""

import json

from snapshotter import derive

PARSER_VERSION = "1"


def parse(body: bytes, ctx: derive.ParseContext):
    items = json.loads(body)
    if not isinstance(items, list):
        raise ValueError(f"{ctx.raw_ref}: expected a JSON list from /api/daily_papers")
    seen: set[str] = set()
    for item in items:
        paper = item["paper"]
        arxiv_id = paper["id"]
        if arxiv_id in seen:  # the feed window can resurface a paper
            continue
        seen.add(arxiv_id)
        if paper.get("upvotes") is not None:
            yield derive.Observation(entity_id=arxiv_id, metric="upvotes", value=int(paper["upvotes"]), unit="count")
        if item.get("numComments") is not None:
            yield derive.Observation(entity_id=arxiv_id, metric="comments", value=int(item["numComments"]), unit="count")


derive.register("papers.v1", parse, PARSER_VERSION)
