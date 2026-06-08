#!/usr/bin/env python3
"""Render a weekly GitHub-trending digest from JSON to styled HTML.

Usage:
    python3 build_digest.py digests/<YYYY-MM-DD>.json

Writes digests/<YYYY-MM-DD>.html (from template.html + entry_template.html)
and regenerates index.html from every digests/*.json.
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
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Go": "#00ADD8", "Rust": "#dea584", "C": "#555555", "C++": "#f34b7d",
    "Java": "#b07219", "Ruby": "#701516", "PHP": "#4F5D95", "Shell": "#89e051",
    "C#": "#178600", "Kotlin": "#A97BFF", "Swift": "#F05138", "Dart": "#00B4AB",
    "Jupyter Notebook": "#DA5B0B", "HTML": "#e34c26", "CSS": "#563d7c",
    "Vue": "#41b883", "Zig": "#ec915c", "Lua": "#000080", "Elixir": "#6e4a7e",
}


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
    gain = repo.get("gained_this_week")
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
    week_label = data.get("week_label") or f"Week of {pretty_date(date)}"
    title = data.get("title", "GitHub Weekly Top 3")

    page_tpl = (ROOT / "template.html").read_text()
    entry_tpl = (ROOT / "entry_template.html").read_text()

    repos = sorted(data["repos"], key=lambda r: r.get("rank", 99))
    entries = "\n\n    ".join(render_entry(r, entry_tpl) for r in repos)

    page = (page_tpl
            .replace("{{PAGE_TITLE}}", esc(f"{title} — {week_label}"))
            .replace("{{WEEK_LABEL}}", esc(week_label))
            .replace("{{GENERATED_DATE}}", esc(pretty_date(date)))
            .replace("{{ENTRIES}}", entries))

    out_path = DIGESTS / f"{date}.html"
    out_path.write_text(page)
    print(f"wrote {out_path.relative_to(ROOT)}")
    return date


def build_index():
    rows = []
    for jp in sorted(DIGESTS.glob("*.json"), reverse=True):
        d = json.loads(jp.read_text())
        date = d["date"]
        repos = sorted(d["repos"], key=lambda r: r.get("rank", 99))
        teaser = " · ".join(f"{r.get('owner','')}/{r.get('repo','')}" for r in repos[:3])
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
<title>GitHub Trending — Weekly Digests</title>
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
    <h1>Weekly <em>Digests</em></h1>
    <p class="sub">The top 3 weekly-trending GitHub repositories, analyzed — one issue per week.</p>
  </header>
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


if __name__ == "__main__":
    main()
