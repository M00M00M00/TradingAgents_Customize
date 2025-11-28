<p align="center">
  <img src="assets/TauricResearch.png" style="width: 60%; height: auto;">
</p>

<div align="center" style="line-height: 1;">
  <a href="https://arxiv.org/abs/2412.20138" target="_blank"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2412.20138-B31B1B?logo=arxiv"/></a>
  <a href="https://discord.com/invite/hk9PGKShPK" target="_blank"><img alt="Discord" src="https://img.shields.io/badge/Discord-TradingResearch-7289da?logo=discord&logoColor=white&color=7289da"/></a>
  <a href="./assets/wechat.png" target="_blank"><img alt="WeChat" src="https://img.shields.io/badge/WeChat-TauricResearch-brightgreen?logo=wechat&logoColor=white"/></a>
  <a href="https://x.com/TauricResearch" target="_blank"><img alt="X Follow" src="https://img.shields.io/badge/X-TauricResearch-white?logo=x&logoColor=white"/></a>
  <br>
  <a href="https://github.com/TauricResearch/" target="_blank"><img alt="Community" src="https://img.shields.io/badge/Join_GitHub_Community-TauricResearch-14C290?logo=discourse"/></a>
</div>

---

# TradingAgents (Crypto Perpetuals Edition)

LangGraph-orchestrated multi-agent workflow for Bybit USDT perpetuals (default BTC/USDT). Focused on short-term setups with 15m triggers and 1h context. Uses OHLCV/indicators/orderbook/funding/OI to output LONG/SHORT/NEUTRAL with tight risk (0.5–1%) and RR 1–10 (prefers 1.5–2.5). News/fundamentals are disabled by default to cut noise (can be enabled separately).

<div align="center">
<a href="https://www.star-history.com/#TauricResearch/TradingAgents&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=TauricResearch/TradingAgents&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=TauricResearch/TradingAgents&type=Date" />
   <img alt="TradingAgents Star History" src="https://api.star-history.com/svg?repos=TauricResearch/TradingAgents&type=Date" style="width: 80%; height: auto;" />
 </picture>
</a>
</div>

<div align="center">
🚀 [Overview](#overview) | ⚡ [Install & Run](#install--run) | 🧭 [Architecture](#architecture) | 🧪 [Tests](#tests) | 🤝 [Contributing](#contributing) | 📄 [Citation](#citation)
</div>

## Overview
- Default symbol/timeframes: `BTC/USDT`, trigger `15m`, context `1h`
- Data: CCXT (Bybit) OHLCV, SMA(7/25/99), RSI14, Bollinger(20,2), MACD(12/26/9), orderbook imbalance (±0.5%/±1.0%), funding rate, open interest change
- Agents: Market Analyst → Bull/Bear debate → Research Manager → Trader → Risk team → Final LONG/SHORT/NEUTRAL
- Risk: target 0.5–1% account risk, RR 1–10 (prefer 1.5–2.5)
- Defaults: news/fundamentals off

## Architecture
```mermaid
flowchart LR
    A[User input: symbol, date] --> B[Market Analyst (15m/1h OHLCV + indicators)]
    B --> C[Bull Researcher]
    B --> D[Bear Researcher]
    C --> E[Research Manager (LONG/SHORT/NEUTRAL + plan)]
    D --> E
    E --> F[Trader (entry/SL/TP/RR)]
    F --> G[Risk Debate (Risky/Safe/Neutral)]
    G --> H[Risk Judge (final decision)]
```

> Want updated visuals? Add your own PNG/SVG under `assets/` (e.g., `assets/crypto_flow.png`) and embed it here. Mermaid above renders on GitHub by default.

## Install & Run

Clone:
```bash
git clone https://github.com/TauricResearch/TradingAgents.git
cd TradingAgents
```

Env:
```bash
conda create -n tradingagents python=3.10
conda activate tradingagents
pip install -r requirements.txt
```

Keys:
```bash
export OPENAI_API_KEY=your_openai_key
```
(Public Bybit data works without API keys; private endpoints would need `BYBIT_API_KEY/SECRET` but are not required here.)

CLI:
```bash
python -m cli.main
```
Select symbol (default BTC/USDT), date, LLM, and stream the 15m/1h analysis.

API (default port 8001 to avoid conflicts):
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8001
```

Discord bot (calls the local API):
```bash
python -m bot.main
```
Ensure `.env` has `DISCORD_BOT_TOKEN` and `API_BASE_URL` (default http://127.0.0.1:8001).

## Package Example
```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["data_vendors"]["core_stock_apis"] = "ccxt"
config["data_vendors"]["technical_indicators"] = "ccxt"
config["max_debate_rounds"] = 1
config["max_risk_discuss_rounds"] = 1

ta = TradingAgentsGraph(debug=True, config=config)
_, decision = ta.propagate("BTC/USDT", "2024-11-01")
print(decision)
```

## Logging
- `eval_results/{ticker}/TradingAgentsStrategy_logs/full_states_log_{trade_date}.json`: final state snapshot.
- CLI run: `results/{ticker}/{date}/message_tool.log` plus per-section markdown under `results/{ticker}/{date}/reports/`.

## Tests
```bash
pytest -q
```
Included:
- OHLCV formatting with a dummy ccxt client
- Indicator calculation and summary generation

## Contributing
Contributions welcome (bugfixes, docs, features). If you create updated diagrams/screenshots for the crypto flow, drop them in `assets/` and embed them above.

## Citation
```
@misc{xiao2025tradingagentsmultiagentsllmfinancial,
      title={TradingAgents: Multi-Agents LLM Financial Trading Framework}, 
      author={Yijia Xiao and Edward Sun and Di Luo and Wei Wang},
      year={2025},
      eprint={2412.20138},
      archivePrefix={arXiv},
      primaryClass={q-fin.TR},
      url={https://arxiv.org/abs/2412.20138}, 
}
```
