import asyncio
import datetime as dt
import os
import io
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

    # Remove request timeout to allow long-running analysis (Discord hard limit ~15 minutes)
    timeout = aiohttp.ClientTimeout(total=None)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload) as resp:
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

        summary = _clean_summary(raw_summary)
        decision_token = _extract_decision(summary)
        embed = _build_embed(
            summary=summary,
            decision=decision_token,
            symbol=symbol,
            model=model or f"default ({DEFAULT_MODEL_KEY})",
            stop_loss_pct=stop_loss_pct,
        )

        # Attach full analysis as a file to avoid Discord embed truncation limits
        file = discord.File(io.BytesIO(raw_summary.encode("utf-8")), filename="analysis.txt")
        await interaction.followup.send(embed=embed, file=file)
    except Exception as e:
        await interaction.followup.send(f"Error while generating decision: {e}")


def _clean_summary(raw: str) -> str:
    """Remove empty heading-only lines like 'Lessons Learned'."""
    lines = [ln.rstrip() for ln in raw.splitlines()]
    cleaned = []
    for idx, ln in enumerate(lines):
        lower_ln = ln.strip().lower()
        is_heading_only = lower_ln.startswith(
            ("lessons learned", "lessons", "risk management")
        )
        # skip repeated "Final Decision" lines to reduce duplication
        if lower_ln.startswith("final decision"):
            continue
        next_nonempty = None
        for j in range(idx + 1, len(lines)):
            if lines[j].strip():
                next_nonempty = lines[j]
                break
        if is_heading_only and (next_nonempty is None or not next_nonempty.strip()):
            continue
        cleaned.append(ln)
    return "\n".join(cleaned).strip()


def _extract_decision(summary: str) -> str:
    decision_token = "NEUTRAL"
    for line in summary.splitlines():
        if "Final Decision" in line:
            decision_token = line.split(":")[-1].strip().upper()
            break
    return decision_token


def _build_embed(summary: str, decision: str, symbol: str, model: str, stop_loss_pct: float) -> discord.Embed:
    color_map = {
        "LONG": discord.Color.green(),
        "SHORT": discord.Color.red(),
        "NEUTRAL": discord.Color.light_grey(),
    }
    embed_color = color_map.get(decision, discord.Color.blurple())

    sections = _split_sections(summary)

    embed = discord.Embed(
        title=f"Final Decision: {decision}",
        description=sections.pop("Summary", "")[:800],
        color=embed_color,
    )
    embed.add_field(name="Symbol", value=symbol, inline=True)
    embed.add_field(name="Model", value=model, inline=True)
    embed.add_field(name="Stop Loss %", value=str(stop_loss_pct), inline=True)

    # Add key sections as fields with truncation
    for key in ["Research Plan", "Trader Plan", "Risk Judge", "Strategic Actions"]:
        if key in sections and sections[key].strip():
            embed.add_field(
                name=key,
                value=sections[key].strip()[:900],  # keep under 1024 limit with buffer
                inline=False,
            )

    return embed


def _split_sections(summary: str) -> dict:
    """
    Split summary into sections based on known headings.
    Returns dict with keys like Research Plan, Trader Plan, Risk Judge, Summary.
    """
    headings = ["Research Plan", "Trader Plan", "Risk Judge", "Strategic Actions"]
    sections = {h: "" for h in headings}
    sections["Summary"] = ""

    current = "Summary"
    for line in summary.splitlines():
        stripped = line.strip()
        if any(stripped.startswith(h) for h in headings):
            for h in headings:
                if stripped.startswith(h):
                    current = h
                    break
            # skip the heading line itself
            continue
        sections[current] += line + "\n"

    # trim
    for k in sections:
        sections[k] = sections[k].strip()
    return sections


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
