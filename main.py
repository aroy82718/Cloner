# ==============================================================
# Telegram Bot Maker & Hosting Manager (Master Bot Engine)
# Fully Fixed Single File Build
# ==============================================================

import os
import sys
import time
import io
import html
import asyncio
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from typing import Optional

# Optional .env support
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import aiosqlite
import qrcode
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# ==============================================================
# CONFIGURATION
# ==============================================================
MASTER_BOT_TOKEN = "8919692865:AAF_8gEPQd9d4VZ9x8YjlaiappUspO0W8qs"

OWNER_ID = 6914205738

DB_NAME = os.getenv("BOTMAKER_DB", "bot_data.db")
TEMPLATES_DIR = "templates_storage"
LOGS_DIR = "bot_logs"
CLONED_BOTS_DIR = "cloned_bots"

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(CLONED_BOTS_DIR, exist_ok=True)

bot = Bot(
    token=MASTER_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

# Stores: bot_id -> (process_instance, log_file_handle)
ACTIVE_PROCESSES = {}

# ==============================================================
# CUSTOM TELEGRAM PREMIUM EMOJIS (IN MESSAGE TEXT ONLY)
# ==============================================================
E = {
    "BOT": '<tg-emoji emoji-id="5282843764451195532">🖥</tg-emoji>',
    "STAR": '<tg-emoji emoji-id="6267118537752450044">🌟</tg-emoji>',
    "ROCKET": '<tg-emoji emoji-id="6267107057304868214">⚡️</tg-emoji>',
    "BRAIN": '<tg-emoji emoji-id="6262648430825182490">🧠</tg-emoji>',
    "CHECK": '<tg-emoji emoji-id="6267008582294705964">✅</tg-emoji>',
    "CROSS": '<tg-emoji emoji-id="5210952531676504517">❌</tg-emoji>',
    "WARN": '<tg-emoji emoji-id="5447644880824181073">⚠️</tg-emoji>',
    "MONEY": '<tg-emoji emoji-id="6267068789146260253">💰</tg-emoji>',
    "CASH": '<tg-emoji emoji-id="5409048419211682843">💵</tg-emoji>',
    "GIFT": '<tg-emoji emoji-id="6269214795325510848">🎁</tg-emoji>',
    "CROWN": '<tg-emoji emoji-id="6266995104687330978">👑</tg-emoji>',
    "FOLDER": '<tg-emoji emoji-id="5229064374403998351">🛍</tg-emoji>',
    "PACKAGE": '<tg-emoji emoji-id="6269358547880908450">🎁</tg-emoji>',
    "FIRE": '<tg-emoji emoji-id="6264785189394717307">🔥</tg-emoji>',
    "SPARKLE": '<tg-emoji emoji-id="5325547803936572038">✨</tg-emoji>',
    "DIAMOND": '<tg-emoji emoji-id="6264791387032523779">💎</tg-emoji>',
    "STATS": '<tg-emoji emoji-id="5231200819986047254">📊</tg-emoji>',
    "CHANNEL": '<tg-emoji emoji-id="6267129592998270736">📣</tg-emoji>',
    "FLASH": '<tg-emoji emoji-id="6267107057304868214">⚡️</tg-emoji>',
    "TAG": '<tg-emoji emoji-id="5222444124698853913">🔖</tg-emoji>',
    "USER": '<tg-emoji emoji-id="5832281029204775089">👤</tg-emoji>',
    "ONLINE": '<tg-emoji emoji-id="5416081784641168838">🟢</tg-emoji>',
    "OFFLINE": '<tg-emoji emoji-id="5411225014148014586">🔴</tg-emoji>',
    "MAGIC": '<tg-emoji emoji-id="6266864696595323855">💎</tg-emoji>',
    "CARD": '<tg-emoji emoji-id="5402186569006210455">💱</tg-emoji>',
    "GEAR": '<tg-emoji emoji-id="5341715473882955310">⚙️</tg-emoji>',
    "ONE": '<tg-emoji emoji-id="5834610430487564415">1️⃣</tg-emoji>',
    "TWO": '<tg-emoji emoji-id="5834840146813390829">2️⃣</tg-emoji>',
    "PIN": '<tg-emoji emoji-id="5391032818111363540">📍</tg-emoji>',
    "LOCK": '<tg-emoji emoji-id="5296369303661067030">🔒</tg-emoji>',
    "BELL": '<tg-emoji emoji-id="6264510702329797113">🔔</tg-emoji>',
    "LOGS": '<tg-emoji emoji-id="5231012545799666522">🔍</tg-emoji>',
    "HEART": '<tg-emoji emoji-id="6266818250818983044">💘</tg-emoji>',
    "EYES": '<tg-emoji emoji-id="6267186570034419608">👀</tg-emoji>',
    "PARTY": '<tg-emoji emoji-id="6266905902511559661">🥳</tg-emoji>',
    "TROPHY": '<tg-emoji emoji-id="6266973397922616654">🏆</tg-emoji>',
    "PHONE": '<tg-emoji emoji-id="6282996898701775483">📞</tg-emoji>',
    "GLOBE": '<tg-emoji emoji-id="5447410659077661506">🌐</tg-emoji>',
    "TRASH": '<tg-emoji emoji-id="5445267414562389170">🗑</tg-emoji>',
    "ARROW": '<tg-emoji emoji-id="6264699552041801361">➡️</tg-emoji>'
}

# ==============================================================
# BUTTON CREATOR
# ==============================================================
# Custom emoji IDs used as button icons. The IDs are from the user's supplied packs.
BUTTON_EMOJI_IDS = {
    "profile": "6267186570034419608",       # eyes / profile
    "refer": "6264720734820505831",         # handshake
    "redeem": "6267068789146260253",        # money
    "create": "6267107057304868214",        # lightning
    "hosted": "6264791387032523779",        # diamond
    "help": "6266794310671275367",          # chat
    "admin": "6266995104687330978",         # crown
    "back": "6264699552041801361",          # arrow
    "cancel": "6267039884016358504",        # warning
    "broadcast": "6267129592998270736",     # megaphone
    "add": "5397916757333654639",            # plus
    "skip": "6266866272848321043",           # soon/forward
    "save": "6267008582294705964",            # check
    "settings": "5341715473882955310",       # gear
    "channel": "6267129592998270736",       # megaphone
    "upi": "5402186569006210455",            # payment
    "verify": "6267291337171670780",         # check
    "yes": "6267032805910254913",             # thumbs up
    "no": "6264989883241076562",              # prohibited
    "default": "6267118537752450044",        # star
}

def _button_emoji_id(text: str) -> str:
    label = text.lower()
    if "profile" in label: return BUTTON_EMOJI_IDS["profile"]
    if "refer" in label: return BUTTON_EMOJI_IDS["refer"]
    if "redeem" in label or "gift" in label: return BUTTON_EMOJI_IDS["redeem"]
    if "create" in label or "new bot" in label: return BUTTON_EMOJI_IDS["create"]
    if "hosted" in label or "my bots" in label: return BUTTON_EMOJI_IDS["hosted"]
    if "help" in label or "guide" in label: return BUTTON_EMOJI_IDS["help"]
    if "admin" in label: return BUTTON_EMOJI_IDS["admin"]
    if "back" in label or "main menu" in label: return BUTTON_EMOJI_IDS["back"]
    if "cancel" in label: return BUTTON_EMOJI_IDS["cancel"]
    if "broadcast" in label: return BUTTON_EMOJI_IDS["broadcast"]
    if "add" in label: return BUTTON_EMOJI_IDS["add"]
    if "skip" in label: return BUTTON_EMOJI_IDS["skip"]
    if "save" in label or "set " in label: return BUTTON_EMOJI_IDS["save"]
    if "setting" in label or "manage" in label: return BUTTON_EMOJI_IDS["settings"]
    if "channel" in label or "join" in label: return BUTTON_EMOJI_IDS["channel"]
    if "upi" in label or "deposit" in label: return BUTTON_EMOJI_IDS["upi"]
    if "verify" in label or "confirm" in label: return BUTTON_EMOJI_IDS["verify"]
    if "yes" in label or "start" in label: return BUTTON_EMOJI_IDS["yes"]
    if "no" in label or "remove" in label or "delete" in label: return BUTTON_EMOJI_IDS["no"]
    return BUTTON_EMOJI_IDS["default"]

def styled_btn(text: str, callback_data: str = None, style: str = "primary", url: str = None, icon_custom_emoji_id: str = None) -> InlineKeyboardButton:
    # Uses Bot API inline-button styles and custom emoji icons (requires an up-to-date Bot API/aiogram).
    btn_dict = {
        "text": text,
        "style": style if style in {"primary", "success", "danger"} else "primary",
        "icon_custom_emoji_id": str(icon_custom_emoji_id or _button_emoji_id(text)),
    }
    if url:
        btn_dict["url"] = url
    elif callback_data:
        btn_dict["callback_data"] = callback_data
    return InlineKeyboardButton(**btn_dict)

# ==============================================================
# DATABASE SETUP
# ==============================================================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                balance REAL DEFAULT 0.0,
                is_banned INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                added_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS force_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                name TEXT NOT NULL,
                invite_link TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS pending_join_requests (
                user_id INTEGER NOT NULL,
                channel_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, channel_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                file_path TEXT NOT NULL,
                price REAL DEFAULT 0.0,
                banner_file_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS gift_codes (
                code TEXT PRIMARY KEY,
                amount REAL NOT NULL,
                max_uses INTEGER NOT NULL,
                used_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS redeemed_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                amount REAL NOT NULL,
                redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, code)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                bot_username TEXT NOT NULL,
                template_id INTEGER NOT NULL,
                is_running INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE
            )
        """)
        await db.commit()

# --- Helpers ---
async def is_admin(user_id: int) -> bool:
    if int(user_id) == OWNER_ID:
        return True
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,)) as cur:
            return (await cur.fetchone()) is not None

async def is_banned(user_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return bool(row[0]) if row else False

async def get_user_balance(user_id: int) -> float:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return float(row[0]) if row else 0.0

async def update_balance(user_id: int, amount: float):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def get_setting(key: str, default: str = "") -> str:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else default

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        await db.commit()

# ==============================================================
# FORCE JOIN CHANNELS CHECK
# ==============================================================
async def check_force_sub(user_id: int) -> tuple[bool, list]:
    if await is_admin(user_id):
        return True, []

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM force_channels") as cur:
            channels = await cur.fetchall()
        async with db.execute("SELECT channel_id FROM pending_join_requests WHERE user_id = ?", (user_id,)) as cur:
            pending = {str(row[0]) for row in await cur.fetchall()}

    unjoined = []
    for ch in channels:
        channel_id = str(ch["channel_id"]).strip()
        target_chat = int(channel_id) if channel_id.lstrip("-").isdigit() else channel_id
        try:
            member = await bot.get_chat_member(chat_id=target_chat, user_id=user_id)
            if member.status not in ("creator", "administrator", "member") and getattr(member, "is_member", False) is not True:
                # A pending join request counts as submitted, but is NOT approved by this bot.
                if channel_id not in pending:
                    unjoined.append(ch)
        except Exception:
            # getChatMember can fail while the user has a pending request; allow only if the
            # bot has received that request event for this exact channel/user pair.
            if channel_id not in pending:
                unjoined.append(ch)

    return (len(unjoined) == 0), unjoined


@dp.chat_join_request()
async def record_pending_join_request(event: types.ChatJoinRequest):
    """Record requests for force-join verification without approving them."""
    channel_id = str(event.chat.id)
    user_id = int(event.from_user.id)
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT 1 FROM force_channels WHERE channel_id = ?", (channel_id,)) as cur:
            configured = await cur.fetchone()
        if configured:
            await db.execute(
                "INSERT OR REPLACE INTO pending_join_requests (user_id, channel_id) VALUES (?, ?)",
                (user_id, channel_id),
            )
            await db.commit()
    # Intentionally do not call approve_chat_join_request().

def get_force_sub_keyboard(unjoined_channels: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in unjoined_channels:
        buttons.append([styled_btn(f"Join: {ch['name']}", style="primary", url=ch["invite_link"])])
    buttons.append([styled_btn("Verify Membership", "verify_force_sub", style="success")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ==============================================================
# DYNAMIC UPI QR GENERATOR
# ==============================================================
def generate_upi_qr(upi_id: str, amount: float, note: str = "Wallet Deposit") -> io.BytesIO:
    """Generate a PNG UPI QR in memory; works even when Pillow is unavailable."""
    import struct
    import zlib

    upi_id = (upi_id or "").strip()
    amount = float(amount)
    if not upi_id or "@" not in upi_id or amount <= 0:
        raise ValueError("Invalid UPI ID or amount")

    upi_url = "upi://pay?" + urlencode({
        "pa": upi_id,
        "pn": "Bot Hosting",
        "am": f"{amount:.2f}",
        "cu": "INR",
        "tn": note,
    })

    # qrcode creates the matrix; PNG encoding below uses only Python stdlib,
    # so the bot does not depend on Pillow being installed in Wispbyte's runtime.
    qr = qrcode.QRCode(version=None, box_size=1, border=4, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(upi_url)
    qr.make(fit=True)
    matrix = qr.get_matrix()

    scale = 8
    width = len(matrix) * scale
    height = width
    # PNG RGB scanlines: filter byte 0 + one RGB pixel per output pixel.
    raw = bytearray()
    for row in matrix:
        expanded = bytearray()
        for dark in row:
            pixel = b"\x00\x00\x00" if dark else b"\xff\xff\xff"
            expanded.extend(pixel * scale)
        scanline = b"\x00" + bytes(expanded)
        raw.extend(scanline * scale)

    def png_chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xffffffff)

    png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + png_chunk(b"IEND", b"")
    )
    bio = io.BytesIO(png)
    bio.seek(0)
    return bio

# ==============================================================
# SUBPROCESS & LOGGING CONTROLLER
# ==============================================================
async def start_bot_process(bot_id: int, file_path: str, token: str, owner_id: int):
    if bot_id in ACTIVE_PROCESSES:
        await stop_bot_process(bot_id)

    if not file_path or not os.path.exists(file_path):
        print(f"[-] Error: Script file not found: {file_path}")
        return False

    try:
        # Each clone gets its own working directory for SQLite DBs, generated files,
        # caches and other relative-path data, preventing cross-bot data collisions.
        bot_dir = os.path.abspath(os.path.join(CLONED_BOTS_DIR, f"bot_{bot_id}"))
        os.makedirs(bot_dir, exist_ok=True)
        clone_script = os.path.join(bot_dir, "main.py")
        if os.path.abspath(file_path) != os.path.abspath(clone_script):
            shutil.copy2(file_path, clone_script)
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["BOT_TOKEN"] = token
        env["BOT_OWNER_ID"] = str(owner_id)
        env["ADMIN_IDS"] = str(owner_id)
        env["BOT_DATA_DIR"] = bot_dir
        env["BOT_WORK_DIR"] = bot_dir

        log_file_path = os.path.join(LOGS_DIR, f"bot_{bot_id}.log")
        log_file = open(log_file_path, "a", encoding="utf-8")
        log_file.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- BOT PROCESS INITIALIZED ---\n")
        log_file.flush()

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            clone_script,
            token,
            str(owner_id),
            cwd=bot_dir,
            env=env,
            stdout=log_file,
            stderr=log_file
        )
        ACTIVE_PROCESSES[bot_id] = (process, log_file)
        print(f"[+] Child bot #{bot_id} online (PID: {process.pid})")
        return True
    except Exception as e:
        print(f"[-] Error starting bot #{bot_id}: {e}")
        return False

async def stop_bot_process(bot_id: int):
    if bot_id in ACTIVE_PROCESSES:
        proc, log_file = ACTIVE_PROCESSES[bot_id]
        try:
            proc.terminate()
            await asyncio.wait_for(proc.wait(), timeout=3.0)
        except Exception:
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
        
        try:
            if log_file and not log_file.closed:
                log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- BOT PROCESS STOPPED ---\n")
                log_file.flush()
                log_file.close()
        except Exception:
            pass

        del ACTIVE_PROCESSES[bot_id]
        print(f"[*] Child bot #{bot_id} stopped.")

async def restore_all_bots():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT ub.id, ub.token, ub.owner_id, ub.is_running, t.file_path 
            FROM user_bots ub
            JOIN templates t ON ub.template_id = t.id
            WHERE ub.is_running = 1
        """) as cur:
            bots = await cur.fetchall()
            for b in bots:
                if os.path.exists(b["file_path"]):
                    await start_bot_process(b["id"], b["file_path"], b["token"], b["owner_id"])
    print(f"[*] Total active child bots restored: {len(ACTIVE_PROCESSES)}")

