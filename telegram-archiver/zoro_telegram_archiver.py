#!/usr/bin/env python3
"""Local Telegram chat/channel exporter for Termux. Exports accessible dialogs to ZIP."""
from __future__ import annotations

import asyncio
import html
import json
import os
import re
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from telethon import TelegramClient
    from telethon.errors import FloodWaitError, SessionPasswordNeededError
    from telethon.tl.types import User, Chat, Channel
except ImportError:
    print("Missing dependency. Run: python -m pip install -r requirements.txt", file=sys.stderr)
    raise SystemExit(2)

APP_NAME = "ZORO TELEGRAM ARCHIVER PRO"
HOME = Path.home()
SHARED_OUT = HOME / "storage" / "shared" / "ZORO_Telegram_Archives"
LOCAL_OUT = HOME / "ZORO_Telegram_Archives"
SESSION_DIR = HOME / ".zoro_telegram_archiver"
MAX_RETRIES = 3


def safe_name(value: str, limit: int = 70) -> str:
    value = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", "_", value or "Telegram chat")
    value = re.sub(r"\s+", " ", value).strip(" ._")
    return (value or "Telegram chat")[:limit]


def prompt_date(label: str) -> datetime | None:
    raw = input(f"{label} (YYYY-MM-DD, leave blank for no limit): ").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        print("Invalid date. Use YYYY-MM-DD.")
        return prompt_date(label)


def choose_output() -> Path:
    out = SHARED_OUT if (HOME / "storage" / "shared").exists() else LOCAL_OUT
    try:
        out.mkdir(parents=True, exist_ok=True)
        test = out / ".write_test"
        test.write_text("ok", encoding="utf-8")
        test.unlink(missing_ok=True)
        return out
    except OSError:
        LOCAL_OUT.mkdir(parents=True, exist_ok=True)
        return LOCAL_OUT


def dialog_kind(entity: Any) -> str:
    if isinstance(entity, User):
        return "private"
    if isinstance(entity, Channel) and getattr(entity, "broadcast", False):
        return "channel"
    if isinstance(entity, (Chat, Channel)):
        return "group"
    return "other"


def message_record(message: Any, media_relative: str | None) -> dict[str, Any]:
    sender = None
    try:
        sender = message.sender_id
    except Exception:
        pass
    date = message.date.isoformat() if getattr(message, "date", None) else None
    return {
        "id": getattr(message, "id", None),
        "date": date,
        "sender_id": sender,
        "text": getattr(message, "message", None) or "",
        "reply_to_msg_id": getattr(getattr(message, "reply_to", None), "reply_to_msg_id", None),
        "forwarded": bool(getattr(message, "fwd_from", None)),
        "media_file": media_relative,
        "views": getattr(message, "views", None),
        "forwards": getattr(message, "forwards", None),
        "edited": getattr(message, "edit_date", None).isoformat() if getattr(message, "edit_date", None) else None,
    }


def write_html(path: Path, title: str, records: list[dict[str, Any]]) -> None:
    parts = [
        "<!doctype html><html lang='en'><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>" + html.escape(title) + "</title>",
        "<style>body{font:16px system-ui;max-width:900px;margin:auto;padding:18px;background:#10151c;color:#e9eef5}"
        "h1{font-size:1.4rem}article{padding:12px;margin:10px 0;background:#1c2632;border-radius:10px}"
        "small{color:#9bb0c4}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;margin:8px 0}"
        "a{color:#82c8ff}</style><body>",
        "<h1>" + html.escape(title) + "</h1>",
        "<p>Messages exported locally by ZORO TELEGRAM ARCHIVER PRO.</p>",
    ]
    for item in records:
        parts.append("<article><small>#{} · {}</small><pre>{}</pre>".format(
            html.escape(str(item.get("id", ""))),
            html.escape(str(item.get("date") or "")),
            html.escape(str(item.get("text") or "")),
        ))
        media = item.get("media_file")
        if media:
            rel = html.escape(media, quote=True)
            parts.append(f"<p>Attachment: <a href='{rel}'>{html.escape(Path(media).name)}</a></p>")
        parts.append("</article>")
    parts.append("</body></html>")
    path.write_text("\n".join(parts), encoding="utf-8")


