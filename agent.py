#!/usr/bin/env python3
"""
🕵️ Competitive Intelligence Agent
===================================
Automatically researches AI platforms (OpenAI, Claude, Microsoft Copilot)
and generates a weekly one-pager with releases, features, sources, and
sales talk tracks.

USAGE:
    python agent.py              Research ALL competitors (with pauses)
    python agent.py 1            Research just OpenAI
    python agent.py 2            Research just Anthropic (Claude)
    python agent.py 3            Research just Microsoft Copilot
    python agent.py list         Show all competitors
    python agent.py report       Rebuild report from saved data

SETUP:
    pip install anthropic
    Set ANTHROPIC_API_KEY as environment variable (see README.md)
"""

import anthropic
import json
import os
import sys
import time
import html as html_module
from datetime import datetime

# ============================================================
# CONFIGURATION — Edit these to add/change competitors
# ============================================================

COMPETITORS = {
    "OpenAI": {
        "products": ["ChatGPT", "GPT-5 family", "Codex", "API Platform"],
        "urls_to_check": [
            "openai.com/news",
            "openai.com/pricing",
            "platform.openai.com/docs"
        ],
        "focus_areas": [
            "latest model releases (GPT-5.x family)",
            "API pricing changes",
            "new tools (Codex, function calling, agents)",
            "enterprise features",
            "partnership announcements"
        ]
    },
    "Anthropic (Claude)": {
        "products": ["Claude.ai", "Claude Code", "Claude API", "Cowork"],
        "urls_to_check": [
            "anthropic.com/news",
            "anthropic.com/pricing",
            "docs.anthropic.com"
        ],
        "focus_areas": [
            "latest model releases (Opus 4.6, Sonnet 4.6)",
            "Claude Code updates and agentic features",
            "MCP (Model Context Protocol) ecosystem",
            "enterprise and safety features",
            "Cowork and desktop capabilities"
        ]
    },
    "Microsoft Copilot": {
        "products": ["Copilot", "Copilot Studio", "GitHub Copilot", "Azure AI"],
        "urls_to_check": [
            "blogs.microsoft.com/ai",
            "github.com/features/copilot",
            "azure.microsoft.com/en-us/products/ai-services"
        ],
        "focus_areas": [
            "Copilot Studio updates and agent builder",
            "GitHub Copilot new features",
            "Azure AI services and model offerings",
            "Microsoft 365 Copilot enterprise features",
            "partnership and integration announcements"
        ]
    }
}

# ============================================================
# MODEL SELECTION — Haiku is cheapest (~$0.03/run)
# Switch to Sonnet for higher quality (~$0.25/run)
# ============================================================
MODEL = "claude-haiku-4-5-20251001"
# MODEL = "claude-sonnet-4-20250514"  # Uncomment for better quality

# Brand colors per competitor (dark theme)
BRAND_STYLES = {
    "OpenAI": {
        "accent": "#10A37F", "accent_light": "#6EE7B7",
        "why_bg": "#0D2818", "why_text": "#D1FAE5",
        "why_strong": "#6EE7B7", "why_border": "#1A4D2E",
    },
    "Anthropic (Claude)": {
        "accent": "#D97706", "accent_light": "#FCD34D",
        "why_bg": "#2D1B00", "why_text": "#FEF3C7",
        "why_strong": "#FCD34D", "why_border": "#4D3000",
    },
    "Microsoft Copilot": {
        "accent": "#2563EB", "accent_light": "#93C5FD",
        "why_bg": "#0C1929", "why_text": "#DBEAFE",
        "why_strong": "#93C5FD", "why_border": "#1E3A5F",
    },
}
DEFAULT_STYLE = {
    "accent": "#6366F1", "accent_light": "#C4CBFC",
    "why_bg": "#1A1538", "why_text": "#E0E7FF",
    "why_strong": "#C4CBFC", "why_border": "#312E81",
}

# System prompt — kept short to save tokens
RESEARCH_SYSTEM_PROMPT = """You are a competitive intelligence analyst for the AI industry.
Research the company and return a JSON brief. Rules:
- Only report facts from web search. Never invent.
- Focus on last 30 days. Include model names, versions, dates.
- Include source URLs for claims. Mark confidence: "verified", "analysis", or "unverified".
- If pricing not found, say "Not found in search".

Return ONLY valid JSON, no markdown:
{
    "company": "Name",
    "last_updated": "YYYY-MM-DD",
    "latest_releases": [{"name":"","date":"","summary":"","why_it_matters":"","confidence":"verified","source_url":"","source_name":""}],
    "current_models": [{"name":"","best_for":"","pricing_note":""}],
    "key_differentiators": [{"text":"","confidence":"verified"}],
    "things_to_try": [""],
    "recent_news": [{"headline":"","source_url":"","source_name":""}],
    "talk_track_ammo": [""],
    "sources": [{"title":"","url":"","date":""}]
}
"""


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def esc(text):
    """HTML-escape text to prevent broken output."""
    if not text:
        return ""
    return html_module.escape(str(text))


