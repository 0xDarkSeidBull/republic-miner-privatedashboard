#!/usr/bin/env python3
"""Republic AI Testnet - GPU Miner Job Tracker Bot v3.2 (English)"""

import asyncio, logging, aiohttp, hashlib, base64, json, os, json, os
from datetime import datetime
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

BOT_TOKEN   = "8735306069:AAGZm7uK1gMD_j1LgzY3MlPHSZeNfQJDJro"
API_BASE    = "https://api-test.republic.vinjan-inc.com"
SCAN_BLOCKS = 999999
BLOCK_BATCH = 20
CACHE_FILE  = "scan_cache.json"  # saves progress across restarts

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

leaderboard_cache: dict = {}
last_scan_time: str     = "Never"
is_scanning: bool       = False
last_scanned_height: int = 0   # 0 = full scan needed

# ══════════════════════════════════════════════
#  CACHE PERSISTENCE (survive restarts)
# ══════════════════════════════════════════════

def save_cache():
    """Save leaderboard + last scanned height to disk"""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump({
                "last_scanned_height": last_scanned_height,
                "last_scan_time": last_scan_time,
                "leaderboard": leaderboard_cache
            }, f)
        log.info(f"💾 Cache saved (block {last_scanned_height})")
    except Exception as e:
        log.error(f"Cache save error: {e}")

def load_cache():
    """Load previously saved leaderboard from disk"""
    global leaderboard_cache, last_scanned_height, last_scan_time
    if not os.path.exists(CACHE_FILE):
        log.info("No cache file found — will do full scan")
        return
    try:
        with open(CACHE_FILE) as f:
            data = json.load(f)
        last_scanned_height = data.get("last_scanned_height", 0)
        last_scan_time      = data.get("last_scan_time", "Never")
        leaderboard_cache   = data.get("leaderboard", {})
        log.info(f"✅ Cache loaded | block={last_scanned_height} | miners={len(leaderboard_cache)}")
    except Exception as e:
        log.error(f"Cache load error: {e}")

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
def _polymod(vals):
    GEN=[0x3b6a57b2,0x26508e6d,0x1ea119fa,0x3d4233dd,0x2a1462b3]; chk=1
    for v in vals:
        b=chk>>25; chk=(chk&0x1ffffff)<<5^v
        for i in range(5): chk^=GEN[i] if (b>>i)&1 else 0
    return chk
def _hrp_expand(hrp): return [ord(x)>>5 for x in hrp]+[0]+[ord(x)&31 for x in hrp]
def bech32_decode(bech):
    bech=bech.lower(); pos=bech.rfind("1")
    if pos<1 or pos+7>len(bech): return None,None
    hrp=bech[:pos]; data=[CHARSET.find(c) for c in bech[pos+1:]]
    return (None,None) if -1 in data else (hrp,data[:-6])
def bech32_encode(hrp,data):
    combined=data+[0,0,0,0,0,0]; pv=_polymod(_hrp_expand(hrp)+combined)^1
    chk=[(pv>>5*(5-i))&31 for i in range(6)]
    return hrp+"1"+"".join(CHARSET[d] for d in data+chk)
def convert_prefix(addr,pfx):
    try: _,data=bech32_decode(addr); return bech32_encode(pfx,data) if data else None
    except: return None
def to_account(addr):
    if addr.startswith("rai1"): return addr
    if addr.startswith("raivaloper1"): return convert_prefix(addr,"rai")
    return None
def to_operator(addr):
    if addr.startswith("raivaloper1"): return addr
    if addr.startswith("rai1"): return convert_prefix(addr,"raivaloper")
    return None

def tx_hash(b64):
    try: return hashlib.sha256(base64.b64decode(b64)).hexdigest().upper()
    except: return None

async def fetch_json(session,url,params=None):
    try:
        async with session.get(url,params=params,timeout=aiohttp.ClientTimeout(total=20)) as r:
            if r.status==200: return await r.json()
    except Exception as e: log.debug(f"fetch {url}: {e}")
    return None

async def get_latest_height(session):
    d=await fetch_json(session,f"{API_BASE}/cosmos/base/tendermint/v1beta1/blocks/latest")
    return int(d["block"]["header"]["height"]) if d else 0

async def get_block_tx_hashes(session,height):
    d=await fetch_json(session,f"{API_BASE}/cosmos/base/tendermint/v1beta1/blocks/{height}")
    if not d: return []
    return [h for h in (tx_hash(t) for t in d.get("block",{}).get("data",{}).get("txs",[])) if h]