# ==============================================================
# UI MENUS & MAIN DASHBOARD
# ==============================================================
def get_main_menu(is_adm: bool = False):
    keyboard = [
        [
            styled_btn("Profile", "btn_profile", style="primary", icon_custom_emoji_id="6267186570034419608"),
            styled_btn("Redeem Code", "btn_redeem_code", style="success", icon_custom_emoji_id="6267068789146260253")
        ],
        [
            styled_btn("Create New Bot", "btn_new_bot", style="success", icon_custom_emoji_id="6267107057304868214"),
            styled_btn("My Hosted Bots", "btn_my_bots", style="primary", icon_custom_emoji_id="6264791387032523779")
        ],
        [
            styled_btn("Help & Guide", "btn_help", style="primary", icon_custom_emoji_id="6266794310671275367")
        ]
    ]
    if is_adm:
        keyboard.append([styled_btn("Admin Panel", "admin_panel", style="danger", icon_custom_emoji_id="6266995104687330978")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def tg_emoji(emoji_id: str, fallback: str = "✨") -> str:
    """Telegram custom emoji entity in HTML text."""
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

MAIN_BANNER_TEXT = (
    f"{tg_emoji('6267186570034419608', '👋')} <i><b>Welcome to the Bot Hosting & Control Center</b></i>\n\n"
    f"{tg_emoji('6267107057304868214', '🚀')} <i><b>Design • Deploy • Manage your Telegram bots with high speed.</b></i>\n\n"
    f"{tg_emoji('6266794310671275367', '💡')} <i>Smart cloud tools, clean interface, and 24/7 continuous uptime.</i>\n\n"
    f"{tg_emoji('6266995104687330978', '📌')} <i>Please choose an option below to continue:</i>"
)

async def send_welcome_dashboard(chat_id: int, old_message: types.Message = None):
    if old_message:
        try:
            await old_message.delete()
        except Exception:
            pass

    is_adm = await is_admin(chat_id)
    welcome_photo = await get_setting("welcome_photo_id")
    kb = get_main_menu(is_adm)

    if welcome_photo:
        try:
            await bot.send_photo(chat_id=chat_id, photo=welcome_photo, caption=MAIN_BANNER_TEXT, reply_markup=kb)
            return
        except Exception:
            pass

    try:
        await bot.send_message(chat_id=chat_id, text=MAIN_BANNER_TEXT, reply_markup=kb)
    except Exception as exc:
        # Fallback: custom emoji entities can fail if an ID is invalid/unavailable.
        # Retry the welcome message as plain HTML-free text so /start still responds.
        import re
        plain_text = re.sub(r"<tg-emoji\s+emoji-id=[\"']\d+[\"']>(.*?)</tg-emoji>", r"\1", MAIN_BANNER_TEXT, flags=re.IGNORECASE | re.DOTALL)
        plain_text = re.sub(r"</?(?:i|b)>", "", plain_text, flags=re.IGNORECASE)
        try:
            await bot.send_message(chat_id=chat_id, text=plain_text, reply_markup=kb, parse_mode=None)
        except Exception:
            # Keep the handler from repeatedly crashing if Telegram rejects the dashboard.
            print(f"Welcome dashboard send failed: {type(exc).__name__}: {exc}")

# ==============================================================
# FSM STATES
# ==============================================================
class UserStates(StatesGroup):
    selecting_category = State()
    waiting_token = State()
    deposit_amount = State()
    deposit_screenshot = State()
    redeem_code = State()

class AdminStates(StatesGroup):
    manage_cloned_user = State()
    add_funds_user = State()
    add_funds_amt = State()
    debit_funds_user = State()
    debit_funds_amt = State()
    ban_user = State()
    unban_user = State()
    add_admin = State()
    del_admin = State()
    add_ch_id = State()
    add_ch_name = State()
    add_ch_link = State()
    set_upi = State()
    set_welcome_photo = State()
    broadcast_msg = State()
    broadcast_buttons = State()
    add_category_name = State()
    tpl_category = State()
    tpl_name = State()
    tpl_desc = State()
    tpl_price = State()
    tpl_banner = State()
    tpl_file = State()
    edit_tpl_price = State()
    gift_name = State()
    gift_amount = State()
    gift_max_uses = State()
    install_module = State()
    manage_cloned_user = State()

# ==============================================================
# GLOBAL CANCEL HANDLER
# ==============================================================
@dp.message(Command("cancel"))
async def cancel_action(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer(f"{E['CROSS']} <i>Action has been cancelled.</i>")
    await send_welcome_dashboard(message.from_user.id)

# ==============================================================
# START & MEMBERSHIP VERIFICATION
# ==============================================================
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id

    if await is_banned(user_id):
        await message.answer(f"{E['CROSS']} <i><b>You have been banned from accessing this platform.</b></i>")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, full_name) VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET username=?, full_name=?
        """, (user_id, message.from_user.username or "N/A", message.from_user.full_name, message.from_user.username or "N/A", message.from_user.full_name))
        await db.commit()

    is_joined, unjoined = await check_force_sub(user_id)
    if not is_joined:
        await message.answer(
            f"{E['WARN']} <i><b>Please join our official channels to unlock access:</b></i>",
            reply_markup=get_force_sub_keyboard(unjoined)
        )
        return

    await send_welcome_dashboard(user_id)

@dp.callback_query(F.data == "verify_force_sub")
async def verify_force_sub(call: types.CallbackQuery):
    is_joined, unjoined = await check_force_sub(call.from_user.id)
    if is_joined:
        await send_welcome_dashboard(call.from_user.id, call.message)
    else:
        await call.answer("You have not joined all the required channels yet.", show_alert=True)

@dp.callback_query(F.data == "main_menu")
async def back_to_main(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await send_welcome_dashboard(call.from_user.id, call.message)

# ==============================================================
# USER GIFT CODE REDEMPTION
# ==============================================================
@dp.callback_query(F.data == "btn_redeem_code")
async def ask_redeem_code(call: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Cancel", "main_menu", style="danger")]])
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        f"{E['GIFT']} <i><b>Redeem Gift or Promotional Code</b></i>\n\n"
        f"<i>Please type and send your gift code below:</i>",
        reply_markup=kb
    )
    await state.set_state(UserStates.redeem_code)

@dp.message(UserStates.redeem_code)
async def process_gift_redemption(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    code_input = message.text.strip().upper()
    user_id = message.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM gift_codes WHERE code = ?", (code_input,)) as cur:
            gift = await cur.fetchone()

        if not gift:
            await message.answer(f"{E['CROSS']} <i><b>Invalid Code!</b> Please enter a valid code or send /cancel.</i>")
            return

        if gift["used_count"] >= gift["max_uses"]:
            await message.answer(f"{E['WARN']} <i><b>This gift code has reached its maximum usage limit!</b></i>")
            await state.clear()
            return

        async with db.execute("SELECT id FROM redeemed_codes WHERE user_id = ? AND code = ?", (user_id, code_input)) as cur:
            already = await cur.fetchone()
            if already:
                await message.answer(f"{E['WARN']} <i><b>You have already claimed this gift code!</b></i>")
                await state.clear()
                return

        amount = gift["amount"]
        await db.execute("INSERT INTO redeemed_codes (user_id, code, amount) VALUES (?, ?, ?)", (user_id, code_input, amount))
        await db.execute("UPDATE gift_codes SET used_count = used_count + 1 WHERE code = ?", (code_input,))
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [styled_btn("View Profile", "btn_profile", style="success")],
        [styled_btn("Main Menu", "main_menu", style="primary")]
    ])
    await message.answer(
        f"{E['SPARKLE']} <i><b>Gift Code Successfully Redeemed!</b></i>\n\n"
        f"{E['MONEY']} <i>An amount of <b>₹{amount:.2f}</b> has been credited to your balance.</i>\n"
        f"{E['TAG']} <i>Code: <code>{code_input}</code></i>",
        reply_markup=kb
    )

# ==============================================================
# CREATE / CLONE BOT FLOW
# ==============================================================
@dp.callback_query(F.data == "btn_new_bot")
async def new_bot_start(call: types.CallbackQuery, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id, name FROM categories") as cur:
            categories = await cur.fetchall()

    if not categories:
        await call.answer("No categories available at the moment.", show_alert=True)
        return

    buttons = []
    for cat in categories:
        buttons.append([styled_btn(f"{cat['name']}", f"user_cat_{cat['id']}", style="primary")])
    buttons.append([styled_btn("Cancel", "main_menu", style="danger")])

    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        f"{E['ROCKET']} <i><b>Select Bot Category</b></i>\n\n"
        f"<i>Please choose a category from the options below:</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(UserStates.selecting_category)

@dp.callback_query(UserStates.selecting_category, F.data.startswith("user_cat_"))
async def show_templates_in_category(call: types.CallbackQuery, state: FSMContext):
    cat_id = int(call.data.replace("user_cat_", ""))

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id, name, price FROM templates WHERE category_id = ?", (cat_id,)) as cur:
            templates = await cur.fetchall()

    if not templates:
        await call.answer("There are no bot templates in this category yet.", show_alert=True)
        return

    buttons = []
    for tpl in templates:
        badge = "FREE" if tpl["price"] == 0 else f"₹{tpl['price']}"
        style_type = "success" if tpl["price"] == 0 else "primary"
        buttons.append([styled_btn(f"{tpl['name']} [{badge}]", f"show_tpl_{tpl['id']}", style=style_type)])
    
    buttons.append([styled_btn("Back to Categories", "btn_new_bot", style="danger")])

    bot_list_header = (
        f"{E['BOT']} <i><b>Available Bot Templates</b></i>\n\n"
        f"{E['SPARKLE']} <i><b>Create • Clone • Deploy your bots easily.</b></i>\n\n"
        f"{E['GEAR']} <i>Select a template below to inspect details:</i>"
    )

    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        bot_list_header,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.callback_query(F.data.startswith("show_tpl_"))
async def show_template_guide_card(call: types.CallbackQuery, state: FSMContext):
    template_id = int(call.data.replace("show_tpl_", ""))

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM templates WHERE id = ?", (template_id,)) as cur:
            tpl = await cur.fetchone()

    if not tpl:
        await call.answer("Template not found.", show_alert=True)
        return

    await state.update_data(selected_template_id=template_id, template_name=tpl["name"], template_price=tpl["price"])

    price_str = "FREE (₹0)" if tpl["price"] == 0 else f"₹{tpl['price']:.2f}"

    guide_caption = (
        f"{E['BOT']} <i><b>Bot Connection Setup</b></i>\n\n"
        f"{E['TAG']} <i><b>Title:</b> {tpl['name']}</i>\n"
        f"{E['MONEY']} <i><b>Price:</b> <code>{price_str}</code></i>\n\n"
        f"{E['MAGIC']} <i><b>Setup Instructions:</b></i>\n"
        f"{E['ONE']} <i>Open @BotFather and create a new bot.</i>\n"
        f"{E['TWO']} <i>Copy the API Token received.</i>\n\n"
        f"{E['PIN']} <i><b>Features:</b></i>\n<i>{tpl['description']}</i>\n\n"
        f"<i>To cancel anytime, send: /cancel</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [styled_btn("Connect This Bot", "proceed_connect_bot", style="success")],
        [styled_btn("Back", f"user_cat_{tpl['category_id']}", style="danger")]
    ])

    try:
        await call.message.delete()
    except Exception:
        pass

    if tpl["banner_file_id"]:
        await call.message.answer_photo(
            photo=tpl["banner_file_id"],
            caption=guide_caption,
            reply_markup=kb
        )
    else:
        await call.message.answer(guide_caption, reply_markup=kb)

@dp.callback_query(F.data == "proceed_connect_bot")
async def ask_token_for_template(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tpl_name = data.get("template_name", "Bot")
    tpl_price = data.get("template_price", 0.0)

    user_id = call.from_user.id
    balance = await get_user_balance(user_id)

    if tpl_price > 0 and balance < tpl_price:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("Deposit Funds", "wallet_deposit", style="success")],
            [styled_btn("Cancel", "main_menu", style="danger")]
        ])
        await call.message.answer(
            f"{E['CROSS']} <i><b>Insufficient Balance!</b></i>\n\n"
            f"<i>Required: <b>₹{tpl_price:.2f}</b></i>\n"
            f"<i>Current Balance: <b>₹{balance:.2f}</b></i>\n\n"
            f"<i>Please top up your wallet balance to continue.</i>",
            reply_markup=kb
        )
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Cancel", "main_menu", style="danger")]])
    await call.message.answer(
        f"{E['BOT']} <i><b>Selected Template:</b> <code>{tpl_name}</code></i>\n\n"
        f"<i>Please paste and send your Telegram Bot <b>API Token</b> below:</i>",
        reply_markup=kb
    )
    await state.set_state(UserStates.waiting_token)

@dp.message(UserStates.waiting_token)
async def process_user_token_and_deploy(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    token = message.text.strip()
    user_id = message.from_user.id

    temp_bot = None
    try:
        temp_bot = Bot(token=token)
        bot_info = await temp_bot.get_me()
    except Exception:
        await message.answer(f"{E['CROSS']} <i><b>Invalid Token!</b> Please provide a valid bot token from @BotFather:</i>")
        return
    finally:
        if temp_bot:
            await temp_bot.session.close()

    data = await state.get_data()
    template_id = data.get("selected_template_id")

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT name, file_path, price FROM templates WHERE id = ?", (template_id,)) as cur:
            tpl = await cur.fetchone()

    if not tpl:
        await message.answer(f"{E['CROSS']} <i>Error: Template configuration not found.</i>")
        await state.clear()
        return

    price = tpl["price"]
    balance = await get_user_balance(user_id)

    if price > 0:
        if balance < price:
            await message.answer(f"{E['CROSS']} <i>Insufficient balance (Price: ₹{price}, Balance: ₹{balance}).</i>")
            await state.clear()
            return
        await update_balance(user_id, -price)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO user_bots (owner_id, token, bot_username, template_id, is_running)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(token) DO UPDATE SET is_running = 1, template_id = ?, owner_id = ?
        """, (user_id, token, bot_info.username, template_id, template_id, user_id))
        await db.commit()
        
        async with db.execute("SELECT id FROM user_bots WHERE token = ?", (token,)) as cur:
            row = await cur.fetchone()
            bot_id = row[0]

    started = await start_bot_process(bot_id, tpl["file_path"], token, user_id)
    await state.clear()

    if started:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("My Hosted Bots", "btn_my_bots", style="success")],
            [styled_btn("Main Menu", "main_menu", style="primary")]
        ])
        await message.answer(
            f"{E['SPARKLE']} <i><b>Congratulations! Your bot is live!</b></i>\n\n"
            f"{E['BOT']} <i><b>Bot:</b> @{bot_info.username}</i>\n"
            f"{E['PACKAGE']} <i><b>Template:</b> <code>{tpl['name']}</code></i>\n"
            f"{E['MONEY']} <i><b>Fee:</b> <code>₹{price:.2f}</code></i>\n"
            f"{E['ONLINE']} <i><b>Status:</b> <code>Online & Running 24/7</code> {E['FLASH']}</i>",
            reply_markup=kb
        )
    else:
        await message.answer(f"{E['WARN']} <i>Bot recorded, but process launch encountered an error. Check server logs.</i>")