def extract_json(text):
    """Extract JSON from text that might have extra stuff around it."""
    text = text.strip()
    for prefix in ["```json", "```"]:
        if text.startswith(prefix):
            text = text[len(prefix):]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find first { and last } — extract just the JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


def research_competitor(client, company_name, company_info):
    """Research one competitor using Claude + web search. Retries on rate limits."""

    print(f"\n🔍 Researching {company_name}...")
    print(f"   Focus areas: {', '.join(company_info['focus_areas'][:3])}...")

    user_prompt = f"""Research {company_name} ({', '.join(company_info['products'])}).
Focus: {', '.join(company_info['focus_areas'])}
Check: {', '.join(company_info['urls_to_check'])}
Find the most recent developments (last 30 days). Include source URLs. Return ONLY valid JSON."""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=3000,
                system=RESEARCH_SYSTEM_PROMPT,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[{"role": "user", "content": user_prompt}]
            )

            result_text = ""
            for block in response.content:
                if block.type == "text":
                    result_text += block.text

            data = extract_json(result_text)
            if data and isinstance(data, dict):
                releases = len(data.get("latest_releases", []))
                sources = len(data.get("sources", []))
                print(f"   ✅ Got {releases} releases, {sources} sources")
                return data

            # JSON extraction failed — try cleanup
            print(f"   ⚠️  JSON parse issue. Attempting cleanup...")
            try:
                time.sleep(10)
                retry = client.messages.create(
                    model=MODEL,
                    max_tokens=3000,
                    system="Extract the JSON object from the text below. Output ONLY the JSON, nothing else.",
                    messages=[{"role": "user", "content": result_text[:6000]}]
                )
                retry_text = "".join(b.text for b in retry.content if b.type == "text")
                retry_data = extract_json(retry_text)
                if retry_data and isinstance(retry_data, dict):
                    releases = len(retry_data.get("latest_releases", []))
                    sources = len(retry_data.get("sources", []))
                    print(f"   ✅ Cleanup worked! Got {releases} releases, {sources} sources")
                    return retry_data
            except Exception:
                pass

            if attempt < max_retries - 1:
                wait = 60
                print(f"   🔄 Retrying in {wait}s (attempt {attempt + 2}/{max_retries})...")
                time.sleep(wait)
            else:
                print(f"   ❌ Could not get valid JSON for {company_name} after {max_retries} attempts")
                return {"company": company_name, "error": "Failed to parse results after multiple attempts"}

        except anthropic.RateLimitError:
            wait_time = 90 * (attempt + 1)
            if attempt < max_retries - 1:
                print(f"   ⏳ Rate limited. Waiting {wait_time}s before retry {attempt + 2}/{max_retries}...")
                time.sleep(wait_time)
            else:
                print(f"   ❌ Rate limited after {max_retries} attempts")
                return {"company": company_name, "error": "Rate limit exceeded. Wait a few minutes and try again."}

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"company": company_name, "error": str(e)}

    return {"company": company_name, "error": "Unknown failure"}


def badge_html(confidence):
    """Return a confidence badge."""
    c = str(confidence).lower()
    if c == "verified":
        return '<span class="badge-verified">Verified</span>'
    elif c == "analysis":
        return '<span class="badge-analysis">Analysis</span>'
    return '<span class="badge-unverified">Unverified</span>'


# ============================================================
# HTML REPORT GENERATION
# ============================================================