async def get_tx(session,txhash):
    return await fetch_json(session,f"{API_BASE}/cosmos/tx/v1beta1/txs/{txhash}")

def parse_tx(tx_data):
    results=[]
    try:
        tx=tx_data.get("tx") or {}
        for msg in tx.get("body",{}).get("messages",[]):
            t=msg.get("@type",""); v=msg.get("validator","") or msg.get("sender","") or msg.get("creator","")
            if not v: continue
            acc=to_account(v)
            if not acc: continue
            if   "MsgSubmitJobResult" in t: results.append((acc,"sjr"))
            elif "MsgSubmitJob"       in t: results.append((acc,"sj"))
    except: pass
    return results

async def refresh_leaderboard():
    global leaderboard_cache, last_scan_time, is_scanning, last_scanned_height
    if is_scanning: return
    is_scanning = True

    try:
        async with aiohttp.ClientSession() as session:
            latest = await get_latest_height(session)
            if not latest: return

            # First scan: genesis to latest
            # Subsequent scans: last_scanned_height+1 to latest (incremental)
            if last_scanned_height == 0:
                start = 1
                log.info(f"🔄 FULL scan: {start}→{latest} (first time, may take a while...)")
                data = defaultdict(lambda: {"submit_job": 0, "submit_job_result": 0})
            else:
                start = last_scanned_height + 1
                if start > latest:
                    log.info(f"✅ Already up to date at block {latest}")
                    is_scanning = False
                    return
                log.info(f"🔄 INCREMENTAL scan: {start}→{latest} ({latest-start} new blocks)")
                # Start from existing cache data
                data = defaultdict(lambda: {"submit_job": 0, "submit_job_result": 0}, 
                                   {k: dict(v) for k,v in leaderboard_cache.items()})

            for batch_top in range(latest, start-1, -BLOCK_BATCH):
                batch_bot = max(batch_top - BLOCK_BATCH, start-1)
                heights = list(range(batch_top, batch_bot, -1))
                if not heights: break

                hl = await asyncio.gather(*[get_block_tx_hashes(session, h) for h in heights], return_exceptions=True)
                all_hashes = [h for r in hl if isinstance(r, list) for h in r]

                if all_hashes:
                    txs = await asyncio.gather(*[get_tx(session, h) for h in all_hashes], return_exceptions=True)
                    for tx in txs:
                        if not tx or isinstance(tx, Exception): continue
                        for acc, kind in parse_tx(tx):
                            if kind == "sj": data[acc]["submit_job"] += 1
                            else:            data[acc]["submit_job_result"] += 1

                log.info(f"  Batch {batch_top}→{batch_bot} | miners: {len(data)}")
                await asyncio.sleep(0.2)

            last_scanned_height = latest

    except Exception as e:
        log.error(f"Scan error: {e}")
    finally:
        is_scanning = False

    leaderboard_cache = dict(sorted(data.items(), key=lambda x: x[1]["submit_job"]+x[1]["submit_job_result"], reverse=True))
    last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    save_cache()
    log.info(f"✅ Done | scanned up to block {last_scanned_height} | {len(leaderboard_cache)} unique miners")
    for i,(addr,d) in enumerate(list(leaderboard_cache.items())[:5]):
        log.info(f"  #{i+1} {addr[:20]}... sj={d['submit_job']} sjr={d['submit_job_result']}")

AUTO_SCAN_INTERVAL = 500   # scan every 500 new blocks (~40-50 min on this chain)

async def auto_refresh_task():
    """Auto scan when 500 new blocks appear on chain"""
    global last_scanned_height
    while True:
        try:
            await asyncio.sleep(60)  # check every 60 seconds
            async with aiohttp.ClientSession() as session:
                latest = await get_latest_height(session)
            if latest and last_scanned_height > 0:
                new_blocks = latest - last_scanned_height
                if new_blocks >= AUTO_SCAN_INTERVAL:
                    log.info(f"🔔 {new_blocks} new blocks detected ({last_scanned_height}→{latest}) — auto scanning!")
                    await refresh_leaderboard()
        except Exception as e:
            log.error(f"Auto scan check error: {e}")