async def export_dialog(client: TelegramClient, dialog: Any, out_root: Path,
                        download_media: bool, date_from: datetime | None,
                        date_to: datetime | None) -> Path | None:
    entity = dialog.entity
    title = getattr(entity, "title", None) or " ".join(
        x for x in [getattr(entity, "first_name", ""), getattr(entity, "last_name", "")] if x
    ) or getattr(entity, "username", None) or f"chat_{dialog.id}"
    kind = dialog_kind(entity)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work = out_root / f"{safe_name(title)}_{dialog.id}_{stamp}"
    media_dir = work / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    count = 0
    print(f"\n[{kind.upper()}] {title} — exporting…")

    try:
        async for msg in client.iter_messages(entity, reverse=True):
            msg_date = getattr(msg, "date", None)
            if date_from and msg_date and msg_date < date_from:
                continue
            if date_to and msg_date and msg_date > date_to:
                continue
            media_relative = None
            if download_media and getattr(msg, "media", None):
                for attempt in range(MAX_RETRIES):
                    try:
                        downloaded = await client.download_media(msg, file=str(media_dir / f"{msg.id}_"))
                        if downloaded:
                            try:
                                media_relative = str(Path(downloaded).relative_to(work))
                            except ValueError:
                                media_relative = str(Path("media") / Path(downloaded).name)
                        break
                    except FloodWaitError as exc:
                        wait = int(getattr(exc, "seconds", 5)) + 1
                        print(f"Telegram rate limit: waiting {wait}s")
                        await asyncio.sleep(wait)
                    except Exception as exc:
                        errors.append(f"message {msg.id}: media download failed ({type(exc).__name__})")
                        break
            records.append(message_record(msg, media_relative))
            count += 1
            if count % 100 == 0:
                print(f"  {count} messages processed…")
    except FloodWaitError as exc:
        wait = int(getattr(exc, "seconds", 5)) + 1
        print(f"Telegram rate limit: waiting {wait}s before retrying…")
        await asyncio.sleep(wait)
        errors.append(f"History iteration stopped at rate limit after {count} messages; rerun to retry.")
    except Exception as exc:
        errors.append(f"History export stopped: {type(exc).__name__}: {exc}")

    if not records and not errors:
        print("  No messages in the selected date range.")
    manifest = {
        "app": APP_NAME,
        "chat_title": title,
        "chat_id": dialog.id,
        "chat_type": kind,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "message_count": len(records),
        "media_download_enabled": download_media,
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
        "errors": errors,
        "note": "Only data accessible to the logged-in Telegram account is exported."
    }
    (work / "messages.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    (work / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_html(work / "index.html", str(title), records)

    zip_path = out_root / f"{safe_name(title)}_{dialog.id}_{stamp}.zip"
    try:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for file in work.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(work))
        print(f"  Done: {count} messages; ZIP: {zip_path}")
        if errors:
            print(f"  Warning: {len(errors)} issue(s). See manifest.json inside the ZIP.")
        return zip_path
    except OSError as exc:
        print(f"  Could not create ZIP: {exc}")
        return None
    finally:
        # Keep temporary files only when zip creation failed, to aid recovery.
        if zip_path.exists():
            import shutil
            shutil.rmtree(work, ignore_errors=True)


async def main() -> int:
    print(f"\n=== {APP_NAME} ===")
    print("Exports only chats available to the Telegram account you sign in with.")
    print("Your session and archive stay on this device. Never share the .session file.\n")
    try:
        api_id_raw = input("Telegram API ID (from my.telegram.org/apps): ").strip()
        api_id = int(api_id_raw)
        api_hash = input("Telegram API hash: ").strip()
        phone = input("Phone number in international format (e.g. +967…): ").strip()
        if not api_hash or not phone:
            raise ValueError("API hash and phone number are required.")
    except (ValueError, EOFError) as exc:
        print(f"Invalid input: {exc}", file=sys.stderr)
        return 2

    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    session_path = str(SESSION_DIR / "account")
    client = TelegramClient(session_path, api_id, api_hash)
    try:
        await client.start(phone=phone)
    except SessionPasswordNeededError:
        password = input("Telegram two-step verification password: ")
        await client.sign_in(password=password)
    except Exception as exc:
        print(f"Login failed ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1

    try:
        dialogs = []
        async for d in client.iter_dialogs():
            if d.is_user or d.is_group or d.is_channel:
                dialogs.append(d)
        if not dialogs:
            print("No accessible dialogs found.")
            return 0
        print("\nAccessible conversations:")
        for i, d in enumerate(dialogs, 1):
            print(f"{i:>3}. [{dialog_kind(d.entity)}] {d.name} (ID {d.id})")
        print("\nEnter numbers separated by commas, 'all' for every listed dialog, or 'q' to quit.")
        raw = input("Selection: ").strip().lower()
        if raw in {"q", "quit", "exit"}:
            return 0
        if raw == "all":
            selected = dialogs
        else:
            try:
                indices = sorted(set(int(x.strip()) for x in raw.split(",") if x.strip()))
                if not indices or any(i < 1 or i > len(dialogs) for i in indices):
                    raise ValueError
                selected = [dialogs[i - 1] for i in indices]
            except ValueError:
                print("Invalid selection.")
                return 2

        date_from = prompt_date("Start date") if input("Limit by date range? [y/N]: ").strip().lower() == "y" else None
        date_to = prompt_date("End date") if date_from is not None else None
        download_media = input("Download available media and attachments? [Y/n]: ").strip().lower() not in {"n", "no"}
        output = choose_output()
        print(f"\nOutput folder: {output}")
        done = 0
        for dialog in selected:
            result = await export_dialog(client, dialog, output, download_media, date_from, date_to)
            done += bool(result)
        print(f"\nFinished: {done}/{len(selected)} ZIP archive(s) created.")
        print(f"Output folder: {output}")
        return 0 if done else 1
    finally:
        await client.disconnect()


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nCancelled by user.")
        raise SystemExit(130)
