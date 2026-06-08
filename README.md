# GitHub Trending Weekly Digest

Auto-published weekly digest of the **top 3 weekly-trending GitHub repositories**, with a short plain-English analysis of each (what it does, why it trended, who it's for).

Produced by a scheduled remote Claude Code routine and delivered as:

- a **push notification** (via [ntfy](https://ntfy.sh)) to the phone, and
- an **email** (via ntfy's email gateway) containing a link to that week's report.

Tapping either opens the styled HTML report for the week.

## How it works

Each Sunday the routine:

1. Fetches `https://github.com/trending?since=weekly` and takes the top 3.
2. Writes a short analysis of each repo.
3. Saves the structured data to `digests/<YYYY-MM-DD>.json`.
4. Runs `build_digest.py` to render `digests/<YYYY-MM-DD>.html` and refresh `index.html`.
5. Commits & pushes here, then fires an ntfy notification whose link points at the rendered HTML
   (served through `htmlpreview.github.io`).

## Layout

```
digests/<date>.json   structured digest data (input)
digests/<date>.html   rendered report (output of build_digest.py)
index.html            landing page linking every weekly report
build_digest.py       JSON -> styled HTML renderer + index updater
```

## Regenerate locally

```bash
python3 build_digest.py digests/2026-06-07.json
```

This (re)writes the matching `.html` and rebuilds `index.html` from every JSON in `digests/`.