def generate_html_report(all_research, report_date):
    """Generate HTML report with high contrast, sources, and badges."""

    competitor_sections = ""
    all_sources_html = ""

    for data in all_research:
        if "error" in data:
            competitor_sections += f"""
        <div class="competitor-card" style="--accent:#EF4444;--accent-light:#FCA5A5;--why-bg:#2D1111;--why-text:#FEE2E2;--why-strong:#FCA5A5;--why-border:#7F1D1D;">
            <div class="card-header"><h2>{esc(data.get('company', 'Unknown'))}</h2></div>
            <p style="color:#FCA5A5;padding:20px;text-align:center;">⚠️ Research failed: {esc(data['error'])}<br><br>Run <code>python agent.py {esc(data.get('company',''))}</code> to retry.</p>
        </div>"""
            continue

        company = data.get("company", "Unknown")
        style = BRAND_STYLES.get(company, DEFAULT_STYLE)
        style_attr = ";".join(f"--{k.replace('_','-')}:{v}" for k, v in style.items())

        # Releases
        releases_html = ""
        for r in data.get("latest_releases", [])[:4]:
            badge = badge_html(r.get("confidence", "unverified"))
            source_link = ""
            if r.get("source_url"):
                source_link = f'<p class="release-source">Source: <a href="{esc(r["source_url"])}" target="_blank">{esc(r.get("source_name", "Source"))}</a></p>'
            releases_html += f"""
                <div class="release-item">
                    <div class="release-header">
                        <span class="release-name">{esc(r.get('name', 'N/A'))}</span>
                        <span class="release-date">{esc(r.get('date', ''))}</span>
                    </div>
                    <p class="release-summary">{badge} &nbsp; {esc(r.get('summary', ''))}</p>
                    <p class="release-why"><strong>Why it matters:</strong> {esc(r.get('why_it_matters', ''))}</p>
                    {source_link}
                </div>"""

        # Models
        models_html = ""
        for m in data.get("current_models", [])[:5]:
            models_html += f"""
                <tr>
                    <td class="model-name">{esc(m.get('name', 'N/A'))}</td>
                    <td>{esc(m.get('best_for', ''))}</td>
                    <td class="pricing">{esc(m.get('pricing_note', 'N/A'))}</td>
                </tr>"""

        # Differentiators
        diffs_html = ""
        for d in data.get("key_differentiators", [])[:4]:
            if isinstance(d, dict):
                diffs_html += f"<li>{badge_html(d.get('confidence', 'analysis'))} &nbsp; {esc(d.get('text', ''))}</li>"
            else:
                diffs_html += f"<li>{esc(d)}</li>"

        # Things to try
        tries_html = "".join(f"<li>{esc(t)}</li>" for t in data.get("things_to_try", [])[:4])

        # Talk tracks
        tracks_html = "".join(f"<li>{esc(t)}</li>" for t in data.get("talk_track_ammo", [])[:4])

        # News
        news_html = ""
        for n in data.get("recent_news", [])[:3]:
            if isinstance(n, dict):
                headline = esc(n.get("headline", ""))
                link = f' <a href="{esc(n.get("source_url", ""))}" target="_blank">{esc(n.get("source_name", "Source"))} →</a>' if n.get("source_url") else ""
                news_html += f"<li>{headline}{link}</li>"
            else:
                news_html += f"<li>{esc(n)}</li>"

        # Sources
        src_links = ""
        for s in data.get("sources", []):
            if s.get("url"):
                date_str = f" · {esc(s.get('date', ''))}" if s.get("date") else ""
                src_links += f'<a class="source-link" href="{esc(s["url"])}" target="_blank"><span class="source-title">{esc(s.get("title", "Source"))}</span><span class="source-url">{esc(s["url"])}{date_str}</span></a>'

        if src_links:
            all_sources_html += f'<div class="source-group"><h4>{esc(company)}</h4>{src_links}</div>'

        # Card
        competitor_sections += f"""
        <div class="competitor-card" style="{style_attr}">
            <div class="card-header">
                <h2>{esc(company)}</h2>
                <span class="updated">Updated: {esc(data.get('last_updated', report_date))}</span>
            </div>
            <div class="section"><h3>🚀 Latest Releases</h3>
                <div class="releases">{releases_html or '<p class="empty">No recent releases found</p>'}</div>
            </div>
            <div class="section"><h3>🤖 Current Models</h3>
                <table class="models-table"><thead><tr><th>Model</th><th>Best For</th><th>Pricing</th></tr></thead>
                <tbody>{models_html or '<tr><td colspan="3">No model data found</td></tr>'}</tbody></table>
            </div>
            <div class="two-col">
                <div class="section"><h3>⚡ Key Differentiators</h3>
                    <ul class="diff-list">{diffs_html or '<li>No data</li>'}</ul></div>
                <div class="section"><h3>🧪 Things to Try</h3>
                    <ul class="try-list">{tries_html or '<li>No data</li>'}</ul></div>
            </div>
            <div class="section"><h3>🎯 Sales Talk Track Ammo <span class="badge-analysis" style="vertical-align:middle">Analysis</span></h3>
                <ul class="talk-tracks">{tracks_html or '<li>No data</li>'}</ul></div>
            <div class="section news-section"><h3>📰 Recent Headlines</h3>
                <ul class="news-list">{news_html or '<li>No recent news found</li>'}</ul></div>
        </div>"""

    # Sources section
    sources_section = ""
    if all_sources_html:
        sources_section = f"""
    <div class="sources-section">
        <h2>📚 All Sources</h2>
        <p style="color:#D4D7E0;font-size:0.92rem;margin-bottom:20px;">Factual claims link to sources below. Talk tracks are editorial. Verify before customer conversations.</p>
        {all_sources_html}
    </div>"""

    # Full HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Competitive Intelligence Report — {report_date}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,700&family=JetBrains+Mono:wght@400;500&display=swap');
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'DM Sans',sans-serif; background:#0B0D14; color:#E8EAF0; line-height:1.7; padding:40px 20px; }}
.container {{ max-width:1400px; margin:0 auto; }}
.report-header {{ text-align:center; margin-bottom:48px; padding:48px 40px; background:linear-gradient(135deg,#161929,#0B0D14); border:1px solid #2a2d3e; border-radius:20px; }}
.report-header h1 {{ font-size:2.4rem; font-weight:700; color:#FFF; margin-bottom:8px; }}
.report-header .subtitle {{ font-size:1.1rem; color:#C5C9D6; }}
.report-header .date {{ display:inline-block; margin-top:16px; padding:6px 20px; background:rgba(99,102,241,0.18); border:1px solid rgba(99,102,241,0.4); border-radius:20px; color:#C4CBFC; font-family:'JetBrains Mono',monospace; font-size:0.85rem; }}
.honesty-banner {{ background:#161929; border:1px solid #3B3F54; border-left:4px solid #F59E0B; border-radius:10px; padding:20px 24px; margin-bottom:32px; font-size:0.92rem; color:#E0E2E8; }}
.honesty-banner strong {{ color:#FCD34D; }}
.honesty-banner .legend {{ margin-top:12px; display:flex; flex-wrap:wrap; gap:16px; }}
.honesty-banner .legend-item {{ display:inline-flex; align-items:center; gap:6px; font-size:0.85rem; color:#D1D5DB; }}
.badge-verified {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:0.72rem; font-weight:700; text-transform:uppercase; background:rgba(16,185,129,0.2); color:#6EE7B7; border:1px solid rgba(16,185,129,0.45); }}
.badge-analysis {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:0.72rem; font-weight:700; text-transform:uppercase; background:rgba(99,102,241,0.2); color:#C4CBFC; border:1px solid rgba(99,102,241,0.45); }}
.badge-unverified {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:0.72rem; font-weight:700; text-transform:uppercase; background:rgba(245,158,11,0.2); color:#FCD34D; border:1px solid rgba(245,158,11,0.45); }}
.competitor-card {{ background:#141724; border:1px solid #2E3248; border-radius:16px; padding:36px; margin-bottom:36px; border-top:4px solid var(--accent); }}
.card-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:28px; padding-bottom:16px; border-bottom:1px solid #2E3248; }}
.card-header h2 {{ font-size:1.7rem; font-weight:700; color:var(--accent-light); }}
.updated {{ font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#A0A5B8; }}
.section {{ margin-bottom:28px; }}
.section h3 {{ font-size:1.08rem; font-weight:700; color:#FFFFFF; margin-bottom:14px; padding-bottom:10px; border-bottom:1px solid #252940; }}
.release-item {{ background:#1C2035; border:1px solid #313658; border-radius:10px; padding:20px; margin-bottom:14px; border-left:4px solid var(--accent); }}
.release-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }}
.release-name {{ font-weight:700; color:#FFFFFF; font-size:1rem; }}
.release-date {{ font-family:'JetBrains Mono',monospace; font-size:0.78rem; color:#E0E2E8; background:#2A2F4A; padding:3px 12px; border-radius:4px; }}
.release-summary {{ font-size:0.92rem; color:#D4D7E0; margin-bottom:8px; }}
.release-why {{ font-size:0.9rem; color:var(--why-text); background:var(--why-bg); padding:12px 16px; border-radius:8px; margin-top:10px; border:1px solid var(--why-border); }}
.release-why strong {{ color:var(--why-strong); font-weight:700; }}
.release-source {{ margin-top:10px; font-size:0.82rem; color:#A0A5B8; }}
.release-source a {{ color:#A5B4FC; text-decoration:none; border-bottom:1px dotted rgba(165,180,252,0.4); }}
.release-source a:hover {{ color:#C4CBFC; border-bottom-style:solid; }}
.models-table {{ width:100%; border-collapse:collapse; font-size:0.92rem; }}
.models-table th {{ text-align:left; padding:12px 14px; background:#1C2035; color:#F0F1F5; font-weight:700; font-size:0.82rem; text-transform:uppercase; border-bottom:2px solid #3B3F54; }}
.models-table td {{ padding:12px 14px; border-bottom:1px solid #2A2F4A; color:#D4D7E0; }}
.model-name {{ font-weight:700; color:#FFFFFF; font-family:'JetBrains Mono',monospace; font-size:0.88rem; }}
.pricing {{ font-family:'JetBrains Mono',monospace; color:var(--accent-light); font-size:0.85rem; font-weight:600; }}
.two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:24px; }}
ul {{ list-style:none; padding:0; }}
.diff-list li,.try-list li,.talk-tracks li,.news-list li {{ padding:14px 18px; margin-bottom:8px; background:#1C2035; border:1px solid #2A2F4A; border-radius:8px; font-size:0.92rem; border-left:4px solid var(--accent); color:#E8EAF0; }}
.talk-tracks li {{ background:rgba(16,185,129,0.08); border-color:#1E3A2E; border-left-color:#10B981; }}
.news-list li {{ border-left-color:#6B7280; color:#D4D7E0; }}
.news-list li a {{ color:#A5B4FC; text-decoration:none; font-size:0.82rem; }}
.sources-section {{ background:#141724; border:1px solid #2E3248; border-radius:16px; padding:36px; margin-bottom:32px; }}
.sources-section h2 {{ font-size:1.3rem; color:#FFF; margin-bottom:20px; padding-bottom:12px; border-bottom:1px solid #2E3248; }}
.source-group {{ margin-bottom:24px; }}
.source-group h4 {{ color:#F0F1F5; font-size:0.92rem; margin-bottom:12px; font-weight:700; text-transform:uppercase; }}
.source-link {{ display:block; padding:10px 16px; margin-bottom:6px; background:#1C2035; border-radius:6px; text-decoration:none; border:1px solid #2A2F4A; }}
.source-link:hover {{ border-color:#A5B4FC; background:#222744; }}
.source-link .source-title {{ color:#E8EAF0; font-weight:600; }}
.source-link .source-url {{ color:#A5B4FC; font-family:'JetBrains Mono',monospace; font-size:0.75rem; display:block; margin-top:3px; }}
.empty {{ color:#6B7280; font-style:italic; }}
.footer {{ text-align:center; padding:32px; color:#A0A5B8; font-size:0.88rem; }}
@media (max-width:768px) {{ .two-col {{ grid-template-columns:1fr; }} .card-header {{ flex-direction:column; gap:8px; }} }}
@media print {{ body {{ background:#fff; color:#111; }} .competitor-card {{ border:1px solid #ccc; background:#fff; }} .release-item,.diff-list li,.try-list li,.talk-tracks li {{ background:#f5f5f5; color:#111; }} .release-why {{ background:#eef4ff !important; color:#111 !important; }} .section h3,.card-header h2 {{ color:#111; }} }}
</style>
</head>
<body>
<div class="container">
    <div class="report-header">
        <h1>🕵️ AI Competitive Intelligence Report</h1>
        <p class="subtitle">OpenAI vs Anthropic (Claude) vs Microsoft Copilot</p>
        <span class="date">Week of {report_date}</span>
    </div>
    <div class="honesty-banner">
        <strong>⚠️ Honesty Notice:</strong> Auto-generated on {report_date} using Claude API with live web search. Every claim is tagged with a confidence level. <strong>Talk tracks are editorial suggestions</strong>, not verified marketing claims. Always verify sources before customer conversations.
        <div class="legend">
            <span class="legend-item"><span class="badge-verified">Verified</span> Found in linked source</span>
            <span class="legend-item"><span class="badge-analysis">Analysis</span> Editorial interpretation</span>
            <span class="legend-item"><span class="badge-unverified">Unverified</span> Not confirmed officially</span>
        </div>
    </div>
    {competitor_sections}
    {sources_section}
    <div class="footer">
        <p>Generated by Competitive Intel Agent · Built for tech sales professionals</p>
        <p style="margin-top:8px">⚠️ Talk tracks are editorial. Always verify linked sources before customer conversations.</p>
    </div>
</div>
</body>
</html>"""

    return html


# ============================================================
# DATA MANAGEMENT
# ============================================================

def load_existing_data(report_date):
    """Load previously saved research data for today."""
    json_path = f"reports/competitive-intel-{report_date}.json"
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []


def save_and_generate(all_research, report_date):
    """Save JSON + generate HTML report."""
    os.makedirs("reports", exist_ok=True)

    json_filename = f"reports/competitive-intel-{report_date}.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(all_research, f, indent=2, ensure_ascii=False)

    html = generate_html_report(all_research, report_date)
    filename = f"reports/competitive-intel-{report_date}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    with open("reports/latest.html", "w", encoding="utf-8") as f:
        f.write(html)

    return filename, json_filename


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("🕵️  COMPETITIVE INTELLIGENCE AGENT")
    print("=" * 60)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n❌ No ANTHROPIC_API_KEY found!")
        print("\nWindows: Search 'environment variables' in Start menu,")
        print("add ANTHROPIC_API_KEY with your key, restart PowerShell.")
        print("\nGet a key at: https://console.anthropic.com/")
        sys.exit(1)

    report_date = datetime.now().strftime("%Y-%m-%d")
    competitor_names = list(COMPETITORS.keys())

    # Parse argument
    target = None
    if len(sys.argv) > 1:
        arg = " ".join(sys.argv[1:])

        if arg.lower() == "list":
            print("\n📋 Available competitors:\n")
            for i, name in enumerate(competitor_names, 1):
                print(f"   {i}. {name}")
            print(f"\n   python agent.py 1        ← research one")
            print(f"   python agent.py           ← research all")
            print(f"   python agent.py report    ← rebuild report")
            return

        if arg.lower() == "report":
            existing = load_existing_data(report_date)
            if not existing:
                print(f"\n❌ No data for {report_date}. Run a competitor first.")
                return
            print(f"\n📝 Rebuilding report from {len(existing)} competitor(s)...")
            filename, _ = save_and_generate(existing, report_date)
            print(f"✅ Done: {filename}")
            return

        if arg.isdigit():
            idx = int(arg) - 1
            if 0 <= idx < len(competitor_names):
                target = competitor_names[idx]
            else:
                print(f"\n❌ No competitor #{arg}. Use 1-{len(competitor_names)}.")
                return
        else:
            for name in competitor_names:
                if arg.lower() in name.lower():
                    target = name
                    break
            if not target:
                print(f"\n❌ '{arg}' not found. Run: python agent.py list")
                return

    targets = {target: COMPETITORS[target]} if target else COMPETITORS
    client = anthropic.Anthropic(api_key=api_key)

    print(f"\n📅 Report date: {report_date}")
    if target:
        print(f"🎯 Researching: {target}\n")
    else:
        print(f"🎯 Researching ALL {len(targets)} competitors\n")

    existing_data = load_existing_data(report_date)
    new_results = []
    target_list = list(targets.items())

    for i, (name, info) in enumerate(target_list):
        data = research_competitor(client, name, info)
        new_results.append(data)
        if not target and i < len(target_list) - 1:
            print(f"\n   ⏳ Waiting 90s for rate limits...", end="", flush=True)
            time.sleep(90)
            print(" done.")

    # Merge with existing data
    all_research = []
    new_companies = {d.get("company") for d in new_results}
    for old in existing_data:
        if old.get("company") not in new_companies:
            all_research.append(old)
    all_research.extend(new_results)

    name_order = {n: i for i, n in enumerate(competitor_names)}
    all_research.sort(key=lambda d: name_order.get(d.get("company", ""), 999))

    print("\n📝 Generating report...")
    filename, json_filename = save_and_generate(all_research, report_date)

    done = sum(1 for d in all_research if "error" not in d)
    print(f"\n✅ {done}/{len(all_research)} competitors done.")
    print(f"   📊 Report: {filename}")
    print(f"   📦 Data:   {json_filename}")
    print(f"\n💡 Open:  start reports\\latest.html")

    missing = [n for n in competitor_names
               if not any(d.get("company") == n and "error" not in d for d in all_research)]
    if missing:
        print(f"\n📋 Still need:")
        for m in missing:
            print(f"   python agent.py {competitor_names.index(m) + 1}    ← {m}")


if __name__ == "__main__":
    main()