# ==============================================================
# MY BOTS MANAGER & LOGS VIEWER
# ==============================================================
@dp.callback_query(F.data == "btn_my_bots")
async def show_my_bots_list(call: types.CallbackQuery):
    user_id = call.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT ub.id, ub.bot_username, ub.is_running, t.name as tpl_name
            FROM user_bots ub
            JOIN templates t ON ub.template_id = t.id
            WHERE ub.owner_id = ?
            ORDER BY ub.id DESC
        """, (user_id,)) as cur:
            bots = await cur.fetchall()

    if not bots:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("Create New Bot", "btn_new_bot", style="success", icon_custom_emoji_id="6267107057304868214")],
            [styled_btn("Main Menu", "main_menu", style="primary")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(
            f"{E['PACKAGE']} <i><b>Hosted Bots Manager</b></i>\n\n"
            f"{E['CROSS']} <i>You do not have any active hosted bots currently.</i>",
            reply_markup=kb
        )
        return

    buttons = []
    for b in bots:
        is_live = (b["id"] in ACTIVE_PROCESSES) and (b["is_running"] == 1)
        btn_style = "success" if is_live else "danger"
        status_tag = "ONLINE" if is_live else "STOPPED"
        btn_text = f"@{b['bot_username']} [{status_tag}]"
        buttons.append([styled_btn(btn_text, f"open_bot_{b['id']}", style=btn_style)])

    buttons.append([styled_btn("Deploy Another Bot", "btn_new_bot", style="primary")])
    buttons.append([styled_btn("Main Menu", "main_menu", style="danger")])

    text = (
        f"{E['BOT']} <i><b>My Hosted Bots</b></i>\n\n"
        f"<i>Select any bot below to manage state, inspect logs, or restart:</i>"
    )

    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("open_bot_"))
async def open_single_bot_controller(call: types.CallbackQuery):
    bot_id = int(call.data.replace("open_bot_", ""))
    user_id = call.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT ub.id, ub.token, ub.bot_username, ub.is_running, ub.created_at, t.name as tpl_name
            FROM user_bots ub
            JOIN templates t ON ub.template_id = t.id
            WHERE ub.id = ? AND ub.owner_id = ?
        """, (bot_id, user_id)) as cur:
            bot_item = await cur.fetchone()

    if not bot_item:
        await call.answer("Bot record not found.", show_alert=True)
        return

    is_live = (bot_id in ACTIVE_PROCESSES) and (bot_item["is_running"] == 1)
    status_text = "ONLINE & RUNNING" if is_live else "STOPPED / OFFLINE"
    dot_icon = E['ONLINE'] if is_live else E['OFFLINE']

    if is_live:
        toggle_btn = styled_btn("Stop Bot", f"botact_stop_{bot_id}", style="danger")
    else:
        toggle_btn = styled_btn("Start Bot", f"botact_start_{bot_id}", style="success")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            styled_btn("Restart Bot", f"botact_restart_{bot_id}", style="primary"),
            toggle_btn
        ],
        [
            styled_btn("Live Logs", f"botact_logs_{bot_id}", style="success"),
            styled_btn("Delete Bot", f"botact_confirm_del_{bot_id}", style="danger")
        ],
        [
            styled_btn("My Bots List", "btn_my_bots", style="primary"),
            styled_btn("Main Menu", "main_menu", style="danger")
        ]
    ])

    token_preview = bot_item['token'][:10] + "..." + bot_item['token'][-4:]

    text = (
        f"{E['BOT']} <i><b>Bot Control Dashboard</b></i>\n\n"
        f"• <i><b>Username:</b> @{bot_item['bot_username']}</i>\n"
        f"• <i><b>Template:</b> <code>{bot_item['tpl_name']}</code></i>\n"
        f"• <i><b>Status:</b> {dot_icon} <code>{status_text}</code></i>\n"
        f"• <i><b>Token:</b> <code>{token_preview}</code></i>\n"
        f"• <i><b>Created:</b> <code>{bot_item['created_at'][:19]}</code></i>"
    )

    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(text, reply_markup=kb)

# --- BOT LOGS VIEWER HANDLER ---
@dp.callback_query(F.data.startswith("botact_logs_"))
async def view_bot_logs_handler(call: types.CallbackQuery):
    bot_id = int(call.data.replace("botact_logs_", ""))
    user_id = call.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT bot_username FROM user_bots WHERE id = ? AND owner_id = ?", (bot_id, user_id)) as cur:
            bot_item = await cur.fetchone()

    if not bot_item:
        await call.answer("Bot not found.", show_alert=True)
        return

    log_file_path = os.path.join(LOGS_DIR, f"bot_{bot_id}.log")
    logs_content = ""

    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                recent_lines = lines[-35:] if len(lines) > 35 else lines
                logs_content = "".join(recent_lines).strip()
        except Exception as e:
            logs_content = f"Error reading logs: {e}"

    if not logs_content:
        logs_content = "No logs recorded yet. Bot output is currently empty."

    safe_logs = html.escape(logs_content[-3500:])

    logs_text = (
        f"{E['LOGS']} <i><b>Live Console Logs: @{bot_item['bot_username']}</b></i>\n\n"
        f"<pre><code class=\"language-log\">{safe_logs}</code></pre>\n\n"
        f"<i>Updated at: <code>{time.strftime('%H:%M:%S')}</code></i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            styled_btn("Refresh Logs", f"botact_logs_{bot_id}", style="primary"),
            styled_btn("Clear Logs", f"botact_clearlogs_{bot_id}", style="danger")
        ],
        [
            styled_btn("Back to Bot Control", f"open_bot_{bot_id}", style="success")
        ]
    ])

    try:
        await call.message.edit_text(logs_text, reply_markup=kb)
    except Exception:
        try:
            await call.message.delete()
            await call.message.answer(logs_text, reply_markup=kb)
        except Exception:
            pass