def build_leaderboard_text():
    top10=list(leaderboard_cache.items())[:25]
    if not top10: return "😔 No miner data found yet."
    medals=["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟","1️⃣1️⃣","1️⃣2️⃣","1️⃣3️⃣","1️⃣4️⃣","1️⃣5️⃣","1️⃣6️⃣","1️⃣7️⃣","1️⃣8️⃣","1️⃣9️⃣","2️⃣0️⃣","2️⃣1️⃣","2️⃣2️⃣","2️⃣3️⃣","2️⃣4️⃣","2️⃣5️⃣"]
    lines=["🏆 *Republic AI — Top 25 GPU Miners*","━━━━━━━━━━━━━━━━━━━━",f"🕐 `{last_scan_time}` | 📦 Block: `{last_scanned_height}`\n"]
    for i,(acc,d) in enumerate(top10):
        tot=d["submit_job"]+d["submit_job_result"]
        lines.append(f"{medals[i]} `{acc}`\n    📦 {d['submit_job']} | ✅ {d['submit_job_result']} | 🔢 *{tot}*")
    lines+=["━━━━━━━━━━━━━━━━━━━━",f"👥 Total miners tracked: `{len(leaderboard_cache)}`",f"🔔 Auto-scan every {AUTO_SCAN_INTERVAL} new blocks"]
    return "\n".join(lines)

def build_myjobs_text(address,d,rank_text):
    sj=d["submit_job"]; sjr=d["submit_job_result"]; total=sj+sjr
    status=("❌ No jobs found yet — is your miner running?" if total==0 else
            "🟡 Mining started — keep going!"              if total<50  else
            "🟢 Active miner!"                              if total<500 else
            "🔥 Pro miner! Outstanding!")
    operator=to_operator(address) or address
    short=f"{address[:12]}...{address[-6:]}"
    return (f"📊 *GPU Miner Stats*\n━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 `{short}`\n\n"
            f"📦 *SubmitJob:* `{sj}`\n"
            f"✅ *SubmitJobResult:* `{sjr}`\n"
            f"🔢 *Total Jobs:* `{total}`\n"
            f"{rank_text}\n\n{status}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 `{last_scan_time}` | 📦 Block: `{last_scanned_height}`\n"
            f"🔗 [Account](https://explorer.vinjan-inc.com/republic-testnet/account/{address}) | "
            f"[Validator](https://explorer.vinjan-inc.com/republic-testnet/staking/{operator})")

def get_myjobs_data(address):
    d=leaderboard_cache.get(address,{"submit_job":0,"submit_job_result":0})
    if address in leaderboard_cache:
        rank=list(leaderboard_cache.keys()).index(address)+1
        rank_text=f"\n🏆 *Leaderboard Rank:* #{rank}"
    else:
        rank_text="\n🏆 *Rank:* Not in leaderboard yet"
    return d,rank_text

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Republic AI Testnet — GPU Miner Tracker*\n\n"
        "This bot tracks GPU miner job counts on the Republic AI testnet.\n\n"
        "📌 *Commands:*\n"
        "➤ `/myjobs <rai_address>` — Check your job count\n"
        "➤ `/leaderboard` — Top 10 GPU miners\n"
        "➤ `/refresh` — Manually refresh leaderboard\n"
        "➤ `/stats` — Network overview & total jobs\n"
        "➤ `/help` — Show this message\n\n"
        "💡 *Example:*\n"
        "`/myjobs rai1xcr42hlh85kutaqtmyxw2zu8pr3nk5rks6nlp5`",
        parse_mode="Markdown")

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, ctx)

async def cmd_myjobs(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args=ctx.args
    if not args:
        await update.message.reply_text(
            "❌ Please provide your address!\nExample: `/myjobs rai1xcr42hlh85kutaqtmyxw2zu8pr3nk5rks6nlp5`",
            parse_mode="Markdown"); return
    raw=args[0].strip(); address=to_account(raw)
    if not address or len(address)<20:
        await update.message.reply_text(
            "❌ Invalid address!\nMust start with `rai1...` or `raivaloper1...`",
            parse_mode="Markdown"); return
    kb=InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Refresh",callback_data=f"addr:{address}"),
        InlineKeyboardButton("🏆 Leaderboard",callback_data="leaderboard")]])
    if leaderboard_cache:
        d,rank_text=get_myjobs_data(address)
        await update.message.reply_text(build_myjobs_text(address,d,rank_text),
            parse_mode="Markdown",reply_markup=kb,disable_web_page_preview=True)
    elif is_scanning:
        await update.message.reply_text(
            "⏳ Background scan is running...\nPlease try `/myjobs` again in a moment!",
            parse_mode="Markdown")
    else:
        msg=await update.message.reply_text("⏳ Scanning chain, please wait...")
        await refresh_leaderboard()
        d,rank_text=get_myjobs_data(address)
        await msg.edit_text(build_myjobs_text(address,d,rank_text),
            parse_mode="Markdown",reply_markup=kb,disable_web_page_preview=True)

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not leaderboard_cache:
        await update.message.reply_text("⏳ No data yet — scan in progress!"); return
    total_jobs = sum(d["submit_job"]+d["submit_job_result"] for d in leaderboard_cache.values())
    total_sj   = sum(d["submit_job"] for d in leaderboard_cache.values())
    total_sjr  = sum(d["submit_job_result"] for d in leaderboard_cache.values())
    top1       = list(leaderboard_cache.items())[0]
    top1_acc   = top1[0]
    top1_jobs  = top1[1]["submit_job"] + top1[1]["submit_job_result"]
    await update.message.reply_text(
        f"📡 *Republic AI Testnet — Network Stats*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 *Total Miners:* `{len(leaderboard_cache)}`\n"
        f"🔢 *Total Jobs:* `{total_jobs:,}`\n"
        f"📦 *SubmitJob:* `{total_sj:,}`\n"
        f"✅ *SubmitJobResult:* `{total_sjr:,}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 *Top Miner:* `{top1_acc[:16]}...`\n"
        f"   └ `{top1_jobs:,}` total jobs\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Last Block Scanned:* `{last_scanned_height:,}`\n"
        f"🕐 *Last Updated:* `{last_scan_time}`",
        parse_mode="Markdown"
    )

