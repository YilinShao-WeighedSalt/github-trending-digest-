#!/usr/bin/env python3
"""Render a GitHub-trending digest from JSON to styled HTML.

Usage:
    python3 build_digest.py digests/<YYYY-MM-DD>.json

Writes digests/<YYYY-MM-DD>.html (from template.html + entry_template.html)
and regenerates, from every digests/*.json:
  - index.html    archive landing page
  - repos.json    aggregated database of every repo ever featured
  - explore.html  knowledge-graph + directory view (from explore_template.html)
"""

import sys
import json
import html
import pathlib
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent
DIGESTS = ROOT / "digests"

# GitHub language colors — fallback when a digest JSON omits lang_color.
LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "C": "#555555",
    "C++": "#f34b7d",
    "Java": "#b07219",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Shell": "#89e051",
    "C#": "#178600",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "Dart": "#00B4AB",
    "Jupyter Notebook": "#DA5B0B",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Vue": "#41b883",
    "Zig": "#ec915c",
    "Lua": "#000080",
    "Elixir": "#6e4a7e",
}


# LLM-API requirement badge. Key icon, slashed for "none".
KEY_ICON = (
    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<circle cx="10.9" cy="5.1" r="3.3"/>'
    '<path d="M8.6 7.4 2 14M4.3 11.7l1.7 1.7M2 14l1.2 1.2"/></svg>'
)
KEY_ICON_SLASH = (
    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<circle cx="10.9" cy="5.1" r="3.3"/>'
    '<path d="M8.6 7.4 2 14M4.3 11.7l1.7 1.7"/>'
    '<path d="M1.5 1.5l13 13" stroke-width="2"/></svg>'
)

LLM_BADGES = {
    "required": ("llm-required", KEY_ICON, "LLM API required"),
    "optional": ("llm-optional", KEY_ICON, "LLM API optional"),
    "none": ("llm-none", KEY_ICON_SLASH, "No LLM API needed"),
}


def llm_badge(repo):
    """Badge HTML for the repo's llm_api field; '' when absent/unknown."""
    status = str(repo.get("llm_api") or "").strip().lower()
    if status not in LLM_BADGES:
        return ""
    cls, icon, label = LLM_BADGES[status]
    note = repo.get("llm_api_note")
    title = f' title="{html.escape(str(note), quote=True)}"' if note else ""
    return f'<span class="llm {cls}"{title}>{icon}{label}</span>'


def fmt(n):
    """Thousands-separated integer, tolerant of strings/None."""
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return str(n) if n is not None else "—"


def esc(text):
    """Escape free text for HTML body content."""
    return html.escape(str(text or ""), quote=False)


def render_entry(repo, entry_tpl):
    owner = repo.get("owner", "")
    name = repo.get("repo", "")
    url = repo.get("url") or f"https://github.com/{owner}/{name}"
    lang = repo.get("language") or "—"
    color = repo.get("lang_color") or LANG_COLORS.get(lang, "#8b8478")
    rank = repo.get("rank", "")
    # gained_this_week: pre-2026-08 digests, when the window was weekly.
    gain = repo.get("gained_today", repo.get("gained_this_week"))
    gain_str = f"+{fmt(gain)}" if gain is not None else "—"

    subs = {
        "{{LEAD_CLASS}}": " lead" if str(rank) == "1" else "",
        "{{RANK}}": esc(rank),
        "{{URL}}": html.escape(url, quote=True),
        "{{OWNER}}": esc(owner),
        "{{REPO}}": esc(name),
        "{{LANG_COLOR}}": html.escape(color, quote=True),
        "{{LANG}}": esc(lang),
        "{{STARS}}": fmt(repo.get("stars")),
        "{{GAIN}}": gain_str,
        "{{DESCRIPTION}}": esc(repo.get("description")),
        "{{ANALYSIS}}": esc(repo.get("analysis")),
        "{{LLM_BADGE}}": llm_badge(repo),
    }
    out = entry_tpl
    for tok, val in subs.items():
        out = out.replace(tok, val)
    return out


def pretty_date(iso):
    """'2026-06-07' -> 'June 7, 2026'."""
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%B %-d, %Y")
    except ValueError:
        return iso


