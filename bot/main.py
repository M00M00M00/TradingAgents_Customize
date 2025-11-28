import asyncio
import datetime as dt
import os
from typing import Optional

import aiohttp
import discord
from discord import app_commands
from dotenv import load_dotenv

from bot.config import resolve_model, ALLOWED_MODELS, DEFAULT_MODEL_KEY

load_dotenv()

INTENTS = discord.Intents.default()
BOT = discord.Client(intents=INTENTS)
TREE = app_commands.CommandTree(BOT)


async def call_api(symbol: str, trade_date: str, model_key: Optional[str]) -> str:
    api_base = os.getenv("API_BASE_URL", "http://127.0.0.1:8001")
    url = f"{api_base}/signal"
    payload = {"symbol": symbol, "trade_date": trade_date, "model": model_key}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=300) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"API error {resp.status}: {text}")
            data = await resp.json()
            return data.get("summary", "No summary returned")


@TREE.command(
    name="position",
    description="Get crypto perp position decision (LONG/SHORT/NEUTRAL) via local API.",
)
@app_commands.describe(
    symbol="Perp symbol, e.g. BTC/USDT",
    model=f"LLM model ({', '.join(ALLOWED_MODELS.keys())}), default {DEFAULT_MODEL_KEY}",
)
async def position_command(interaction: discord.Interaction, symbol: str, model: Optional[str] = None):
    await interaction.response.defer(thinking=True)
    trade_date = dt.date.today().strftime("%Y-%m-%d")

    try:
        result = await call_api(symbol, trade_date, model)
        await interaction.followup.send(result[:1800])
    except Exception as e:
        await interaction.followup.send(f"Error while generating decision: {e}")


async def main():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN is not set in environment.")
    await BOT.login(token)
    await BOT.connect()


@BOT.event
async def on_ready():
    try:
        await TREE.sync()
        print(f"Bot ready. Logged in as {BOT.user}")
    except Exception as e:
        print(f"Command tree sync failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