async def cmd_leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh",callback_data="refresh_lb")]])
    if not leaderboard_cache:
        if is_scanning:
            await update.message.reply_text("⏳ Scan in progress... please try again shortly!"); return
        wait=await update.message.reply_text("⏳ First time scan in progress... 1-2 min!")
        await refresh_leaderboard()
        try: await wait.delete()
        except: pass
    await update.message.reply_text(build_leaderboard_text(),parse_mode="Markdown",reply_markup=kb)

async def cmd_refresh(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if is_scanning:
        await update.message.reply_text("⏳ Scan already in progress..."); return
    async with aiohttp.ClientSession() as session:
        latest = await get_latest_height(session)
    new_blocks = latest - last_scanned_height if last_scanned_height else latest
    msg = await update.message.reply_text(
        f"🔍 *Scan Info*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Currently scanned:* `{last_scanned_height:,}`\n"
        f"🔝 *Latest block:* `{latest:,}`\n"
        f"➕ *New blocks to scan:* `{new_blocks:,}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ Scanning now...",
        parse_mode="Markdown")
    await refresh_leaderboard()
    await msg.edit_text(
        f"✅ *Refresh complete!*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Scanned up to block:* `{last_scanned_height:,}`\n"
        f"🕐 *Updated:* `{last_scan_time}`\n"
        f"👥 *Miners tracked:* `{len(leaderboard_cache)}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔔 Next auto-scan in ~{AUTO_SCAN_INTERVAL} new blocks",
        parse_mode="Markdown")

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query=update.callback_query; await query.answer()
    kb_lb=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh",callback_data="refresh_lb")]])
    if query.data=="leaderboard":
        await query.message.reply_text(build_leaderboard_text(),parse_mode="Markdown",reply_markup=kb_lb)
    elif query.data=="refresh_lb":
        if is_scanning: await query.answer("Already scanning...",show_alert=True); return
        await query.edit_message_text("⏳ Refreshing leaderboard...")
        await refresh_leaderboard()
        await query.edit_message_text(build_leaderboard_text(),parse_mode="Markdown",reply_markup=kb_lb)
    elif query.data.startswith("addr:"):
        address=query.data.split(":",1)[1]; d,rank_text=get_myjobs_data(address)
        kb=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Refresh",callback_data=f"addr:{address}"),
            InlineKeyboardButton("🏆 Leaderboard",callback_data="leaderboard")]])
        await query.edit_message_text(build_myjobs_text(address,d,rank_text),
            parse_mode="Markdown",reply_markup=kb,disable_web_page_preview=True)

async def post_init(app: Application):
    load_cache()  # load previous scan from disk
    asyncio.create_task(auto_refresh_task())
    log.info("✅ Auto-refresh started (30 min interval)")

def main():
    app=Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start",       cmd_start))
    app.add_handler(CommandHandler("help",        cmd_help))
    app.add_handler(CommandHandler("myjobs",      cmd_myjobs))
    app.add_handler(CommandHandler("stats",       cmd_stats))
    app.add_handler(CommandHandler("leaderboard", cmd_leaderboard))
    app.add_handler(CommandHandler("refresh",     cmd_refresh))
    app.add_handler(CallbackQueryHandler(callback_handler))
    log.info("🚀 Republic AI Bot v3.2 (EN) starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
