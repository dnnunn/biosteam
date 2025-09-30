#!/usr/bin/env python3
"""Extract a condensed, timestamped transcript from Codex CLI session logs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, Optional

KEEP_EVENT_TYPES = {"user_message", "agent_message"}
KEEP_RESPONSE_TYPE = "message"
CONTENT_TYPES = {"output_text", "input_text"}

TIMESTAMP_RE = re.compile(r"\"timestamp\"\s*:\s*\"([^\"]+)\"")
TYPE_RE = re.compile(r"\"type\"\s*:\s*\"([^\"]+)\"")
ROLE_RE = re.compile(r"\"role\"\s*:\s*\"([^\"]+)\"")
MESSAGE_RE = re.compile(r"\"message\"\s*:\s*\"(.*?)\"", re.DOTALL)
TEXT_RE = re.compile(r"\"text\"\s*:\s*\"(.*?)\"", re.DOTALL)


@dataclass
class TranscriptEntry:
    timestamp: str
    speaker: str
    text: str


def parse_json_line(line: str) -> Optional[dict]:
    try:
        return json.loads(line)
    except Exception:
        return None


def coerce_iso(timestamp: str) -> str:
    if not timestamp:
        return ""
    cleaned = timestamp.strip()
    if not cleaned:
        return ""
    try:
        dt = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError:
        return cleaned
    return dt.isoformat()


def _collect_text(payload_content) -> str:
    if isinstance(payload_content, str):
        return payload_content.strip()
    if isinstance(payload_content, dict):
        if payload_content.get("type") in CONTENT_TYPES:
            return str(payload_content.get("text", "")).strip()
    if isinstance(payload_content, Iterable):
        pieces = []
        for chunk in payload_content:
            if isinstance(chunk, dict) and chunk.get("type") in CONTENT_TYPES:
                text = chunk.get("text")
                if text:
                    pieces.append(str(text).strip())
        return "\n".join(piece for piece in pieces if piece)
    return ""


def extract_from_json(obj: dict) -> Optional[TranscriptEntry]:
    typ = obj.get("type")
    payload = obj.get("payload") or {}
    timestamp = coerce_iso(obj.get("timestamp") or obj.get("time") or "")

    if typ == "event_msg":
        inner = payload.get("type") or payload.get("event")
        if inner in KEEP_EVENT_TYPES:
            speaker = "user" if inner == "user_message" else "assistant"
            text = payload.get("message") or payload.get("text") or ""
            return TranscriptEntry(timestamp=timestamp, speaker=speaker, text=text.strip())

    if typ == "response_item" and payload.get("type") == KEEP_RESPONSE_TYPE:
        role = payload.get("role") or "assistant"
        text = _collect_text(payload.get("content"))
        if text:
            return TranscriptEntry(timestamp=timestamp, speaker=role.strip(), text=text)

    return None


def decode_simple(entry: TranscriptEntry) -> TranscriptEntry:
    """Replace JSON escape sequences for readability."""
    text = (
        entry.text.replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace("\\r", "\r")
        .replace("\\\"", "\"")
        .replace("\\\\", "\\")
    )
    return TranscriptEntry(timestamp=entry.timestamp, speaker=entry.speaker, text=text)


def fallback_extract(line: str) -> Optional[TranscriptEntry]:
    timestamp_match = TIMESTAMP_RE.search(line)
    if not timestamp_match:
        return None
    typ_match = TYPE_RE.search(line)
    if not typ_match:
        return None
    typ = typ_match.group(1)
    if typ not in {"event_msg", "response_item"}:
        return None

    timestamp = coerce_iso(timestamp_match.group(1))
    if typ == "event_msg":
        message_match = MESSAGE_RE.search(line)
        if not message_match:
            return None
        text = message_match.group(1)
        role = "assistant"
        if "user_message" in line:
            role = "user"
        return decode_simple(TranscriptEntry(timestamp=timestamp, speaker=role, text=text))

    if typ == "response_item":
        role_match = ROLE_RE.search(line)
        role = role_match.group(1) if role_match else "assistant"
        text_match = TEXT_RE.search(line)
        if text_match:
            return decode_simple(TranscriptEntry(timestamp=timestamp, speaker=role, text=text_match.group(1)))

    return None


def iter_transcript_entries(lines: Iterable[str]) -> Iterator[TranscriptEntry]:
    for line in lines:
        json_obj = parse_json_line(line)
        entry: Optional[TranscriptEntry] = None
        if isinstance(json_obj, dict):
            entry = extract_from_json(json_obj)
        if entry is None:
            entry = fallback_extract(line)
        if entry is None or not entry.text:
            continue
        yield decode_simple(entry)


def format_entries(entries: Iterable[TranscriptEntry], output_format: str) -> str:
    if output_format == "markdown":
        header = ["| timestamp | speaker | text |", "| --- | --- | --- |"]
        rows = []
        for entry in entries:
            text = entry.text.replace("\n", "<br>").strip()
            rows.append(f"| {entry.timestamp} | {entry.speaker} | {text} |")
        return "\n".join(header + rows)

    # plain text fallback
    lines = []
    for entry in entries:
        lines.append(f"{entry.timestamp} | {entry.speaker}\n{entry.text}\n")
    return "\n".join(lines)


def _gather_rollouts(sessions_dir: Path, path_contains: Optional[str]) -> list[Path]:
    if not sessions_dir.exists():
        return []

    rollouts: list[tuple[float, Path]] = []
    for path in sessions_dir.rglob("rollout-*.jsonl"):
        if path_contains and path_contains not in str(path):
            continue
        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError:
            continue
        rollouts.append((mtime, path))

    rollouts.sort(key=lambda item: item[0], reverse=True)
    return [path for _, path in rollouts]


def find_latest_log(
    sessions_dir: Path,
    path_contains: Optional[str],
    skip: int = 0,
) -> Optional[Path]:
    rollouts = _gather_rollouts(sessions_dir, path_contains)
    if skip < 0:
        skip = 0
    if skip >= len(rollouts):
        return None
    return rollouts[skip]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "log_path",
        nargs="?",
        type=Path,
        help="Path to rollout log file (JSONL or raw)",
    )
    parser.add_argument("--out", type=Path, help="Destination file; defaults to stdout")
    parser.add_argument(
        "--format",
        choices=("markdown", "text"),
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--contains",
        help="Only keep entries whose text contains this substring (case-insensitive)",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Automatically select the most recent rollout log under --sessions-dir",
    )
    parser.add_argument(
        "--sessions-dir",
        type=Path,
        default=Path.home() / ".codex" / "sessions",
        help="Root directory containing Codex rollout logs (default: ~/.codex/sessions)",
    )
    parser.add_argument(
        "--path-contains",
        help="When using --latest, only consider log paths containing this substring",
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=None,
        help="When using --latest, skip this many newest logs (default: 1, to avoid the current session)",
    )
    args = parser.parse_args(argv)

    log_path: Optional[Path]
    if args.latest:
        skip = args.skip if args.skip is not None else 1
        log_path = find_latest_log(args.sessions_dir, args.path_contains, skip=skip)
        if log_path is None:
            parser.error(
                f"No rollout logs found under {args.sessions_dir}"
            )
    else:
        log_path = args.log_path

    if log_path is None:
        parser.error("Please supply a log path or pass --latest")

    if not log_path.exists():
        parser.error(f"Log file not found: {log_path}")

    lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    entries = list(iter_transcript_entries(lines))

    if args.contains:
        needle = args.contains.lower()
        entries = [e for e in entries if needle in e.text.lower()]

    output = format_entries(entries, args.format)

    if args.out:
        args.out.write_text(output + "\n", encoding="utf-8")
    else:
        sys.stdout.write(output)
        if not output.endswith("\n"):
            sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    try:
        raise SystemExit(main())
    except BrokenPipeError:  # allow piping to head
        raise SystemExit(0)
