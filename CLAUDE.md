# Claude Code Instructions

## About
AI competitive intelligence agent. Researches OpenAI, Anthropic, and Microsoft Copilot via Claude API + web search. Generates styled HTML reports with sources.

## Run the Agent
```bash
python agent.py 1          # OpenAI
python agent.py 2          # Anthropic (Claude)
python agent.py 3          # Microsoft Copilot
python agent.py            # All (with rate limit pauses)
python agent.py list       # Show competitors
python agent.py report     # Rebuild report from saved data
```

Reports save to `reports/latest.html` and dated archives.

## Add a Competitor
Edit `COMPETITORS` dict in `agent.py`. Optionally add colors to `BRAND_STYLES`.

## Key Files
- `agent.py` — Main script (model, prompts, HTML template)
- `reports/` — Generated output (gitignored except sample)
- `run.bat` — Windows one-click runner (runs all 3 with pauses)
