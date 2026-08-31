# Cohort: hf-text-generation

Frozen sample of text-generation models, followed forever — **including
members that die**. Selection is **manual and quarterly, never on a cron**:
a human runs the script, reads the result, commits it.

## Two qualifying paths

- **established** — top-N models by `downloads` (last 30 days), above a floor
- **new entrant** — created since a cutoff date, **any size**

The new-entrant path is what prevents a survivor-only sample: tomorrow's
winner qualifies while it is still tiny, and if it later dies, that failure
stays in the dataset instead of being silently re-sampled away.

## Quarterly procedure

```bash
export SNAPSHOTTER_CONTACT="you@example.com"
python scripts/select_cohort.py \
    --date 2026-10-01 \
    --top-n 200 --floor 10000 --new-since 2026-07-01 \
    --emit-registry
git add cohorts/ registry/
git commit -m "cohort: 2026-10-01 vintage"
```

- Writes `cohorts/hf-text-generation/<date>.yml` — a **vintage**: criteria +
  members, immutable once written (the script refuses to overwrite).
- `--emit-registry` rebuilds `registry/hf.models.cohort-members.yml` with one
  endpoint per *effective member* (the union of every vintage). Members that
  have died keep their endpoints; the gate `expect_status: [200, 404]`
  archives the 404 as the death record instead of failing the run.
- The emitted source starts `paused`; run
  `snapshotter doctor hf.models.cohort-members`, then set it `active`.

## Rules

- Old vintages are **never edited**. A correction is a new vintage.
- Criteria changes are allowed only at a vintage boundary and live in the
  vintage file itself, so every membership decision is reproducible.
- Deaths are data. Never remove a member.
