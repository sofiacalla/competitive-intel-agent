# 🕵️ Competitive Intelligence Agent

An AI-powered agent that automatically researches **OpenAI**, **Anthropic (Claude)**, and **Microsoft Copilot** using live web search, then generates a one-pager with latest releases, model comparisons, source references, and sales talk tracks.

Built with the [Anthropic Claude API](https://docs.anthropic.com/) + web search tool. Designed for **tech sales professionals, Solution Engineers, and Account Managers** who need to stay current on the AI landscape.

![Sample Report](https://img.shields.io/badge/output-HTML_Report-blue) ![Cost](https://img.shields.io/badge/cost-%240.03--0.05%2Frun-green) ![Python](https://img.shields.io/badge/python-3.10%2B-yellow)

---

## What It Does

```
You run: python agent.py 1
Agent calls Claude API → Claude searches the live web → Returns structured data → Generates HTML report
```

The report includes:
- **Latest releases** with dates, descriptions, and why they matter
- **Model/product lineup** with pricing (when available)
- **Key differentiators** vs competitors
- **Things to try** — hands-on demos and features to test
- **Sales talk track ammunition** — suggested positioning (marked as editorial)
- **Source links** for every factual claim
- **Confidence badges** (Verified / Analysis / Unverified) so you know what's confirmed

[**→ See a sample report**](reports/sample-report.html) (download and open in your browser)

---

## Quick Start (Windows)

### 1. Install Python
Download from [python.org/downloads](https://python.org/downloads)

> ⚠️ **CRITICAL:** Check **"Add python.exe to PATH"** during installation. If you miss this, nothing will work.

### 2. Install the SDK
Open PowerShell and run:
```powershell
pip install anthropic
```

### 3. Get your API key
1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up → Click **API Keys** → **Create Key**
3. Copy the key (starts with `sk-ant-...`)
4. Add $5 in credits under **Billing** (gives you 100+ runs)

### 4. Set the key as an environment variable
Press `Win+S` → search **"environment variables"** → Click **"Edit the system environment variables"** → **"Environment Variables..."** → Under **User variables** → **"New..."**

| Field | Value |
|-------|-------|
| Variable name | `ANTHROPIC_API_KEY` |
| Variable value | `sk-ant-your-key-here` |

Click OK → OK → OK. **Close and reopen PowerShell.**

### 5. Clone and run
```powershell
# Click the green "Code" button on this repo → Copy the URL
git clone <paste-url-here>
cd competitive-intel-agent
python agent.py 1
```

Wait ~1 minute. Then:
```powershell
python agent.py 2
```

Wait ~2 minutes. Then:
```powershell
python agent.py 3
```

Open the report:
```powershell
start reports\latest.html
```

---

## Quick Start (Mac/Linux)

```bash
# Install SDK
pip install anthropic

# Set API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# To make it permanent:
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.zshrc && source ~/.zshrc

# Clone and run (use the green "Code" button on GitHub to copy URL)
git clone <paste-url-here>
cd competitive-intel-agent
python3 agent.py 1     # OpenAI
python3 agent.py 2     # Anthropic
python3 agent.py 3     # Microsoft

# Open report
open reports/latest.html
```

---

## Usage

```
python agent.py              Research ALL competitors (with pauses between each)
python agent.py 1            Research OpenAI only
python agent.py 2            Research Anthropic (Claude) only
python agent.py 3            Research Microsoft Copilot only
python agent.py list         Show all competitors with numbers
python agent.py report       Rebuild HTML report from saved data
```

**Recommended workflow:** Run one competitor at a time to stay under API rate limits. Data accumulates — each run adds to the same daily report.

```powershell
python agent.py 1              # ~1 min, researches OpenAI
# wait a couple minutes
python agent.py 2              # ~1 min, researches Claude, keeps OpenAI data
# wait a couple minutes
python agent.py 3              # ~1 min, researches Microsoft, report now has all 3
start reports\latest.html      # open the full report
```

---

## Output

Reports are saved to the `reports/` folder:

```
reports/
├── competitive-intel-2026-03-15.html   ← This week's report
├── competitive-intel-2026-03-15.json   ← Raw data (for coding projects)
└── latest.html                         ← Always the most recent
```

Each week builds an archive. Run it every Monday for a running record of the AI landscape.

---

## Cost

| Model | Cost per run | $5 budget |
|-------|-------------|-----------|
| **Haiku** (default) | ~$0.03–0.05 | **100+ runs** (~2 years weekly) |
| Sonnet (higher quality) | ~$0.20–0.30 | ~20 runs (~5 months weekly) |

To switch to Sonnet for higher quality reports, edit line 86 in `agent.py`:
```python
# MODEL = "claude-haiku-4-5-20251001"        # Comment this out
MODEL = "claude-sonnet-4-20250514"            # Uncomment this
```

---

## Add Your Own Competitors

Open `agent.py` and add to the `COMPETITORS` dictionary:

```python
"Salesforce": {
    "products": ["Agentforce", "Einstein", "Data Cloud"],
    "urls_to_check": [
        "salesforce.com/agentforce",
        "salesforce.com/news"
    ],
    "focus_areas": [
        "Agentforce platform updates",
        "Einstein AI capabilities",
        "Data Cloud integrations",
        "enterprise customer wins"
    ]
},
```

Then run:
```powershell
python agent.py Salesforce
```

Other ideas: GitHub, SAP, HubSpot, Google Gemini, AWS Bedrock — just add the config.

---

## Schedule Weekly Runs

### Windows (Task Scheduler)
1. Press `Win+S` → search **"Task Scheduler"**
2. **Create Basic Task** → Name: `Weekly AI Intel Report`
3. Trigger: **Weekly** → Monday → 8:00 AM
4. Action: **Start a program**
   - Program: `python`
   - Arguments: `C:\path\to\competitive-intel-agent\agent.py`
   - Start in: `C:\path\to\competitive-intel-agent`

### Mac/Linux (cron)
```bash
crontab -e
# Add: runs every Monday at 8am
0 8 * * 1 cd ~/competitive-intel-agent && python3 agent.py >> cron.log 2>&1
```

---

## How It Works

1. **You pick a competitor** (`python agent.py 1`)
2. **Script calls the Claude API** with the `web_search` tool enabled
3. **Claude autonomously searches the web** — it decides what to search, reads results, and searches again
4. **Claude returns structured JSON** with releases, models, differentiators, sources, and talk tracks
5. **Script renders JSON → HTML report** with the high-contrast dark theme
6. **Data accumulates** — run each competitor separately, the report merges everything

```
┌─────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│  agent.py   │───▶│ Claude API │───▶│ Web Search │───▶│   JSON     │
│ (you run)   │    │  (Haiku)   │    │  (live)    │    │ (structured│
└─────────────┘    └────────────┘    └────────────┘    └─────┬──────┘
                                                             │
                                                    ┌────────▼──────┐
                                                    │  HTML Report  │
                                                    │ (dark theme,  │
                                                    │  sources,     │
                                                    │  badges)      │
                                                    └───────────────┘
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `'python' is not recognized` | Reinstall Python, CHECK "Add to PATH" |
| `ModuleNotFoundError: anthropic` | `pip install anthropic` or `python -m pip install anthropic` |
| `AuthenticationError` | Check: `echo $env:ANTHROPIC_API_KEY` (PowerShell) — if blank, set it again |
| `RateLimitError` | Wait 2 minutes between runs. Run one competitor at a time. |
| JSON parse error | Agent retries automatically. If persistent, run again. |
| Empty report sections | Normal on slow news weeks. Try running again. |
| `agent.py.txt` instead of `agent.py` | Windows trap — rename: `Rename-Item agent.py.txt agent.py` |

---

## Project Structure

```
competitive-intel-agent/
├── agent.py                  # Main agent script
├── run.bat                   # Windows double-click runner
├── CLAUDE.md                 # Instructions for Claude Code
├── README.md                 # This file
├── LICENSE                   # MIT License
├── .gitignore                # Keeps secrets and outputs out of git
└── reports/
    └── sample-report.html    # Example output (open in browser)
```

---

## Security

- **No API keys are stored in the code.** The key is read from your environment variable.
- **The `.gitignore` excludes** generated reports, `.env` files, and key files.
- **Never commit your API key.** If you accidentally do, revoke it immediately at [console.anthropic.com](https://console.anthropic.com/) and create a new one.

---

## License

MIT — use it, modify it, share it. See [LICENSE](LICENSE).

---

## Why I Built This

I'm preparing for Solution Engineer and Account Manager roles at companies like Salesforce, Microsoft, OpenAI, Anthropic, GitHub, and HubSpot. This project demonstrates:

- **API skills** — Claude API with tool use (web search) and structured outputs
- **Agentic thinking** — autonomous web research with decision-making
- **Product sense** — understanding what matters to enterprise buyers
- **Sales empathy** — talk tracks, competitive positioning, and differentiators

The same architecture works for lead enrichment, deal research, CRM intelligence, and any workflow where AI + web data = business value.