@dp.callback_query(F.data.startswith("botact_clearlogs_"))
async def clear_bot_logs_handler(call: types.CallbackQuery):
    bot_id = int(call.data.replace("botact_clearlogs_", ""))
    user_id = call.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id FROM user_bots WHERE id = ? AND owner_id = ?", (bot_id, user_id)) as cur:
            if not (await cur.fetchone()):
                await call.answer("Access Denied.", show_alert=True)
                return

    log_file_path = os.path.join(LOGS_DIR, f"bot_{bot_id}.log")
    try:
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- LOGS CLEARED BY USER ---\n")
        await call.answer("Logs cleared successfully!", show_alert=True)
    except Exception as e:
        await call.answer(f"Failed to clear logs: {e}", show_alert=True)

    await view_bot_logs_handler(call)

@dp.callback_query(F.data.startswith("botact_"))
async def execute_bot_actions(call: types.CallbackQuery):
    if "logs_" in call.data or "clearlogs_" in call.data:
        return

    data_parts = call.data.replace("botact_", "").split("_")
    action = data_parts[0]
    bot_id = int(data_parts[-1])
    user_id = call.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT ub.*, t.file_path, t.name as tpl_name FROM user_bots ub
            JOIN templates t ON ub.template_id = t.id
            WHERE ub.id = ? AND ub.owner_id = ?
        """, (bot_id, user_id)) as cur:
            bot_data = await cur.fetchone()

    if not bot_data:
        await call.answer("Bot record not found.", show_alert=True)
        return

    if action == "restart":
        await stop_bot_process(bot_id)
        await start_bot_process(bot_id, bot_data["file_path"], bot_data["token"], user_id)
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE user_bots SET is_running = 1 WHERE id = ?", (bot_id,))
            await db.commit()
        await call.answer("Bot restarted successfully.", show_alert=True)

    elif action == "stop":
        await stop_bot_process(bot_id)
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE user_bots SET is_running = 0 WHERE id = ?", (bot_id,))
            await db.commit()
        await call.answer("Bot stopped.", show_alert=True)

    elif action == "start":
        await start_bot_process(bot_id, bot_data["file_path"], bot_data["token"], user_id)
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE user_bots SET is_running = 1 WHERE id = ?", (bot_id,))
            await db.commit()
        await call.answer("Bot started and online.", show_alert=True)

    elif action == "confirm":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("Yes, Delete Permanently", f"botact_dodelete_{bot_id}", style="danger")],
            [styled_btn("Cancel", f"open_bot_{bot_id}", style="success")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(
            f"{E['WARN']} <i><b>Are you sure you want to delete @{bot_data['bot_username']}?</b></i>\n\n"
            f"<i>This bot instance will be stopped and removed permanently.</i>",
            reply_markup=kb
        )
        return

    elif action == "dodelete":
        await stop_bot_process(bot_id)
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("DELETE FROM user_bots WHERE id = ? AND owner_id = ?", (bot_id, user_id))
            await db.commit()
        
        log_file_path = os.path.join(LOGS_DIR, f"bot_{bot_id}.log")
        if os.path.exists(log_file_path):
            try:
                os.remove(log_file_path)
            except Exception:
                pass

        await call.answer("Bot removed permanently.", show_alert=True)
        await show_my_bots_list(call)
        return

    await open_single_bot_controller(call)

# ==============================================================
# PROFILE & WALLET SYSTEM
# ==============================================================
@dp.callback_query(F.data == "btn_profile")
async def show_profile_wallet(call: types.CallbackQuery):
    user_id = call.from_user.id
    balance = await get_user_balance(user_id)

    profile_text = (
        f"{E['USER']} <i><b>Account:</b> {call.from_user.full_name}</i>\n"
        f"{E['TAG']} <i><b>User ID:</b> <code>{user_id}</code></i>\n\n"
        f"{E['MONEY']} <i><b>Current Balance:</b></i>\n"
        f"<i><b>₹{balance:.2f}</b></i>\n\n"
        f"<i>Use the options below to manage your wallet balance:</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            styled_btn("Deposit Funds", "wallet_deposit", style="success"),
            styled_btn("Redeem Code", "btn_redeem_code", style="primary")
        ],
        [styled_btn("Main Menu", "main_menu", style="danger")]
    ])

    try:
        user_photos = await bot.get_user_profile_photos(user_id, limit=1)
        if user_photos.total_count > 0:
            photo_file_id = user_photos.photos[0][-1].file_id
            await call.message.delete()
            await call.message.answer_photo(photo=photo_file_id, caption=profile_text, reply_markup=kb)
            return
    except Exception:
        pass

    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(profile_text, reply_markup=kb)

# Add Funds amount entry uses INLINE buttons (not Telegram reply-keyboard buttons).
# Numeric buttons intentionally have no emojis, as requested.
def deposit_amount_keyboard():
    rows = [
        [styled_btn("1", "dep_digit_1", style="success"), styled_btn("2", "dep_digit_2", style="success"), styled_btn("3", "dep_digit_3", style="success")],
        [styled_btn("4", "dep_digit_4", style="success"), styled_btn("5", "dep_digit_5", style="success"), styled_btn("6", "dep_digit_6", style="success")],
        [styled_btn("7", "dep_digit_7", style="success"), styled_btn("8", "dep_digit_8", style="success"), styled_btn("9", "dep_digit_9", style="success")],
        [styled_btn("Delete", "dep_delete", style="danger"), styled_btn("0", "dep_digit_0", style="success"), styled_btn("Confirm", "dep_confirm", style="success")],
        [styled_btn("Back", "dep_back", style="primary")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def deposit_amount_text(amount_text: str) -> str:
    shown = amount_text if amount_text else "0"
    return (
        f"{E['CARD']} <b>Enter Amount</b>\n\n"
        f"{E['MONEY']} <b>Method:</b> <i>All UPI QR {E['FIRE']}</i>\n"
        f"{E['CASH']} <b>Amount: ₹{shown}</b>\n\n"
        f"{E['PIN']} <i>Use the buttons below to enter the amount:</i>"
    )

@dp.callback_query(F.data == "wallet_deposit")
async def ask_deposit_amount(call: types.CallbackQuery, state: FSMContext):
    admin_upi = await get_setting("admin_upi")
    if not admin_upi or "@" not in admin_upi:
        await call.answer("UPI ID not configured yet. Please contact admin.", show_alert=True)
        return

    try:
        await call.message.delete()
    except Exception:
        pass

    await state.set_state(UserStates.deposit_amount)
    await state.update_data(deposit_amount_text="")
    prompt = await call.message.answer(
        deposit_amount_text(""),
        reply_markup=deposit_amount_keyboard(),
    )
    await state.update_data(deposit_prompt_id=prompt.message_id, deposit_prompt_chat_id=prompt.chat.id)
    await call.answer()

@dp.callback_query(UserStates.deposit_amount, F.data.startswith("dep_"))
async def process_deposit_amount_button(call: types.CallbackQuery, state: FSMContext):
    action = call.data
    data = await state.get_data()
    amount_text = str(data.get("deposit_amount_text", ""))

    if action == "dep_back":
        await state.clear()
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer("Deposit cancelled.")
        await send_welcome_dashboard(call.from_user.id)
        await call.answer("Cancelled")
        return

    if action == "dep_delete":
        amount_text = amount_text[:-1]
    elif action.startswith("dep_digit_"):
        digit = action.rsplit("_", 1)[-1]
        if not digit.isdigit() or len(digit) != 1:
            await call.answer("Invalid number", show_alert=True)
            return
        if len(amount_text.replace(".", "")) >= 9:
            await call.answer("Amount is too long. Please use a smaller amount.", show_alert=True)
            return
        amount_text += digit
    elif action == "dep_confirm":
        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            await call.answer("Enter an amount greater than ₹0 first.", show_alert=True)
            return

        admin_upi = (await get_setting("admin_upi", "")).strip()
        if not admin_upi or "@" not in admin_upi:
            await call.answer("UPI ID is not configured. Contact admin.", show_alert=True)
            return
        try:
            qr_io = generate_upi_qr(admin_upi, amount, f"Wallet-Dep-{call.from_user.id}")
            qr_file = BufferedInputFile(qr_io.getvalue(), filename="deposit_qr.png")
        except Exception as exc:
            print(f"[Deposit QR] Failed to generate QR: {exc}")
            await call.answer("Could not generate the payment QR. Try again.", show_alert=True)
            return

        async with aiosqlite.connect(DB_NAME) as db:
            cur = await db.execute("INSERT INTO deposits (user_id, amount, status) VALUES (?, ?, 'PENDING')", (call.from_user.id, amount))
            await db.commit()
            dep_id = cur.lastrowid
        await state.update_data(dep_id=dep_id, amount=amount)
        await state.set_state(None)

        caption = (
            f"{E['CARD']} <i><b>Add Funds Via UPI QR</b></i>\n\n"
            f"• <i><b>Amount:</b> <code>₹{amount:.2f}</code></i>\n"
            f"• <i><b>UPI ID:</b> <code>{html.escape(admin_upi)}</code></i>\n\n"
            f"{E['PIN']} <i><b>Instructions:</b></i>\n"
            f"<i>1. Scan the QR code with any UPI app to pay.</i>\n"
            f"<i>2. After paying, click 'Send Screenshot' to send proof.</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("Send Screenshot", "deposit_send_ss", style="success")],
            [styled_btn("Cancel", "main_menu", style="danger")],
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        try:
            await call.message.answer_photo(photo=qr_file, caption=caption, reply_markup=kb)
        except Exception as exc:
            print(f"[Deposit QR] Telegram send_photo failed: {type(exc).__name__}: {exc}")
            await call.answer("QR bana, lekin Telegram par send nahi hua. Console logs check karein.", show_alert=True)
            return
        await call.answer("QR generated")
        return
    else:
        await call.answer()
        return

    await state.update_data(deposit_amount_text=amount_text)
    await call.message.edit_text(
        deposit_amount_text(amount_text),
        reply_markup=deposit_amount_keyboard(),
    )
    await call.answer()

@dp.callback_query(F.data == "deposit_send_ss")
async def prompt_screenshot(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(f"{E['PIN']} <i><b>Please upload your payment screenshot (Photo) now:</b></i>")
    await state.set_state(UserStates.deposit_screenshot)

@dp.message(UserStates.deposit_screenshot, F.photo)
async def handle_deposit_screenshot(message: types.Message, state: FSMContext):
    data = await state.get_data()
    dep_id = data.get("dep_id")
    amount = data.get("amount")

    if not dep_id:
        await message.answer(f"{E['CROSS']} <i>Session expired. Please restart deposit.</i>")
        await state.clear()
        return

    photo_id = message.photo[-1].file_id

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            styled_btn("Approve Funds", f"adm_dep_app_{dep_id}", style="success"),
            styled_btn("Reject", f"adm_dep_rej_{dep_id}", style="danger")
        ]
    ])

    admin_caption = (
        f"{E['FLASH']} <i><b>New Deposit Request</b></i>\n\n"
        f"• <i><b>ID:</b> <code>#{dep_id}</code></i>\n"
        f"• <i><b>User:</b> {message.from_user.full_name} (<code>{message.from_user.id}</code>)</i>\n"
        f"• <i><b>Amount:</b> <code>₹{amount:.2f}</code></i>"
    )

    try:
        await bot.send_photo(chat_id=OWNER_ID, photo=photo_id, caption=admin_caption, reply_markup=admin_kb)
    except Exception as e:
        print(f"[Error] Failed to forward payment proof: {e}")

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Main Menu", "main_menu", style="primary")]])
    await message.answer(
        f"{E['CHECK']} <i><b>Screenshot received!</b> Administrators will verify and credit your wallet.</i>",
        reply_markup=kb
    )

@dp.callback_query(F.data.startswith("adm_dep_"))
async def process_deposit_decision(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        return

    parts = call.data.replace("adm_dep_", "").split("_")
    action, dep_id = parts[0], int(parts[1])

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM deposits WHERE id = ?", (dep_id,)) as cur:
            deposit = await cur.fetchone()

    if not deposit or deposit["status"] != "PENDING":
        await call.answer("Deposit already processed.", show_alert=True)
        return

    if action == "app":
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE deposits SET status = 'APPROVED' WHERE id = ?", (dep_id,))
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (deposit["amount"], deposit["user_id"]))
            await db.commit()

        await call.message.edit_caption(
            caption=f"{call.message.caption}\n\n{E['ONLINE']} <i><b>Status: Approved (+₹{deposit['amount']} Credited)</b></i>",
            reply_markup=None
        )

        try:
            await bot.send_message(
                chat_id=deposit["user_id"],
                text=f"{E['SPARKLE']} <i><b>Deposit Approved!</b> <code>₹{deposit['amount']:.2f}</code> has been credited to your balance.</i>"
            )
        except Exception:
            pass

        await call.answer("Deposit approved.", show_alert=True)

    elif action == "rej":
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE deposits SET status = 'REJECTED' WHERE id = ?", (dep_id,))
            await db.commit()

        await call.message.edit_caption(
            caption=f"{call.message.caption}\n\n{E['OFFLINE']} <i><b>Status: Rejected</b></i>",
            reply_markup=None
        )

        try:
            await bot.send_message(
                chat_id=deposit["user_id"],
                text=f"{E['CROSS']} <i><b>Deposit Rejected!</b> Verification was unsuccessful. Please check proof or contact admin.</i>"
            )
        except Exception:
            pass

        await call.answer("Deposit rejected.", show_alert=True)

@dp.callback_query(F.data == "btn_help")
async def show_help(call: types.CallbackQuery):
    text = (
        f"{E['WARN']} <i><b>Help & Documentation Guide</b></i>\n\n"
        f"<i>1. Open @BotFather to create a bot and get an API Token.</i>\n"
        f"<i>2. Use 'Create New Bot' to select a template and connect.</i>\n"
        f"<i>3. Use 'My Hosted Bots' to Start, Stop, View Logs, Restart, or Delete bots.</i>\n"
        f"<i>4. Top up balance using 'Deposit Funds' or redeem promo codes.</i>\n\n"
        f"<i>Send /cancel at any point to abort inputs.</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back", "main_menu", style="danger")]])
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(text, reply_markup=kb)

# ==============================================================
# MASTER ADMIN CONTROL PANEL
# ==============================================================
@dp.callback_query(F.data == "admin_panel")
async def admin_dashboard(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        await call.answer("Access Denied.", show_alert=True)
        return

    current_upi = await get_setting("admin_upi", "Not Set")
    has_welcome_photo = "Custom Banner Set" if (await get_setting("welcome_photo_id")) else "Default Banner"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            styled_btn("Statistics", "adm_stats", style="primary"),
            styled_btn("Gift Codes", "adm_manage_gifts", style="success")
        ],
        [
            styled_btn("Set Banner Photo", "adm_set_welcome_photo", style="primary"),
            styled_btn("Configure UPI", "adm_set_upi", style="success")
        ],
        [
            styled_btn("Manage Categories", "adm_manage_cats", style="primary"),
            styled_btn("Manage Templates", "adm_manage_tpl_menu", style="primary")
        ],
        [
            styled_btn("Upload Template", "adm_upload_tpl", style="success"),
            styled_btn("Install Pip Module", "adm_install_module", style="primary")
        ],
        [
            styled_btn("Credit Balance", "adm_add_funds", style="success"),
            styled_btn("Debit Balance", "adm_debit_funds", style="danger")
        ],
        [
            styled_btn("Ban User", "adm_ban_user", style="danger"),
            styled_btn("Unban User", "adm_unban_user", style="success")
        ],
        [
            styled_btn("Manage Admins", "adm_manage_admins", style="primary"),
            styled_btn("Force Channels", "adm_force_channels", style="primary")
        ],
        [
            styled_btn("Broadcast Message", "adm_broadcast", style="primary"),
            styled_btn("Manage Cloned Bots", "adm_manage_cloned_bots", style="success", icon_custom_emoji_id="6264791387032523779")
        ],
        [styled_btn("All Cloned Bots", "adm_all_cloned_bots", style="primary", icon_custom_emoji_id="6267107057304868214")],
        [
            styled_btn("Backup Templates", "adm_backup_templates", style="success", icon_custom_emoji_id="6267068789146260253"),
            styled_btn("Backup All Cloned Data", "adm_backup_cloned_data", style="success", icon_custom_emoji_id="6267186570034419608")
        ],
        [styled_btn("Main Menu", "main_menu", style="danger")]
    ])

    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        f"{E['CROWN']} <i><b>Master Admin Control Panel</b></i>\n\n"
        f"• <i><b>Admin:</b> {call.from_user.full_name}</i>\n"
        f"• <i><b>UPI ID:</b> <code>{current_upi}</code></i>\n"
        f"• <i><b>Banner Photo:</b> <code>{has_welcome_photo}</code></i>\n\n"
        f"<i>Select an option below to manage platform settings:</i>",
        reply_markup=kb
    )

# ==============================================================
# ADMIN: BACKUPS (ZIP ARCHIVES SENT PRIVATELY TO ADMIN)
# ==============================================================
def _zip_existing_paths(paths):
    """Create an in-memory ZIP while preserving relative folder names."""
    buf = io.BytesIO()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in paths:
            src = Path(source)
            if not src.exists():
                continue
            if src.is_file():
                archive.write(src, arcname=src.name)
                continue
            for file_path in src.rglob("*"):
                if file_path.is_file():
                    try:
                        arcname = file_path.as_posix()
                        archive.write(file_path, arcname=arcname)
                    except (OSError, PermissionError):
                        continue
    buf.seek(0)
    return buf.getvalue(), stamp


async def _send_admin_backup(call: types.CallbackQuery, paths, title: str):
    if not await is_admin(call.from_user.id):
        await call.answer("Access denied", show_alert=True)
        return
    await call.answer("Backup is being prepared…")
    data, stamp = await asyncio.to_thread(_zip_existing_paths, paths)
    if not data:
        await call.message.answer("Backup could not be created: no files found.")
        return
    filename = f"{title}_{stamp}.zip"
    caption = (
        f"{E['BOT']} <b>{html.escape(title.replace('_', ' '))}</b>\n"
        f"<i>Created: {stamp} UTC</i>\n"
        "<i>Keep this archive private; it may contain bot configuration, database records, or tokens.</i>"
    )
    await call.message.answer_document(BufferedInputFile(data, filename=filename), caption=caption)


@dp.callback_query(F.data == "adm_backup_templates")
async def adm_backup_templates(call: types.CallbackQuery):
    # Template source files and template metadata live in these paths.
    await _send_admin_backup(call, [TEMPLATES_DIR, DB_NAME], "templates_backup")


@dp.callback_query(F.data == "adm_backup_cloned_data")
async def adm_backup_cloned_data(call: types.CallbackQuery):
    # Includes bot working directories, logs, and database metadata required to map
    # cloned bot records to their template and owner. Database may contain credentials.
    await _send_admin_backup(call, [CLONED_BOTS_DIR, LOGS_DIR, DB_NAME], "all_cloned_bots_backup")


# ==============================================================
# ADMIN: ALL CLONED BOTS + PER-BOT CONTROLS
# ==============================================================
@dp.callback_query(F.data == "adm_all_cloned_bots")
async def adm_all_cloned_bots(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        await call.answer("Not authorized", show_alert=True)
        return
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT ub.id, ub.owner_id, ub.bot_username, ub.is_running, ub.created_at,
                   t.name AS template_name, t.file_path
            FROM user_bots ub LEFT JOIN templates t ON t.id = ub.template_id
            ORDER BY ub.id DESC
        """) as cur:
            rows = await cur.fetchall()
    if not rows:
        kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back to Admin Panel", "admin_panel", style="primary")]])
        await call.message.answer(f"{tg_emoji('6267068789146260253', 'ℹ️')} <b>No cloned bots have been created yet.</b>", reply_markup=kb)
        await call.answer()
        return
    buttons = []
    for row in rows:
        status = "RUNNING" if row["id"] in ACTIVE_PROCESSES else ("PAUSED" if row["is_running"] else "STOPPED")
        username = ("@" + row["bot_username"].lstrip("@")) if row["bot_username"] else "Unknown bot"
        buttons.append([styled_btn(f"{status} #{row['id']} {username} · Owner {row['owner_id']}", f"admcb_open_{row['id']}", style="primary")])
    buttons.append([styled_btn("Manage by User ID", "adm_manage_cloned_bots", style="success")])
    buttons.append([styled_btn("Back to Admin Panel", "admin_panel", style="danger")])
    await call.message.answer(
        f"{tg_emoji('6267107057304868214', '🤖')} <b>All Cloned Bots</b>\n\n"
        f"{tg_emoji('6266794310671275367', '📊')} Total bots: <b>{len(rows)}</b>\n"
        "Select a bot to start, stop, restart, view logs, or delete it.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await call.answer()

@dp.callback_query(F.data == "adm_manage_cloned_bots")
async def adm_manage_cloned_bots(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        await call.answer("Not authorized", show_alert=True)
        return
    await state.set_state(AdminStates.manage_cloned_user)
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("View All Cloned Bots", "adm_all_cloned_bots", style="success")], [styled_btn("Cancel", "admin_panel", style="danger")]])
    await call.message.answer(
        f"{tg_emoji('6267186570034419608', '👤')} <b>Manage User's Cloned Bots</b>\n\n"
        "Send the Telegram numeric user ID. I'll show every bot owned by that user.", reply_markup=kb
    )
    await call.answer()

