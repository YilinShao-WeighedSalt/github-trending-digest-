# GitHub Trending Digest

Auto-published digest of the **top 5 daily-trending GitHub repositories**, with a short plain-English analysis of each (what it does, why it trended, who it's for).

Produced by a scheduled remote Claude Code routine and delivered as:

- a **push notification** (via [ntfy](https://ntfy.sh)) to the phone, and
- an **email** (via ntfy's email gateway) containing a link to that issue's report.

Tapping either opens the styled HTML report for the issue.

## How it works

Every two days the routine:

1. Fetches `https://github.com/trending?since=daily` and takes the top 5.
2. Writes a short analysis of each repo.
3. Saves the structured data to `digests/<YYYY-MM-DD>.json`.
4. Runs `build_digest.py` to render `digests/<YYYY-MM-DD>.html` and refresh `index.html`.
5. Commits & pushes here, then fires an ntfy notification whose link points at the rendered HTML
   (served through `raw.githack.com`).

## Layout

```
digests/<date>.json   structured digest data (input)
digests/<date>.html   rendered report (output of build_digest.py)
index.html            landing page linking every report
build_digest.py       JSON -> styled HTML renderer + index updater
```

## Regenerate locally

```bash
python3 build_digest.py digests/2026-06-07.json
```

This (re)writes the matching `.html` and rebuilds `index.html` from every JSON in `digests/`.
