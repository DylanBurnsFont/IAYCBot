"""
Bulk role assignment script (CSV version).

Reads userid,roleid pairs from assignments.csv and gives each user the
specific role listed next to them. Different users can get different roles
in the same run.

Usage:
    1. pip install -r requirements.txt --break-system-packages
    2. cp .env.example .env   (then fill in BOT_TOKEN, GUILD_ID)
    3. Fill in assignments.csv with your userid,roleid pairs
    4. python assign_roles.py

A results.log file will be written with the outcome for every row.
"""

import asyncio
import csv
import os
import sys
from pathlib import Path

import discord
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
DELAY_SECONDS = float(os.getenv("DELAY_SECONDS", "1"))

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "wgAllocation.csv"
LOG_FILE = BASE_DIR / "results.log"

roleDict = {
    "1492929286716260432": "Agony",
    "1492929434007769118": "Asterix",
    "1492929228524490904": "Beans",
    "1492929455608299521": "Clanker",
    "1492929483194499293": "eSparkle",
    "1492929516564250674": "Irn-bru",
    "1492929739655086293": "Poets Society",
    "1492929770474832013": "Sigma",
    "1492929790867669134": "Space bugs",
}

def validate_env() -> None:
    missing = [name for name, val in (
        ("BOT_TOKEN", BOT_TOKEN),
        ("GUILD_ID", GUILD_ID),
    ) if not val]
    if missing:
        print(
            f"Missing required .env values: {', '.join(missing)}. "
            "Copy .env.example to .env and fill them in."
        )
        sys.exit(1)


def load_assignments() -> list[tuple[str, str]]:
    """Returns a list of (user_id, role_id) string tuples, in file order."""
    if not CSV_FILE.exists():
        print(f"Could not find {CSV_FILE}. Create it with a userid,roleid header and rows.")
        sys.exit(1)

    assignments = []
    with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = {(h or "").strip().lower() for h in (reader.fieldnames or [])}
        if not {"userid", "roleid","name"}.issubset(headers):
            print('assignments.csv must have a header row: "userid,roleid,name"')
            sys.exit(1)

        # Normalize header lookup regardless of casing/spacing in the file.
        field_map = {(h or "").strip().lower(): h for h in reader.fieldnames}

        for row in reader:
            user_id = (row.get(field_map["userid"]) or "").strip()
            role_id = (row.get(field_map["roleid"]) or "").strip()
            name = (row.get(field_map["name"]) or "").strip()
            if not user_id or not role_id or not name:
                continue  # skip blank/incomplete rows
            assignments.append((user_id, role_id, name))

    return assignments


async def main() -> None:
    validate_env()
    assignments = load_assignments()

    if not assignments:
        print("assignments.csv has no valid rows in it. Nothing to do.")
        return

    print(f"Loaded {len(assignments)} assignment(s) from assignments.csv.")

    intents = discord.Intents.default()
    intents.members = True  # required to fetch guild members by ID
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}.")

        guild = client.get_guild(int(GUILD_ID))
        if guild is None:
            try:
                guild = await client.fetch_guild(int(GUILD_ID))
            except discord.HTTPException:
                guild = None
        if guild is None:
            print(f"Could not find/access guild {GUILD_ID}. Check GUILD_ID and that the bot is in that server.")
            await client.close()
            return

        me = guild.me or await guild.fetch_member(client.user.id)

        # Cache roles by ID so we don't refetch the same role repeatedly.
        role_cache = {}

        async def get_role(role_id: int):
            if role_id not in role_cache:
                role = guild.get_role(role_id)
                if role is None:
                    roles = await guild.fetch_roles()
                    role = next((r for r in roles if r.id == role_id), None)
                role_cache[role_id] = role
            return role_cache[role_id]

        results = []
        success_count = 0
        fail_count = 0

        for i, (user_id, role_id, name) in enumerate(assignments, start=1):
            outcome = ""
            try:
                role = await get_role(int(role_id))
                if role is None:
                    outcome = f"{name},{role_id} - FAILED (role not found in this server)"
                    fail_count += 1
                elif me.top_role.position <= role.position:
                    outcome = (
                        f"{name},{roleDict[role_id]} - FAILED "
                        f'(bot role must be positioned above "{role.name}")'
                    )
                    fail_count += 1
                else:
                    member = guild.get_member(int(user_id)) or await guild.fetch_member(int(user_id))
                    if role in member.roles:
                        outcome = f"{name},{roleDict[role_id]} - SKIPPED (already had the role)"
                    else:
                        await member.add_roles(role, reason="Bulk role assignment script")
                        outcome = f"{name},{roleDict[role_id]} - SUCCESS"
                        success_count += 1
            except discord.NotFound:
                outcome = f"{name},{roleDict[role_id]} - FAILED (user not found in this server)"
                fail_count += 1
            except discord.Forbidden:
                outcome = f"{name},{roleDict[role_id]} - FAILED (missing permissions)"
                fail_count += 1
            except Exception as err:  # noqa: BLE001 - want to log any failure and keep going
                outcome = f"{name},{roleDict[role_id]} - FAILED ({err})"
                fail_count += 1

            results.append(outcome)
            print(f"[{i}/{len(assignments)}] {outcome}")

            if i < len(assignments):
                await asyncio.sleep(DELAY_SECONDS)

        LOG_FILE.write_text("\n".join(results) + "\n", encoding="utf-8")
        print(f"\nDone. {success_count} succeeded, {fail_count} failed (see results.log for details).")

        await client.close()

    await client.start(BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())