@dp.message(AdminStates.manage_cloned_user)
async def adm_manage_cloned_user_result(message: types.Message, state: FSMContext):
    if not (await is_admin(message.from_user.id)):
        await state.clear()
        return
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Please send a numeric Telegram user ID, for example: <code>123456789</code>.")
        return
    owner_id = int(raw)
    await state.clear()
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT ub.id, ub.owner_id, ub.bot_username, ub.is_running, t.name AS template_name
            FROM user_bots ub LEFT JOIN templates t ON t.id = ub.template_id
            WHERE ub.owner_id = ? ORDER BY ub.id DESC
        """, (owner_id,)) as cur:
            rows = await cur.fetchall()
    if not rows:
        await message.answer(f"No cloned bots found for user <code>{owner_id}</code>.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[styled_btn("All Cloned Bots", "adm_all_cloned_bots", style="primary")], [styled_btn("Admin Panel", "admin_panel", style="danger")]]))
        return
    buttons = []
    for row in rows:
        username = ("@" + row["bot_username"].lstrip("@")) if row["bot_username"] else "Unknown bot"
        status = "RUNNING" if row["id"] in ACTIVE_PROCESSES else ("PAUSED" if row["is_running"] else "STOPPED")
        buttons.append([styled_btn(f"{status} #{row['id']} {username}", f"admcb_open_{row['id']}", style="primary")])
    buttons.extend([[styled_btn("All Cloned Bots", "adm_all_cloned_bots", style="success")], [styled_btn("Admin Panel", "admin_panel", style="danger")]])
    await message.answer(f"{tg_emoji('6267186570034419608', '👤')} <b>User:</b> <code>{owner_id}</code>\n<b>Cloned bots:</b> {len(rows)}\nSelect a bot to manage:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("admcb_open_"))
async def admcb_open(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        await call.answer("Not authorized", show_alert=True)
        return
    try:
        bot_id = int(call.data.rsplit("_", 1)[1])
    except ValueError:
        await call.answer("Invalid bot ID", show_alert=True)
        return
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT ub.*, t.file_path, t.name AS template_name FROM user_bots ub LEFT JOIN templates t ON t.id=ub.template_id WHERE ub.id=?", (bot_id,)) as cur:
            row = await cur.fetchone()
    if not row:
        await call.answer("Bot not found", show_alert=True)
        return
    running = bot_id in ACTIVE_PROCESSES
    status = "RUNNING" if running else ("PAUSED" if row["is_running"] else "STOPPED")
    username = "@" + row["bot_username"].lstrip("@") if row["bot_username"] else "Unknown"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [styled_btn("Start", f"admcb_start_{bot_id}", style="success"), styled_btn("Stop", f"admcb_stop_{bot_id}", style="danger")],
        [styled_btn("Restart", f"admcb_restart_{bot_id}", style="primary"), styled_btn("View Logs", f"admcb_logs_{bot_id}", style="primary")],
        [styled_btn("Delete Bot", f"admcb_delete_{bot_id}", style="danger")],
        [styled_btn("All Cloned Bots", "adm_all_cloned_bots", style="success"), styled_btn("Admin Panel", "admin_panel", style="primary")]
    ])
    await call.message.answer(f"{tg_emoji('6267107057304868214', '🤖')} <b>Cloned Bot #{bot_id}</b>\n\n<b>Bot:</b> {html.escape(username)}\n<b>Owner ID:</b> <code>{row['owner_id']}</code>\n<b>Template:</b> {html.escape(str(row['template_name'] or 'Missing'))}\n<b>Status:</b> <b>{status}</b>\n\nChoose an action:", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data.startswith("admcb_"))
async def admcb_action(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        await call.answer("Not authorized", show_alert=True)
        return
    parts = call.data.split("_")
    if len(parts) < 3:
        await call.answer("Invalid action", show_alert=True)
        return
    action = parts[1]
    try:
        bot_id = int(parts[2])
    except ValueError:
        await call.answer("Invalid bot ID", show_alert=True)
        return
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT ub.*, t.file_path FROM user_bots ub LEFT JOIN templates t ON t.id=ub.template_id WHERE ub.id=?", (bot_id,)) as cur:
            row = await cur.fetchone()
    if not row:
        await call.answer("Bot not found", show_alert=True)
        return
    if action == "start" or action == "restart":
        ok = await start_bot_process(bot_id, row["file_path"], row["token"], row["owner_id"])
        if ok:
            async with aiosqlite.connect(DB_NAME) as db:
                await db.execute("UPDATE user_bots SET is_running=1 WHERE id=?", (bot_id,)); await db.commit()
            result = "Bot started." if action == "start" else "Bot restarted."
        else:
            result = "Could not start bot. Check that its template file still exists."
    elif action == "stop":
        await stop_bot_process(bot_id)
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE user_bots SET is_running=0 WHERE id=?", (bot_id,)); await db.commit()
        result = "Bot stopped."
    elif action == "logs":
        log_path = os.path.join(LOGS_DIR, f"bot_{bot_id}.log")
        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                logs = f.read()[-3000:] or "Log file is empty."
        except FileNotFoundError:
            logs = "No log file exists yet."
        await call.message.answer(f"<b>Logs for bot #{bot_id}</b>\n<pre>{html.escape(logs)}</pre>", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back to Bot", f"admcb_open_{bot_id}", style="primary")]]))
        await call.answer()
        return
    elif action == "delete":
        kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Confirm Delete", f"admcb_dodelete_{bot_id}", style="danger"), styled_btn("Cancel", f"admcb_open_{bot_id}", style="primary")]])
        await call.message.answer(f"Delete cloned bot <b>#{bot_id}</b> ({html.escape(str(row['bot_username'] or 'Unknown'))})? This removes its database entry and log file.", reply_markup=kb)
        await call.answer()
        return
    elif action == "dodelete":
        await stop_bot_process(bot_id)
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("DELETE FROM user_bots WHERE id=?", (bot_id,)); await db.commit()
        try:
            os.remove(os.path.join(LOGS_DIR, f"bot_{bot_id}.log"))
        except FileNotFoundError:
            pass
        result = f"Cloned bot #{bot_id} deleted."
    else:
        await call.answer("Unknown action", show_alert=True)
        return
    await call.message.answer(f"{tg_emoji('6267068789146260253', '✅')} {html.escape(result)}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[styled_btn("All Cloned Bots", "adm_all_cloned_bots", style="success"), styled_btn("Admin Panel", "admin_panel", style="primary")]]))
    await call.answer()

# ==============================================================
# ADMIN PIP MODULE INSTALLER
# ==============================================================
@dp.callback_query(F.data == "adm_install_module")
async def adm_install_module_prompt(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Cancel", "admin_panel", style="danger")]])
    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        f"{E['PACKAGE']} <i><b>Install Python Module / PIP Package</b></i>\n\n"
        f"<i>Please send the module or library name you want to install:</i>\n"
        f"<i>Examples: <code>motor</code>, <code>pymongo</code>, <code>requests</code>, <code>aiohttp</code></i>",
        reply_markup=kb
    )
    await state.set_state(AdminStates.install_module)

@dp.message(AdminStates.install_module)
async def adm_execute_module_install(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    pkg_name = message.text.strip()
    status_msg = await message.answer(f"<i>Installing package <code>{html.escape(pkg_name)}</code>... Please wait.</i>")
    await state.clear()

    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "pip", "install", pkg_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        output = (stdout.decode('utf-8', errors='ignore') + "\n" + stderr.decode('utf-8', errors='ignore')).strip()

        if proc.returncode == 0:
            res_title = f"{E['CHECK']} <i><b>Module Installed Successfully!</b></i>"
        else:
            res_title = f"{E['CROSS']} <i><b>Module Installation Failed!</b></i>"

        safe_output = html.escape(output[-3500:]) if output else "No output generated."

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("Install Another Module", "adm_install_module", style="success")],
            [styled_btn("Back to Admin Panel", "admin_panel", style="primary")]
        ])

        await status_msg.edit_text(
            f"{res_title}\n\n"
            f"<b>Package:</b> <code>{html.escape(pkg_name)}</code>\n\n"
            f"<pre><code class=\"language-bash\">{safe_output}</code></pre>",
            reply_markup=kb
        )
    except Exception as e:
        kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back to Admin Panel", "admin_panel", style="primary")]])
        await status_msg.edit_text(
            f"{E['CROSS']} <i>Error executing pip install:</i> <code>{html.escape(str(e))}</code>",
            reply_markup=kb
        )

# --- Set Welcome Banner Photo ---
@dp.callback_query(F.data == "adm_set_welcome_photo")
async def adm_set_welcome_photo_menu(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [styled_btn("Remove Custom Banner", "adm_remove_welcome_photo", style="danger")],
        [styled_btn("Back to Admin Panel", "admin_panel", style="primary")]
    ])

    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        f"{E['SPARKLE']} <i><b>Set Welcome Banner Photo</b></i>\n\n"
        f"<i>Please upload the photo to be displayed on the main welcome dashboard:</i>",
        reply_markup=kb
    )
    await state.set_state(AdminStates.set_welcome_photo)

@dp.message(AdminStates.set_welcome_photo, F.photo)
async def adm_save_welcome_photo(message: types.Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    await set_setting("welcome_photo_id", photo_file_id)
    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]])
    await message.answer(f"{E['CHECK']} <i><b>Welcome banner photo updated successfully!</b></i>", reply_markup=kb)

@dp.callback_query(F.data == "adm_remove_welcome_photo")
async def adm_remove_welcome_photo(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await set_setting("welcome_photo_id", "")
    await call.answer("Banner removed.", show_alert=True)
    await admin_dashboard(call)

# ==============================================================
# TEMPLATES MANAGEMENT
# ==============================================================
@dp.callback_query(F.data == "adm_manage_tpl_menu")
async def adm_manage_templates_list(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        return

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT t.id, t.name, t.price, c.name as cat_name 
            FROM templates t
            JOIN categories c ON t.category_id = c.id
        """) as cur:
            templates = await cur.fetchall()

    if not templates:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("Upload Template", "adm_upload_tpl", style="success")],
            [styled_btn("Admin Panel", "admin_panel", style="primary")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(f"{E['CROSS']} <i>No bot templates found.</i>", reply_markup=kb)
        return

    buttons = []
    for tpl in templates:
        p_badge = "FREE" if tpl['price'] == 0 else f"₹{tpl['price']}"
        buttons.append([styled_btn(f"{tpl['name']} [{tpl['cat_name']}] - {p_badge}", f"adm_tpl_detail_{tpl['id']}", style="primary")])
    buttons.append([styled_btn("Upload New Template", "adm_upload_tpl", style="success")])
    buttons.append([styled_btn("Admin Panel", "admin_panel", style="danger")])

    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        f"{E['PACKAGE']} <i><b>Manage Templates Dashboard</b></i>\n\n"
        f"<i>Select any template to inspect, edit pricing, or delete:</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.callback_query(F.data.startswith("adm_tpl_detail_"))
async def adm_template_single_view(call: types.CallbackQuery):
    tpl_id = int(call.data.replace("adm_tpl_detail_", ""))

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT t.*, c.name as cat_name 
            FROM templates t
            JOIN categories c ON t.category_id = c.id
            WHERE t.id = ?
        """, (tpl_id,)) as cur:
            tpl = await cur.fetchone()

    if not tpl:
        await call.answer("Template not found.", show_alert=True)
        return

    price_str = "FREE (₹0)" if tpl["price"] == 0 else f"₹{tpl['price']:.2f}"

    text = (
        f"{E['PACKAGE']} <i><b>Template Details & Configuration</b></i>\n\n"
        f"• <i><b>Name:</b> <code>{tpl['name']}</code></i>\n"
        f"• <i><b>Category:</b> <code>{tpl['cat_name']}</code></i>\n"
        f"• <i><b>Current Price:</b> <code>{price_str}</code></i>\n"
        f"• <i><b>Script Path:</b> <code>{tpl['file_path']}</code></i>\n\n"
        f"{E['TAG']} <i><b>Features:</b></i>\n<i>{tpl['description']}</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [styled_btn("Edit Price", f"adm_tpled_prc_{tpl_id}", style="primary")],
        [styled_btn("Delete Template", f"adm_tpled_del_{tpl_id}", style="danger")],
        [styled_btn("Back to Templates", "adm_manage_tpl_menu", style="success")]
    ])

    try:
        await call.message.delete()
    except Exception:
        pass

    if tpl["banner_file_id"]:
        await call.message.answer_photo(photo=tpl["banner_file_id"], caption=text, reply_markup=kb)
    else:
        await call.message.answer(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("adm_tpled_prc_"))
async def adm_edit_template_price_prompt(call: types.CallbackQuery, state: FSMContext):
    tpl_id = int(call.data.replace("adm_tpled_prc_", ""))
    await state.update_data(edit_tpl_id=tpl_id)
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['CASH']} <i><b>Enter new price (₹, 0 for free):</b></i>")
    await state.set_state(AdminStates.edit_tpl_price)

@dp.message(AdminStates.edit_tpl_price)
async def adm_save_template_price(message: types.Message, state: FSMContext):
    try:
        new_price = float(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid numeric value:</i>")
        return

    data = await state.get_data()
    tpl_id = data["edit_tpl_id"]

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE templates SET price = ? WHERE id = ?", (new_price, tpl_id))
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back to Templates", "adm_manage_tpl_menu", style="primary")]])
    await message.answer(f"{E['CHECK']} <i><b>Template price updated to ₹{new_price:.2f}!</b></i>", reply_markup=kb)

@dp.callback_query(F.data.startswith("adm_tpled_del_"))
async def adm_delete_template_confirm(call: types.CallbackQuery):
    tpl_id = int(call.data.replace("adm_tpled_del_", ""))

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT file_path FROM templates WHERE id = ?", (tpl_id,)) as cur:
            row = await cur.fetchone()
            if row and os.path.exists(row[0]):
                try:
                    os.remove(row[0])
                except Exception:
                    pass
        await db.execute("DELETE FROM templates WHERE id = ?", (tpl_id,))
        await db.commit()

    await call.answer("Template deleted permanently.", show_alert=True)
    await adm_manage_templates_list(call)

# ==============================================================
# GIFT CODES CONTROLLER
# ==============================================================
@dp.callback_query(F.data == "adm_manage_gifts")
async def adm_gift_codes_menu(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        return

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM gift_codes ORDER BY created_at DESC") as cur:
            gifts = await cur.fetchall()

    buttons = []
    for g in gifts:
        btn_txt = f"Delete: {g['code']} - ₹{g['amount']} ({g['used_count']}/{g['max_uses']})"
        buttons.append([styled_btn(btn_txt, f"adm_delgift_{g['code']}", style="danger")])

    buttons.append([styled_btn("Generate Gift Code", "adm_add_gift_start", style="success")])
    buttons.append([styled_btn("Admin Panel", "admin_panel", style="primary")])

    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        f"{E['GIFT']} <i><b>Gift Codes Management</b></i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.callback_query(F.data == "adm_add_gift_start")
async def adm_create_gift_step1(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['TAG']} <i><b>Step 1:</b> Enter the Gift Code name (e.g., <code>BONUS50</code>):</i>")
    await state.set_state(AdminStates.gift_name)

@dp.message(AdminStates.gift_name)
async def adm_create_gift_step2(message: types.Message, state: FSMContext):
    code_name = message.text.strip().upper()
    await state.update_data(gift_code=code_name)
    await message.answer(f"{E['CASH']} <i><b>Step 2:</b> Enter the monetary value (₹) for <code>{code_name}</code>:</i>")
    await state.set_state(AdminStates.gift_amount)

@dp.message(AdminStates.gift_amount)
async def adm_create_gift_step3(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid numeric value:</i>")
        return

    await state.update_data(gift_amount=amount)
    await message.answer(f"{E['USER']} <i><b>Step 3:</b> Enter the maximum usage limit (e.g., <code>10</code>):</i>")
    await state.set_state(AdminStates.gift_max_uses)

@dp.message(AdminStates.gift_max_uses)
async def adm_create_gift_finish(message: types.Message, state: FSMContext):
    try:
        max_uses = int(message.text.strip())
        if max_uses <= 0:
            raise ValueError
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid integer:</i>")
        return

    data = await state.get_data()
    code = data["gift_code"]
    amount = data["gift_amount"]

    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                INSERT INTO gift_codes (code, amount, max_uses, used_count)
                VALUES (?, ?, ?, 0)
            """, (code, amount, max_uses))
            await db.commit()
    except Exception:
        await message.answer(f"{E['CROSS']} <i>Error: Code already exists.</i>")
        await state.clear()
        return

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Gift Codes List", "adm_manage_gifts", style="success")]])
    await message.answer(
        f"{E['CHECK']} <i><b>Gift Code Created Successfully!</b></i>\n\n"
        f"• <i><b>Code:</b> <code>{code}</code></i>\n"
        f"• <i><b>Amount:</b> <code>₹{amount:.2f}</code></i>\n"
        f"• <i><b>Max Users:</b> <code>{max_uses}</code></i>",
        reply_markup=kb
    )

