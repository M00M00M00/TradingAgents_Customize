import datetime as dt
import os
from typing import Callable, Tuple

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph
from bot.config import resolve_model


class SignalRequest(BaseModel):
    symbol: str = Field(default="BTC/USDT", description="Perp symbol, e.g. BTC/USDT")
    trade_date: str | None = Field(
        default=None, description="YYYY-MM-DD; defaults to today if not provided"
    )
    model: str | None = Field(
        default=None,
        description="LLM model key (gpt-5.1, gpt-5-mini, gpt-5-nano, o4-mini, gpt-4.1-mini)",
    )
    debug: bool = Field(default=False, description="Enable LangGraph debug mode")


class SignalResponse(BaseModel):
    decision: str
    summary: str
    raw_decision: str


def default_graph_factory(config) -> TradingAgentsGraph:
    return TradingAgentsGraph(selected_analysts=["market"], debug=config.get("debug", False), config=config)


def create_app(graph_factory: Callable = default_graph_factory) -> FastAPI:
    app = FastAPI(title="TradingAgents Crypto Perp API", version="0.1.0")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/signal", response_model=SignalResponse)
    def signal(req: SignalRequest):
        trade_date = req.trade_date or dt.date.today().strftime("%Y-%m-%d")
        deep, quick = resolve_model(req.model)

        config = DEFAULT_CONFIG.copy()
        config["deep_think_llm"] = deep
        config["quick_think_llm"] = quick
        config["data_vendors"]["core_stock_apis"] = "ccxt"
        config["data_vendors"]["technical_indicators"] = "ccxt"
        config["debug"] = req.debug

        try:
            graph = graph_factory(config)
            final_state, decision_text = graph.propagate(req.symbol, trade_date)
            decision = graph.process_signal(decision_text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Graph execution failed: {e}")

        summary_parts = [f"Final Decision: {decision}"]
        if final_state.get("investment_plan"):
            summary_parts.append(f"Research Plan:\n{final_state['investment_plan']}")
        if final_state.get("trader_investment_plan"):
            summary_parts.append(f"Trader Plan:\n{final_state['trader_investment_plan']}")
        if final_state.get("final_trade_decision"):
            summary_parts.append(f"Risk Judge:\n{final_state['final_trade_decision']}")

        return SignalResponse(
            decision=decision,
            summary="\n\n".join(summary_parts),
            raw_decision=decision_text,
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", "8001"))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=False)
