from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.agents.utils.agent_utils import get_stock_data, get_indicators
from tradingagents.dataflows.config import get_config


def create_market_analyst(llm):

    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        tools = [
            get_stock_data,
            get_indicators,
        ]

        system_message = (
            "You are a crypto trading assistant focusing on Bybit USDT perpetuals. "
            "Analyze short-term price action with 15m trigger and 1h context. "
            "Use get_stock_data to fetch OHLCV (default 15m, you may also fetch 1h), "
            "then get_indicators to retrieve the core bundle: SMA(7/25/99), RSI14, "
            "Bollinger(20,2), MACD(12/26/9). Prioritize:\n"
            "- 1h bias vs SMA99 and SMA stack (7/25/99)\n"
            "- 15m pattern type: trend pullback, range breakout, reversal at S/R, squeeze expansion\n"
            "- Momentum/divergence: RSI, MACD\n"
            "- Volatility state: Bollinger squeeze/expansion\n"
            "- Volume/impulse context from recent candles\n"
            "Report actionable insights for LONG/SHORT/NEUTRAL with specific levels "
            "(recent swing, band, or obvious liquidity zone). Do not hand-wave with 'mixed'; "
            "be concrete and concise. Append a Markdown table summarizing bias, pattern, "
            "levels, momentum, volatility, and confidence."
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. The company we want to look at is {ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content
       
        return {
            "messages": [result],
            "market_report": report,
        }

    return market_analyst_node