@dp.callback_query(F.data.startswith("adm_delgift_"))
async def adm_delete_gift_code(call: types.CallbackQuery):
    code = call.data.replace("adm_delgift_", "")
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM gift_codes WHERE code = ?", (code,))
        await db.commit()
    await call.answer("Gift code removed.", show_alert=True)
    await adm_gift_codes_menu(call)

# ==============================================================
# CATEGORIES CONTROLLER
# ==============================================================
@dp.callback_query(F.data == "adm_manage_cats")
async def adm_categories_menu(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        return

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM categories") as cur:
            categories = await cur.fetchall()

    buttons = []
    for cat in categories:
        buttons.append([styled_btn(f"Delete: {cat['name']}", f"adm_delcat_{cat['id']}", style="danger")])

    buttons.append([styled_btn("Add New Category", "adm_add_cat_start", style="success")])
    buttons.append([styled_btn("Admin Panel", "admin_panel", style="primary")])

    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        f"{E['FOLDER']} <i><b>Categories Management</b></i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.callback_query(F.data == "adm_add_cat_start")
async def adm_add_category_prompt(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['FOLDER']} <i><b>Enter new category name:</b></i>")
    await state.set_state(AdminStates.add_category_name)

@dp.message(AdminStates.add_category_name)
async def adm_save_category(message: types.Message, state: FSMContext):
    cat_name = message.text.strip()
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO categories (name) VALUES (?)", (cat_name,))
            await db.commit()
        await state.clear()
        kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back to Categories", "adm_manage_cats", style="primary")]])
        await message.answer(f"{E['CHECK']} <i><b>Category Added:</b> <code>{cat_name}</code></i>", reply_markup=kb)
    except Exception:
        await message.answer(f"{E['CROSS']} <i>Error: Category name already exists.</i>")

@dp.callback_query(F.data.startswith("adm_delcat_"))
async def adm_delete_category(call: types.CallbackQuery):
    cat_id = int(call.data.replace("adm_delcat_", ""))
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        await db.commit()
    await call.answer("Category deleted.", show_alert=True)
    await adm_categories_menu(call)

# ==============================================================
# TEMPLATE UPLOADER
# ==============================================================
@dp.callback_query(F.data == "adm_upload_tpl")
async def adm_upload_tpl_step0(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        return

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id, name FROM categories") as cur:
            categories = await cur.fetchall()

    if not categories:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("Create Category First", "adm_add_cat_start", style="success")],
            [styled_btn("Admin Panel", "admin_panel", style="primary")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(f"{E['CROSS']} <i>Please create a category first before adding templates.</i>", reply_markup=kb)
        return

    buttons = []
    for cat in categories:
        buttons.append([styled_btn(f"{cat['name']}", f"adm_pickcat_{cat['id']}", style="primary")])
    buttons.append([styled_btn("Admin Panel", "admin_panel", style="danger")])

    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        f"{E['FOLDER']} <i><b>Step 1:</b> Select a Category:</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(AdminStates.tpl_category)

@dp.callback_query(AdminStates.tpl_category, F.data.startswith("adm_pickcat_"))
async def adm_upload_tpl_step1(call: types.CallbackQuery, state: FSMContext):
    cat_id = int(call.data.replace("adm_pickcat_", ""))
    await state.update_data(category_id=cat_id)

    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['TAG']} <i><b>Step 2:</b> Enter Template Name:</i>")
    await state.set_state(AdminStates.tpl_name)

@dp.message(AdminStates.tpl_name)
async def adm_upload_tpl_step2(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer(f"{E['PIN']} <i><b>Step 3:</b> Enter Features / Description:</i>")
    await state.set_state(AdminStates.tpl_desc)

@dp.message(AdminStates.tpl_desc)
async def adm_upload_tpl_step3(message: types.Message, state: FSMContext):
    await state.update_data(desc=message.text.strip())
    await message.answer(f"{E['MONEY']} <i><b>Step 4:</b> Enter Price (₹, enter 0 for free):</i>")
    await state.set_state(AdminStates.tpl_price)

@dp.message(AdminStates.tpl_price)
async def adm_upload_tpl_step4(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid numeric amount:</i>")
        return

    await state.update_data(price=price)
    await message.answer(f"{E['SPARKLE']} <i><b>Step 5:</b> Send Demo Banner Photo (or send /skip if none):</i>")
    await state.set_state(AdminStates.tpl_banner)

@dp.message(AdminStates.tpl_banner, Command("skip"))
async def adm_upload_tpl_skip_banner(message: types.Message, state: FSMContext):
    await state.update_data(banner_file_id=None)
    await message.answer(f"{E['PACKAGE']} <i><b>Step 6:</b> Upload standalone Python script (<code>.py</code>):</i>")
    await state.set_state(AdminStates.tpl_file)

@dp.message(AdminStates.tpl_banner, F.photo)
async def adm_upload_tpl_step5(message: types.Message, state: FSMContext):
    banner_file_id = message.photo[-1].file_id
    await state.update_data(banner_file_id=banner_file_id)

    await message.answer(f"{E['PACKAGE']} <i><b>Step 6:</b> Upload standalone Python script (<code>.py</code>):</i>")
    await state.set_state(AdminStates.tpl_file)

@dp.message(AdminStates.tpl_file, F.document)
async def adm_upload_tpl_finish(message: types.Message, state: FSMContext):
    if not message.document.file_name.endswith(".py"):
        await message.answer(f"{E['CROSS']} <i>Please upload a Python (<code>.py</code>) file only!</i>")
        return

    data = await state.get_data()
    file_info = await bot.get_file(message.document.file_id)
    save_name = f"tpl_{int(time.time())}.py"
    local_path = os.path.join(TEMPLATES_DIR, save_name)

    await bot.download_file(file_info.file_path, local_path)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO templates (category_id, name, description, file_path, price, banner_file_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data["category_id"], data["name"], data["desc"], local_path, data["price"], data.get("banner_file_id")))
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]])
    await message.answer(
        f"{E['CHECK']} <i><b>Template Added Successfully!</b></i>\n\n"
        f"• <i><b>Name:</b> <code>{data['name']}</code></i>\n"
        f"• <i><b>Price:</b> <code>₹{data['price']}</code></i>",
        reply_markup=kb
    )

