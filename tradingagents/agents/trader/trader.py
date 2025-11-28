import functools
import time
import json


def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found."

        context = {
            "role": "user",
            "content": f"Based on a comprehensive analysis by a team of analysts, here is a trading plan tailored for {company_name} (Bybit USDT perp). "
            f"The plan reflects short-term confluence from 15m/1h OHLCV, SMA(7/25/99), RSI, Bollinger, MACD, orderbook, funding, and OI. "
            f"Use this plan to produce a concrete LONG/SHORT/NEUTRAL decision with entry/SL/TP and RR.\n\nProposed Plan: {investment_plan}\n\n"
            "Respect tight risk (0.5-1% account risk) and keep RR between 1 and 10.",
        }

        messages = [
            {
                "role": "system",
                "content": f"""You are a trading agent analyzing crypto market data to make short-term decisions. Provide a specific recommendation: LONG, SHORT, or NEUTRAL. 
Return one decision with entry idea, SL (~0.5-1% risk), TP for RR 1-10 (prefer 1.5-2.5). 
Always conclude with 'FINAL TRANSACTION PROPOSAL: **LONG/SHORT/NEUTRAL**'. 
Use lessons from past decisions to avoid repeating mistakes: {past_memory_str}""",
            },
            context,
        ]

        result = llm.invoke(messages)

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
