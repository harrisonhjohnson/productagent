"""
Karma integration for Navi.

Writes seeds as markdown files directly to karma's seeds directory.
Queries knowledge via Claude CLI RAG over those files.
No karma Python import required — pure file I/O + subprocess.
"""
import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Resolved at call time via expanduser (not at import time) so the running
# process always sees the correct home dir regardless of LaunchAgent timing.
def _seeds_dir() -> Path:
    return Path(os.path.expanduser("~/.karma/seeds"))

def _points_file() -> Path:
    return Path(os.path.expanduser("~/.karma/points.json"))


def _slugify(text: str) -> str:
    slug = text.lower()[:60]
    slug = "".join(c if c.isalnum() else "-" for c in slug)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def write_seed(title: str, body: str) -> str:
    """Write a markdown seed to karma's seeds dir. Returns the slug."""
    seeds_dir = _seeds_dir()
    seeds_dir.mkdir(parents=True, exist_ok=True)

    slug = _slugify(title)
    filepath = seeds_dir / f"{slug}.md"

    if filepath.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        slug = f"{slug}-{ts}"
        filepath = seeds_dir / f"{slug}.md"

    now = datetime.now(timezone.utc).isoformat()
    content = f"---\ntitle: {title}\ncreated_at: {now}\ntags: []\n---\n\n{body}"
    filepath.write_text(content, encoding="utf-8")
    logger.info(f"Karma seed written: {filepath.name}")
    return slug


def query(question: str, claude_path: str = None) -> str:
    """RAG query over all karma seeds via Claude CLI."""
    seeds_dir = _seeds_dir()
    if not seeds_dir.exists():
        return "No karma seeds yet."

    seed_files = sorted(seeds_dir.glob("*.md"))
    if not seed_files:
        return "No karma seeds yet."

    parts = []
    for sf in seed_files:
        try:
            text = sf.read_text(encoding="utf-8")
            title = sf.stem
            body = text
            if text.startswith("---"):
                chunks = text.split("---", maxsplit=2)
                if len(chunks) >= 3:
                    body = chunks[2].strip()
                    for line in chunks[1].splitlines():
                        if line.startswith("title:"):
                            title = line.split(":", 1)[1].strip()
                            break
            if body:
                parts.append(f"[{title}]\n{body}")
        except OSError:
            continue

    if not parts:
        return "No readable karma seeds."

    seeds_context = "\n\n".join(parts)
    prompt = (
        f"Personal knowledge seeds:\n\n{seeds_context}\n\n"
        f"Question: {question}\n\n"
        f"Answer concisely using only what's in the seeds. "
        f"If the answer isn't there, say so plainly."
    )

    if not claude_path:
        claude_path = os.path.expanduser("~/.local/bin/claude")

    try:
        result = subprocess.run(
            [claude_path, "-p", prompt, "--output-format", "text"],
            capture_output=True, text=True, timeout=90
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        logger.error(f"Karma query failed: {result.stderr[:200]}")
        return "Query failed — check logs."
    except subprocess.TimeoutExpired:
        return "Query timed out."
    except Exception as e:
        logger.error(f"Karma query error: {e}")
        return f"Query error: {e}"


def get_recent_seeds(n: int = 3) -> list:
    """Return titles of the n most recently written seeds."""
    seeds_dir = _seeds_dir()
    if not seeds_dir.exists():
        return []
    files = sorted(seeds_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    titles = []
    for sf in files[:n]:
        title = sf.stem
        try:
            text = sf.read_text(encoding="utf-8")
            if text.startswith("---"):
                chunks = text.split("---", maxsplit=2)
                for line in chunks[1].splitlines():
                    if line.startswith("title:"):
                        title = line.split(":", 1)[1].strip()
                        break
        except OSError:
            pass
        titles.append(title)
    return titles


def get_status() -> dict:
    """Return seed count and karma points total."""
    seeds_dir = _seeds_dir()
    seed_count = len(list(seeds_dir.glob("*.md"))) if seeds_dir.exists() else 0
    points = 0
    points_file = _points_file()
    if points_file.exists():
        try:
            data = json.loads(points_file.read_text(encoding="utf-8"))
            points = data.get("total", 0)
        except (json.JSONDecodeError, OSError):
            pass
    return {"seeds": seed_count, "points": points}
