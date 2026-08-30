# GitHub Trending Digest

Auto-published digest of the **top 5 daily-trending GitHub repositories**, with a short plain-English analysis of each (what it does, why it trended, who it's for).

Produced by a scheduled remote Claude Code routine and delivered as:

- a **push notification** (via [ntfy](https://ntfy.sh)) to the phone, and
- an **email** (via ntfy's email gateway) containing a link to that issue's report.

Tapping either opens the styled HTML report for the issue.

## How it works

Every two days the routine:

1. Fetches `https://github.com/trending?since=daily` and takes the top 5.
2. Writes a short analysis of each repo, tags it with `topics`, and classifies
   `llm_api` — whether the repo needs an LLM API to be useful
   (`required` / `optional` / `none`, with an optional `llm_api_note`).
3. Saves the structured data to `digests/<YYYY-MM-DD>.json`.
4. Runs `build_digest.py` to render `digests/<YYYY-MM-DD>.html` and refresh
   `index.html`, `repos.json`, and `explore.html`.
5. Commits & pushes here, then fires an ntfy notification whose link points at the rendered HTML
   (served through `raw.githack.com`).

## Layout

```
digests/<date>.json     structured digest data (input)
digests/<date>.html     rendered report (output of build_digest.py)
index.html              landing page linking every report
repos.json              aggregated database: every repo ever featured, with
                        appearances, topics, and llm_api classification
explore.html            Repo Atlas — interactive knowledge graph (repos <-> topics)
                        plus a directory browsable by topic or date, with an
                        "Ask Claude" handoff per repo (see below)
explore_template.html   template for explore.html
build_digest.py         JSON -> styled HTML renderer + index/db/atlas updater
```

## Ask Claude

Every repo — on each issue page and in the Atlas detail panel — has an
"Ask Claude" button. It opens claude.ai in a new tab with a prefilled prompt
carrying the digest's context (description, topics, LLM-API classification,
analysis) and asks Claude to fetch the repo's README before answering. The
conversation runs on your Claude subscription; the pages themselves make no
API calls and store nothing. In the Atlas panel you can type a custom question
that gets folded into the prefill. `explore.html#repo=<owner>/<repo>` deep-links
to a repo's panel.

## Regenerate locally

```bash
python3 build_digest.py digests/2026-06-07.json
```

This (re)writes the matching `.html` and rebuilds `index.html` from every JSON in `digests/`.
