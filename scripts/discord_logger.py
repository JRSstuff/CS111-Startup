"""
scripts/discord_logger.py
Automated Git Commit & Push Logger for CS111 Startup Simulation
Posts directly to #📜・git-logs (ID: 1561216093303996507).
"""

import sys
import os
import subprocess
import asyncio
import discord

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def load_env():
    """Load key-value pairs from .env without requiring external dependencies."""
    search_dirs = [
        os.getcwd(),
        os.path.dirname(__file__),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    ]
    for d in search_dirs:
        env_path = os.path.join(d, ".env")
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            except Exception:
                pass
            break


load_env()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
TARGET_GUILD_ID = int(os.getenv("TARGET_GUILD_ID", "1559152569853546580"))
TARGET_CHANNEL_NAME = "📜・git-logs"
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "1561216093303996507"))
REPO_URL = "https://github.com/JRSstuff/CS111-Startup"


def get_git_info():
    """Retrieve the latest commit details from the local repository."""
    info = {
        "hash": "unknown",
        "author": "Teammate",
        "message": "Update codebase",
        "files": [],
        "branch": "main",
    }
    try:
        info["hash"] = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        info["author"] = subprocess.check_output(
            ["git", "log", "-1", "--pretty=format:%an"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        info["message"] = subprocess.check_output(
            ["git", "log", "-1", "--pretty=format:%s"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        info["branch"] = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        raw_files = subprocess.check_output(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip().splitlines()
        info["files"] = [f for f in raw_files if f]
    except Exception:
        pass
    return info


async def send_discord_notification(summary_override=None):
    if not DISCORD_TOKEN:
        print("❌ Error: DISCORD_TOKEN not found in environment or .env file.")
        return

    client = discord.Client(intents=discord.Intents.default())
    try:
        await client.login(DISCORD_TOKEN)
        asyncio.create_task(client.connect())
        for _ in range(25):
            if client.is_ready():
                break
            await asyncio.sleep(0.2)

        guild = client.get_guild(TARGET_GUILD_ID)
        if not guild:
            guild = await client.fetch_guild(TARGET_GUILD_ID)

        channel = client.get_channel(TARGET_CHANNEL_ID)
        if not channel:
            channel = await client.fetch_channel(TARGET_CHANNEL_ID)

        git_info = get_git_info()
        commit_msg = summary_override or git_info["message"]
        commit_hash = git_info["hash"]
        author = git_info["author"]
        branch = git_info["branch"]
        files = git_info["files"]

        commit_url = f"{REPO_URL}/commit/{commit_hash}" if commit_hash != "unknown" else REPO_URL

        embed = discord.Embed(
            title="🚀 New Code Pushed to GitHub!",
            description=f"**[{commit_msg}]({commit_url})**",
            color=0x00E5FF,
        )
        embed.add_field(name="👤 Author", value=author, inline=True)
        embed.add_field(name="🌿 Branch", value=f"`{branch}`", inline=True)
        embed.add_field(name="🔗 Commit", value=f"[`{commit_hash}`]({commit_url})", inline=True)

        if files:
            files_display = "\n".join([f"• `{f}`" for f in files[:8]])
            if len(files) > 8:
                files_display += f"\n*...and {len(files) - 8} more files*"
            embed.add_field(name="📁 Changed Files", value=files_display, inline=False)

        embed.set_footer(text=f"CS111 Startup • Team 4 • Repo: {REPO_URL.split('/')[-1]}")

        await channel.send(
            content=f"🛠️ **Git Update:** `{author}` pushed a new commit to `{branch}`!",
            embed=embed,
        )
        print(f"✓ Discord notification successfully sent to #{channel.name}!")
    except Exception as e:
        print(f"❌ Failed to send Discord notification: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    override = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(send_discord_notification(override))