# ==============================================================
# BOT STATISTICS
# ==============================================================
@dp.callback_query(F.data == "adm_stats")
async def show_bot_statistics(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        return

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1") as cur:
            banned_users = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM user_bots") as cur:
            total_bots = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM categories") as cur:
            total_cats = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM templates") as cur:
            total_templates = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM gift_codes") as cur:
            total_gifts = (await cur.fetchone())[0]
        async with db.execute("SELECT SUM(balance) FROM users") as cur:
            total_wallet_funds = (await cur.fetchone())[0] or 0.0

    stats_text = (
        f"{E['STATS']} <i><b>Live Server Statistics & Analytics</b></i>\n\n"
        f"• <i><b>Total Users:</b> <code>{total_users}</code> (Banned: <code>{banned_users}</code>)</i>\n"
        f"• <i><b>Hosted Bots:</b> <code>{total_bots}</code></i>\n"
        f"• <i><b>Active Subprocesses:</b> <code>{len(ACTIVE_PROCESSES)}</code></i>\n"
        f"• <i><b>Categories:</b> <code>{total_cats}</code> | <b>Templates:</b> <code>{total_templates}</code></i>\n"
        f"• <i><b>Active Gift Codes:</b> <code>{total_gifts}</code></i>\n"
        f"• <i><b>Total Wallet Holding:</b> <code>₹{total_wallet_funds:.2f}</code></i>\n"
        f"• <i><b>Server Status:</b> <code>Optimal & Running 24/7</code> {E['FLASH']}</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back to Admin", "admin_panel", style="primary")]])
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(stats_text, reply_markup=kb)

# ==============================================================
# CREDIT / DEBIT FUNDS
# ==============================================================
@dp.callback_query(F.data == "adm_add_funds")
async def adm_add_funds_step1(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['CASH']} <i><b>Enter User Telegram ID:</b></i>")
    await state.set_state(AdminStates.add_funds_user)

@dp.message(AdminStates.add_funds_user)
async def adm_add_funds_step2(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid numeric ID:</i>")
        return

    await state.update_data(target_id=target_id)
    await message.answer(f"<i>Enter amount (₹) to credit to User <code>{target_id}</code>:</i>")
    await state.set_state(AdminStates.add_funds_amt)

@dp.message(AdminStates.add_funds_amt)
async def adm_add_funds_step3(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        amt = float(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid numeric amount:</i>")
        return

    data = await state.get_data()
    target_id = data["target_id"]

    await update_balance(target_id, amt)
    await state.clear()

    try:
        await bot.send_message(chat_id=target_id, text=f"{E['GIFT']} <i><b>Admin added ₹{amt:.2f} to your balance!</b></i>")
    except Exception:
        pass

    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]])
    await message.answer(f"{E['CHECK']} <i><b>₹{amt:.2f} credited to User <code>{target_id}</code>!</b></i>", reply_markup=kb)

@dp.callback_query(F.data == "adm_debit_funds")
async def adm_debit_funds_step1(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['CASH']} <i><b>Enter User Telegram ID:</b></i>")
    await state.set_state(AdminStates.debit_funds_user)

@dp.message(AdminStates.debit_funds_user)
async def adm_debit_funds_step2(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid numeric ID:</i>")
        return

    await state.update_data(target_id=target_id)
    await message.answer(f"<i>Enter amount (₹) to debit from User <code>{target_id}</code>:</i>")
    await state.set_state(AdminStates.debit_funds_amt)

@dp.message(AdminStates.debit_funds_amt)
async def adm_debit_funds_step3(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        amt = float(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Please enter a valid numeric amount:</i>")
        return

    data = await state.get_data()
    target_id = data["target_id"]

    await update_balance(target_id, -amt)
    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]])
    await message.answer(f"{E['CHECK']} <i><b>₹{amt:.2f} debited from User <code>{target_id}</code>!</b></i>", reply_markup=kb)

# ==============================================================
# BAN / UNBAN USERS
# ==============================================================
@dp.callback_query(F.data == "adm_ban_user")
async def adm_ban_step1(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['CROSS']} <i><b>Enter User Telegram ID to ban:</b></i>")
    await state.set_state(AdminStates.ban_user)

@dp.message(AdminStates.ban_user)
async def adm_ban_step2(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Invalid ID:</i>")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (target_id,))
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]])
    await message.answer(f"{E['CROSS']} <i>User <code>{target_id}</code> has been banned.</i>", reply_markup=kb)

@dp.callback_query(F.data == "adm_unban_user")
async def adm_unban_step1(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['ONLINE']} <i><b>Enter User Telegram ID to unban:</b></i>")
    await state.set_state(AdminStates.unban_user)

@dp.message(AdminStates.unban_user)
async def adm_unban_step2(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Invalid ID:</i>")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,))
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]])
    await message.answer(f"{E['ONLINE']} <i>User <code>{target_id}</code> has been unbanned.</i>", reply_markup=kb)

# ==============================================================
# MANAGE ADMINS (OWNER ONLY)
# ==============================================================
@dp.callback_query(F.data == "adm_manage_admins")
async def adm_admins_menu(call: types.CallbackQuery):
    if int(call.from_user.id) != OWNER_ID:
        await call.answer("Access restricted to Main Owner.", show_alert=True)
        return

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM admins") as cur:
            admins = await cur.fetchall()

    adm_list_str = "\n".join([f"• <code>{a[0]}</code>" for a in admins]) if admins else "<i>No Sub-Administrators assigned.</i>"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            styled_btn("Add Admin", "adm_add_admin_action", style="success"),
            styled_btn("Remove Admin", "adm_del_admin_action", style="danger")
        ],
        [styled_btn("Admin Panel", "admin_panel", style="primary")]
    ])

    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        f"{E['CROWN']} <i><b>Administrators Management</b></i>\n\n"
        f"• <i><b>Main Owner:</b> <code>{OWNER_ID}</code></i>\n\n"
        f"• <i><b>Sub-Admins:</b></i>\n{adm_list_str}",
        reply_markup=kb
    )

@dp.callback_query(F.data == "adm_add_admin_action")
async def adm_add_admin_input(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['USER']} <i>Enter Telegram User ID to grant Admin rights:</i>")
    await state.set_state(AdminStates.add_admin)