def build_one(json_path):
    data = json.loads(pathlib.Path(json_path).read_text())
    date = data["date"]
    issue_label = data.get("issue_label") or pretty_date(date)
    title = data.get("title", "GitHub Trending Top 5")

    page_tpl = (ROOT / "template.html").read_text()
    entry_tpl = (ROOT / "entry_template.html").read_text()

    repos = sorted(data["repos"], key=lambda r: r.get("rank", 99))
    entries = "\n\n    ".join(render_entry(r, entry_tpl) for r in repos)

    page = (
        page_tpl.replace("{{PAGE_TITLE}}", esc(f"{title} — {issue_label}"))
        .replace("{{ISSUE_LABEL}}", esc(issue_label))
        .replace("{{GENERATED_DATE}}", esc(pretty_date(date)))
        .replace("{{ENTRIES}}", entries)
    )

    out_path = DIGESTS / f"{date}.html"
    out_path.write_text(page)
    print(f"wrote {out_path.relative_to(ROOT)}")
    return date


def build_db():
    """Aggregate every digests/*.json into repos.json — one record per repo."""
    by_slug = {}
    dates = []
    for jp in sorted(DIGESTS.glob("*.json")):
        d = json.loads(jp.read_text())
        dates.append(d["date"])
        for r in d["repos"]:
            slug = f"{r.get('owner', '')}/{r.get('repo', '')}"
            rec = by_slug.setdefault(
                slug,
                {
                    "owner": r.get("owner", ""),
                    "repo": r.get("repo", ""),
                    "url": r.get("url") or f"https://github.com/{slug}",
                    "appearances": [],
                },
            )
            gain = r.get("gained_today", r.get("gained_this_week"))
            rec["appearances"].append(
                {
                    "date": d["date"],
                    "rank": r.get("rank"),
                    "stars": r.get("stars"),
                    "gained": gain,
                }
            )
            # Latest issue wins for descriptive fields.
            lang = r.get("language")
            if lang:
                rec["language"] = lang
                rec["lang_color"] = r.get("lang_color") or LANG_COLORS.get(
                    lang, "#8b8478"
                )
            for field in ("description", "analysis", "llm_api", "llm_api_note"):
                if r.get(field):
                    rec[field] = r[field]
            if r.get("topics"):
                rec["topics"] = r["topics"]
    repos = list(by_slug.values())
    for rec in repos:
        apps = rec["appearances"]
        rec["first_seen"] = apps[0]["date"]
        rec["last_seen"] = apps[-1]["date"]
        rec["best_rank"] = min((a["rank"] or 99) for a in apps)
        rec["latest_stars"] = apps[-1]["stars"]
        rec["max_gained"] = max((a["gained"] or 0) for a in apps)
    db = {"issues": dates, "repos": repos}
    out = ROOT / "repos.json"
    out.write_text(json.dumps(db, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote repos.json ({len(repos)} repos, {len(dates)} issues)")
    return db


def build_explore(db):
    """Render explore.html (knowledge graph + directory) with the db inlined."""
    tpl = (ROOT / "explore_template.html").read_text()
    # Break "</script>"-like sequences so the inlined JSON can't close the tag.
    data_js = json.dumps(
        db, ensure_ascii=False, separators=(",", ":")
    ).replace("</", "<\\/")
    dates = db["issues"]
    page = (
        tpl.replace("{{DATA_JSON}}", data_js)
        .replace("{{REPO_COUNT}}", str(len(db["repos"])))
        .replace("{{ISSUE_COUNT}}", str(len(dates)))
        .replace(
            "{{DATE_RANGE}}",
            f"{pretty_date(dates[0])} — {pretty_date(dates[-1])}",
        )
        .replace("{{GENERATED_DATE}}", esc(pretty_date(dates[-1])))
    )
    (ROOT / "explore.html").write_text(page)
    print("wrote explore.html")


def build_index():
    rows = []
    for jp in sorted(DIGESTS.glob("*.json"), reverse=True):
        d = json.loads(jp.read_text())
        date = d["date"]
        repos = sorted(d["repos"], key=lambda r: r.get("rank", 99))
        teaser = " · ".join(
            f"{r.get('owner', '')}/{r.get('repo', '')}" for r in repos[:3]
        )
        rows.append(
            f'    <li><a href="digests/{date}.html"><span class="d">{esc(pretty_date(date))}</span>'
            f'<span class="t">{esc(teaser)}</span></a></li>'
        )
    index = INDEX_TEMPLATE.replace("{{ROWS}}", "\n".join(rows))
    (ROOT / "index.html").write_text(index)
    print(f"wrote index.html ({len(rows)} digest(s))")


INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GitHub Trending — Digest Archive</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{--paper:#fbfaf7;--ink:#1c1a17;--ink-soft:#4a463f;--rule:#e3ded3;--rule-strong:#cfc8ba;--accent:#9a3324;--card:#fff;}
  *{box-sizing:border-box;}
  body{margin:0;background:var(--paper);color:var(--ink);font-family:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;font-size:17px;line-height:1.6;-webkit-font-smoothing:antialiased;
    background-image:radial-gradient(circle at 18% 12%,rgba(154,51,36,.045),transparent 40%),radial-gradient(circle at 88% 2%,rgba(31,111,67,.04),transparent 34%);background-attachment:fixed;}
  .topbar{height:4px;background:var(--accent);}
  .sheet{max-width:804px;margin:0 auto;background:var(--card);box-shadow:0 18px 50px -28px rgba(28,26,23,.18);min-height:100vh;}
  .wrap{max-width:760px;margin:0 auto;padding:0 22px 64px;}
  header{padding:46px 0 26px;border-bottom:2px solid var(--ink);}
  .kicker{font-family:"JetBrains Mono",monospace;font-size:11.5px;font-weight:500;letter-spacing:.22em;text-transform:uppercase;color:var(--accent);margin:0 0 16px;}
  h1{font-family:"Fraunces",Georgia,serif;font-weight:600;font-size:clamp(2rem,7vw,3.2rem);line-height:1.04;letter-spacing:-.018em;margin:0;}
  h1 em{font-style:italic;font-weight:400;color:var(--accent);}
  .sub{margin:14px 0 0;color:var(--ink-soft);font-size:15px;}
  ul{list-style:none;margin:0;padding:0;}
  li a{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 16px;justify-content:space-between;
    padding:22px 0;border-bottom:1px solid var(--rule);text-decoration:none;color:inherit;transition:padding-left .18s ease,color .18s ease;}
  li a:hover{padding-left:8px;color:var(--accent);}
  .d{font-family:"Fraunces",Georgia,serif;font-weight:600;font-size:1.2rem;}
  .t{font-family:"JetBrains Mono",monospace;font-size:12.5px;color:var(--ink-soft);}
  .atlas{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 16px;justify-content:space-between;
    margin-top:26px;padding:18px 20px;border:1px solid var(--rule-strong);border-radius:10px;
    text-decoration:none;color:inherit;transition:border-color .18s ease,color .18s ease;}
  .atlas:hover{border-color:var(--accent);color:var(--accent);}
  .atlas .d{font-size:1.15rem;}
  .atlas .d em{font-style:italic;font-weight:400;color:var(--accent);}
  @media (prefers-color-scheme:dark){
    :root{--paper:#16140f;--ink:#f3efe6;--ink-soft:#b8b1a3;--rule:#2e2a22;--accent:#e08a6f;--card:#1e1b15;}
    header{border-color:#423d33;}
  }
</style>
</head>
<body>
<div class="topbar"></div>
<div class="sheet">
<div class="wrap">
  <header>
    <p class="kicker">GitHub Trending · Archive</p>
    <h1>Trending <em>Digests</em></h1>
    <p class="sub">The top 5 daily-trending GitHub repositories, analyzed — a new issue every two days.</p>
  </header>
  <a class="atlas" href="explore.html">
    <span class="d">Repo <em>Atlas</em></span>
    <span class="t">every featured repo · knowledge graph · by topic &amp; date →</span>
  </a>
  <ul>
{{ROWS}}
  </ul>
</div>
</div>
</body>
</html>
"""


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    for json_path in sys.argv[1:]:
        build_one(json_path)
    build_index()
    build_explore(build_db())


if __name__ == "__main__":
    main()
