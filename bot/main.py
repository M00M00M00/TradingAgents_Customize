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


async def call_api(symbol: str, trade_date: str, model_key: Optional[str], stop_loss_pct: float) -> str:
    api_base = os.getenv("API_BASE_URL", "http://127.0.0.1:8001")
    url = f"{api_base}/signal"
    payload = {"symbol": symbol, "trade_date": trade_date, "model": model_key, "stop_loss_pct": stop_loss_pct}

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
    stop_loss_pct="Stop loss percent (e.g., 0.5 for 0.5%)"
)
@app_commands.choices(
    model=[app_commands.Choice(name=key, value=key) for key in ALLOWED_MODELS.keys()]
)
async def position_command(interaction: discord.Interaction, symbol: str, stop_loss_pct: float = 0.5, model: Optional[str] = None):
    await interaction.response.defer(thinking=True)
    trade_date = dt.date.today().strftime("%Y-%m-%d")

    try:
        raw_summary = await call_api(symbol, trade_date, model, stop_loss_pct)

        # Clean summary: drop trailing empty heading lines like "Lessons Learned ..."
        lines = [ln.rstrip() for ln in raw_summary.splitlines()]
        cleaned = []
        for idx, ln in enumerate(lines):
            lower_ln = ln.strip().lower()
            is_heading_only = lower_ln.startswith(("lessons learned", "lessons", "risk management"))
            next_nonempty = None
            for j in range(idx + 1, len(lines)):
                if lines[j].strip():
                    next_nonempty = lines[j]
                    break
            if is_heading_only and (next_nonempty is None or not next_nonempty.strip()):
                continue
            cleaned.append(ln)
        summary = "\n".join(cleaned).strip()

        # Parse decision token if present in summary (pattern: "Final Decision: XYZ")
        decision_token = "NEUTRAL"
        for line in summary.splitlines():
            if "Final Decision" in line:
                decision_token = line.split(":")[-1].strip().upper()
                break

        color_map = {
            "LONG": discord.Color.green(),
            "SHORT": discord.Color.red(),
            "NEUTRAL": discord.Color.light_grey(),
        }
        embed_color = color_map.get(decision_token, discord.Color.blurple())

        embed = discord.Embed(
            title=f"Final Decision: {decision_token}",
            description=summary[:3900],  # embed description limit safety
            color=embed_color,
        )
        embed.add_field(name="Symbol", value=symbol, inline=True)
        embed.add_field(name="Model", value=model or f"default ({DEFAULT_MODEL_KEY})", inline=True)
        embed.add_field(name="Stop Loss %", value=str(stop_loss_pct), inline=True)

        await interaction.followup.send(embed=embed)
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