@dp.message(AdminStates.add_admin)
async def adm_add_admin_finish(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        new_admin = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Invalid ID:</i>")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO admins (user_id, added_by) VALUES (?, ?)", (new_admin, message.from_user.id))
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back", "adm_manage_admins", style="primary")]])
    await message.answer(f"{E['CHECK']} <i>User <code>{new_admin}</code> assigned as Admin!</i>", reply_markup=kb)

@dp.callback_query(F.data == "adm_del_admin_action")
async def adm_del_admin_input(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['USER']} <i>Enter Telegram User ID to revoke Admin rights:</i>")
    await state.set_state(AdminStates.del_admin)

@dp.message(AdminStates.del_admin)
async def adm_del_admin_finish(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    try:
        del_adm = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E['CROSS']} <i>Invalid ID:</i>")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM admins WHERE user_id = ?", (del_adm,))
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back", "adm_manage_admins", style="primary")]])
    await message.answer(f"{E['CHECK']} <i>User <code>{del_adm}</code> removed from Admin list!</i>", reply_markup=kb)

# ==============================================================
# FORCE JOIN CHANNELS
# ==============================================================
@dp.callback_query(F.data == "adm_force_channels")
async def adm_channels_menu(call: types.CallbackQuery):
    if not (await is_admin(call.from_user.id)):
        return

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM force_channels") as cur:
            channels = await cur.fetchall()

    buttons = []
    for ch in channels:
        buttons.append([styled_btn(f"Delete: {ch['name']}", f"adm_delch_{ch['id']}", style="danger")])
    buttons.append([styled_btn("Add New Channel", "adm_add_channel", style="success")])
    buttons.append([styled_btn("Admin Panel", "admin_panel", style="primary")])

    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        f"{E['CHANNEL']} <i><b>Force Join Channels Management</b></i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.callback_query(F.data == "adm_add_channel")
async def adm_channel_add_step1(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        await call.answer("Admin only", show_alert=True)
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['CHANNEL']} <i><b>Step 1:</b> Enter the channel display name:</i>")
    await state.set_state(AdminStates.add_ch_name)
    await call.answer()

@dp.message(AdminStates.add_ch_name)
async def adm_channel_add_step2(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return
    name = (message.text or "").strip()
    if not name:
        await message.answer("Please enter a channel name.")
        return
    await state.update_data(ch_name=name)
    await message.answer(f"{E['PIN']} <i><b>Step 2:</b> Enter channel chat ID (usually starts with <code>-100</code>):</i>")
    await state.set_state(AdminStates.add_ch_id)

@dp.message(AdminStates.add_ch_id)
async def adm_channel_add_step3(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return
    channel_id = (message.text or "").strip()
    if not channel_id:
        await message.answer("Please enter the channel chat ID.")
        return
    await state.update_data(ch_id=channel_id)
    await message.answer(f"{E['TAG']} <i><b>Step 3:</b> Enter the channel invite link (normal or join-request link). The bot must be an admin in the channel with permission to receive join requests.</i>")
    await state.set_state(AdminStates.add_ch_link)

@dp.message(AdminStates.add_ch_link)
async def adm_channel_add_step4(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return
    link = (message.text or "").strip()
    if not link.startswith(("https://t.me/", "http://t.me/", "https://telegram.me/", "http://telegram.me/")):
        await message.answer("Please send a valid Telegram invite link starting with https://t.me/ .")
        return
    data = await state.get_data()
    channel_id = str(data["ch_id"]).strip()
    try:
        target_chat = int(channel_id) if channel_id.lstrip("-").isdigit() else channel_id
        chat = await bot.get_chat(target_chat)
        # Require the master bot to be an admin so Telegram sends chat_join_request updates.
        me = await bot.get_me()
        bot_member = await bot.get_chat_member(chat_id=chat.id, user_id=me.id)
        if bot_member.status not in ("administrator", "creator"):
            await message.answer("The master bot must be an administrator in this channel before it can be added. Promote it, then send the channel ID again using /cancel and restart the add-channel flow.")
            return
        # Ensure the supplied ID resolves to the channel the bot will check.
        channel_id = str(chat.id)
    except Exception as exc:
        await message.answer(f"I couldn't access that channel ID. Make sure the bot is an admin and the ID is correct. Details: <code>{html.escape(str(exc))}</code>")
        return
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO force_channels (channel_id, name, invite_link) VALUES (?, ?, ?)", (channel_id, data["ch_name"], link))
        await db.commit()
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Back to Channels", "adm_force_channels", style="primary")]])
    await message.answer(f"{E['CHECK']} <i><b>Force Join Channel Added!</b></i>\nName: <b>{html.escape(data['ch_name'])}</b>\nChat ID: <code>{html.escape(channel_id)}</code>\n\nJoin requests are recorded for verification only; the bot will not approve them automatically.", reply_markup=kb)

@dp.callback_query(F.data.startswith("adm_delch_"))
async def adm_del_channel(call: types.CallbackQuery):
    ch_id = int(call.data.replace("adm_delch_", ""))
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT channel_id FROM force_channels WHERE id = ?", (ch_id,)) as cur:
            old = await cur.fetchone()
        if old:
            await db.execute("DELETE FROM pending_join_requests WHERE channel_id = ?", (str(old[0]),))
        await db.execute("DELETE FROM force_channels WHERE id = ?", (ch_id,))
        await db.commit()
    await call.answer("Channel deleted.", show_alert=True)
    await adm_channels_menu(call)

# ==============================================================
# CONFIGURE UPI & BROADCAST
# ==============================================================
@dp.callback_query(F.data == "adm_set_upi")
async def adm_set_upi_start(call: types.CallbackQuery, state: FSMContext):
    if not (await is_admin(call.from_user.id)):
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(f"{E['CARD']} <i><b>Enter your UPI ID (e.g., <code>merchant@bank</code>):</b></i>")
    await state.set_state(AdminStates.set_upi)

@dp.message(AdminStates.set_upi)
async def adm_set_upi_finish(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_action(message, state)
        return

    upi = message.text.strip()
    await set_setting("admin_upi", upi)
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]])
    await message.answer(f"{E['CHECK']} <i><b>UPI ID Set: <code>{upi}</code></b></i>", reply_markup=kb)

def broadcast_button_keyboard(button_specs):
    rows = []
    for item in button_specs:
        label, url = item[0], item[1]
        style = item[2] if len(item) > 2 else "primary"
        rows.append([styled_btn(label, url=url, style=style)])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


@dp.callback_query(F.data.in_({"adm_broadcast", "adm_broadcast_main", "adm_broadcast_all"}))
async def adm_broadcast_start(call: types.CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("Access Denied.", show_alert=True)
        return

    # The Broadcast button first presents the two requested destinations.
    if call.data == "adm_broadcast":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("Broadcast To Main Bot", "adm_broadcast_main", style="primary")],
            [styled_btn("Broadcast To All Bots", "adm_broadcast_all", style="success")],
            [styled_btn("Back", "admin_panel", style="danger")],
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer("<b>Choose Broadcast Destination</b>\n\nBroadcast To Main Bot: only users of this main bot.\nBroadcast To All Bots: main bot plus all cloned bots.", reply_markup=kb)
        await call.answer()
        return

    await state.clear()
    await state.update_data(broadcast_mode="all_bots" if call.data == "adm_broadcast_all" else "main",
                            broadcast_buttons=[], broadcast_step="content")
    try:
        await call.message.delete()
    except Exception:
        pass
    target = "the main bot and all cloned bots" if call.data == "adm_broadcast_all" else "main bot users only"
    await call.message.answer(f"Send the broadcast content for {target}: text, photo, video, or other media.\nSend /cancel to stop.")
    await state.set_state(AdminStates.broadcast_msg)
    await call.answer()


@dp.message(AdminStates.broadcast_msg)
async def adm_broadcast_get_content(message: types.Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "/cancel":
        await cancel_action(message, state)
        return
    data = await state.get_data()
    if data.get("broadcast_step") == "content":
        await state.update_data(broadcast_chat_id=message.chat.id, broadcast_message_id=message.message_id,
                                broadcast_step="buttons")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("Add Button", "bc_add_button", style="success"),
             styled_btn("Skip Buttons", "bc_skip_buttons", style="primary")],
            [styled_btn("Cancel", "bc_cancel", style="danger")]
        ])
        await message.answer("Content saved. Add one or more URL buttons, or tap Skip Buttons.", reply_markup=kb)
        return
    if data.get("broadcast_step") == "button_label":
        label = (message.text or "").strip()
        if not label or len(label) > 64:
            await message.answer("Button label must be 1–64 characters. Send the label again.")
            return
        await state.update_data(pending_button_label=label, broadcast_step="button_url")
        await message.answer("Now send the button URL beginning with https:// or http://.")
        return
    if data.get("broadcast_step") == "button_url":
        url = (message.text or "").strip()
        if not (url.startswith("https://") or url.startswith("http://")):
            await message.answer("Invalid URL. Send a URL beginning with https:// or http://.")
            return
        buttons = data.get("broadcast_buttons", [])
        buttons.append([data["pending_button_label"], url, "primary"])
        await state.update_data(broadcast_buttons=buttons, pending_button_label=None, broadcast_step="buttons")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [styled_btn("Add Another Button", "bc_add_button", style="success"),
             styled_btn("Finish & Broadcast", "bc_finish", style="primary")],
            [styled_btn("Cancel", "bc_cancel", style="danger")]
        ])
        await message.answer(f"Button added ({len(buttons)}). Add another or finish.", reply_markup=kb)
        return
    await message.answer("Use the buttons shown above to continue.")


@dp.callback_query(F.data == "bc_add_button", AdminStates.broadcast_msg)
async def broadcast_add_button_prompt(call: types.CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    data = await state.get_data()
    if not data.get("broadcast_chat_id"):
        await call.answer("Send broadcast content first.", show_alert=True)
        return
    await state.update_data(broadcast_step="button_label")
    await call.message.answer("Send button label (1–64 characters).")
    await call.answer()


async def _run_broadcast(message: types.Message, state: FSMContext):
    data = await state.get_data()
    mode = data.get("broadcast_mode", "main")
    source_chat = data["broadcast_chat_id"]
    source_message = data["broadcast_message_id"]
    markup = broadcast_button_keyboard(data.get("broadcast_buttons", []))

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM users WHERE is_banned = 0") as cur:
            users = [r[0] for r in await cur.fetchall()]
        if mode == "all_bots":
            async with db.execute("SELECT token FROM user_bots WHERE is_running = 1") as cur:
                cloned_tokens = [r[0] for r in await cur.fetchall()]
        else:
            cloned_tokens = []

    status = await message.answer("Broadcast started. Please wait…")
    sent = failed = 0

    # Main bot is always included. All-bots mode additionally targets each active clone.
    for uid in users:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=source_chat, message_id=source_message, reply_markup=markup)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.04)

    clone_failures = 0
    if mode == "all_bots":
        for token in cloned_tokens:
            child = None
            try:
                child = Bot(token=token)
                # This sends to registered main-bot user IDs who have also started the clone.
                # Telegram rejects delivery to users who have never opened that cloned bot.
                for uid in users:
                    try:
                        await child.copy_message(chat_id=uid, from_chat_id=source_chat, message_id=source_message, reply_markup=markup)
                        sent += 1
                    except Exception:
                        failed += 1
                    await asyncio.sleep(0.04)
            except Exception:
                clone_failures += 1
            finally:
                if child:
                    await child.session.close()

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]])
    target = "main bot users only" if mode == "main" else f"main bot + {len(cloned_tokens)} active cloned bot(s)"
    await status.edit_text(
        f"Broadcast finished.\nTarget: {target}\nSuccessful deliveries: <code>{sent}</code>\nFailed deliveries: <code>{failed}</code>\n\n"
        "Note: Telegram only allows each cloned bot to message users who have started that clone. Cross-bot media copying may be rejected by Telegram.",
        reply_markup=kb
    )


@dp.callback_query(F.data.in_({"bc_skip_buttons", "bc_finish"}), AdminStates.broadcast_msg)
async def broadcast_finish_buttons(call: types.CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await _run_broadcast(call.message, state)
    await call.answer("Broadcast complete.")


@dp.callback_query(F.data == "bc_cancel")
async def broadcast_cancel(call: types.CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await state.clear()
    await call.message.answer("Broadcast cancelled.", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[styled_btn("Admin Panel", "admin_panel", style="primary")]]
    ))
    await call.answer()


# MAIN ENTRY POINT
# ==============================================================
async def main():
    await init_db()
    print("[*] Restoring hosted child bots...")
    await restore_all_bots()
    print("[+] Master Bot Engine is Online & Running!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n[!] Master Bot Stopped.")
