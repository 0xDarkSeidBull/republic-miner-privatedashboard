#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json, os, aiohttp, bech32
from datetime import datetime, timezone

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CACHE_FILE           = "/root/republic_bot/scan_cache.json"
PROJECTS_FILE        = "/root/republic_bot/projects.json"
VALIDATOR_CACHE_FILE = "/root/republic_bot/validator_cache.json"
API_BASE             = "https://api-test.republic.vinjan-inc.com"

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {"leaderboard":{}, "last_scanned_height":0, "last_scan_time":"Never"}
    with open(CACHE_FILE) as f:
        return json.load(f)

def load_projects():
    if not os.path.exists(PROJECTS_FILE):
        return []
    with open(PROJECTS_FILE) as f:
        return json.load(f)

def save_projects(p):
    with open(PROJECTS_FILE,'w') as f:
        json.dump(p, f, indent=2)

def load_validator_cache():
    if not os.path.exists(VALIDATOR_CACHE_FILE):
        return {}
    with open(VALIDATOR_CACHE_FILE) as f:
        return json.load(f)

def save_validator_cache(data):
    with open(VALIDATOR_CACHE_FILE,'w') as f:
        json.dump(data, f, indent=2)

def valoper_to_account(valoper: str) -> Optional[str]:
    try:
        hrp, data = bech32.bech32_decode(valoper)
        if data is None: return None
        return bech32.bech32_encode("rai", data)
    except:
        return None

async def fetch_validator_data():
    account_to_moniker = {}
    account_to_uptime  = {}

    async with aiohttp.ClientSession() as session:
        latest_height = 0
        try:
            async with session.get(f"{API_BASE}/cosmos/base/tendermint/v1beta1/blocks/latest", timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    d = await r.json()
                    latest_height = int(d["block"]["header"]["height"])
        except:
            pass

        cons_to_pubkey = {}
        try:
            async with session.get(f"{API_BASE}/cosmos/base/tendermint/v1beta1/validatorsets/latest?pagination.limit=200", timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    d = await r.json()
                    for v in d.get("validators", []):
                        cons_to_pubkey[v["address"]] = v["pub_key"]["key"]
        except:
            pass

        pubkey_to_valoper = {}
        for status in ["BOND_STATUS_BONDED", "BOND_STATUS_UNBONDING", "BOND_STATUS_UNBONDED"]:
            try:
                next_key = None
                while True:
                    url = f"{API_BASE}/cosmos/staking/v1beta1/validators?status={status}&pagination.limit=200"
                    if next_key:
                        url += f"&pagination.key={next_key}"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                        if r.status == 200:
                            d = await r.json()
                            for v in d.get("validators", []):
                                pk      = v.get("consensus_pubkey", {}).get("key", "")
                                valoper = v.get("operator_address", "")
                                moniker = v.get("description", {}).get("moniker", "")
                                if pk:
                                    pubkey_to_valoper[pk] = valoper
                                account = valoper_to_account(valoper)
                                if account:
                                    account_to_moniker[account] = moniker
                            next_key = d.get("pagination", {}).get("next_key")
                            if not next_key:
                                break
                        else:
                            break
            except:
                pass

        cons_to_missed = {}
        cons_to_start  = {}
        try:
            next_key = None
            while True:
                url = f"{API_BASE}/cosmos/slashing/v1beta1/signing_infos?pagination.limit=200"
                if next_key:
                    url += f"&pagination.key={next_key}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status == 200:
                        d = await r.json()
                        for info in d.get("info", []):
                            addr = info.get("address", "")
                            cons_to_missed[addr] = int(info.get("missed_blocks_counter", 0))
                            cons_to_start[addr]  = int(info.get("start_height", 0))
                        next_key = d.get("pagination", {}).get("next_key")
                        if not next_key:
                            break
                    else:
                        break
        except:
            pass

        for cons, pubkey in cons_to_pubkey.items():
            valoper = pubkey_to_valoper.get(pubkey)
            if not valoper:
                continue
            account = valoper_to_account(valoper)
            if not account:
                continue
            missed = cons_to_missed.get(cons, 0)
            start  = cons_to_start.get(cons, 0)
            window = max(latest_height - start, 1)
            uptime = round(max(0, (window - missed) / window * 100), 2)
            account_to_uptime[account] = uptime

    result = {
        "account_to_moniker": account_to_moniker,
        "account_to_uptime":  account_to_uptime,
        "updated_at":         datetime.now().isoformat()
    }
    save_validator_cache(result)
    return result

@app.get("/api/stats")
def get_stats():
    cache = load_cache()
    lb = cache.get("leaderboard", {})
    if not lb:
        return {"error":"No data yet"}
    total_sj  = sum(d["submit_job"] for d in lb.values())
    total_sjr = sum(d["submit_job_result"] for d in lb.values())
    top1 = list(lb.items())[0]
    return {
        "total_miners":        len(lb),
        "total_jobs":          total_sj + total_sjr,
        "total_submit_job":    total_sj,
        "total_submit_result": total_sjr,
        "last_scanned_height": cache.get("last_scanned_height", 0),
        "last_scan_time":      cache.get("last_scan_time", "Never"),
        "top_miner":           {"address": top1[0], "jobs": top1[1]["submit_job"]+top1[1]["submit_job_result"]}
    }

@app.get("/api/leaderboard")
async def get_leaderboard(limit: int = 25, refresh: bool = False):
    cache  = load_cache()
    lb     = cache.get("leaderboard", {})
    vcache = load_validator_cache()
    if not vcache or refresh:
        vcache = await fetch_validator_data()
    account_to_moniker = vcache.get("account_to_moniker", {})
    account_to_uptime  = vcache.get("account_to_uptime", {})
    result = []
    for i, (addr, d) in enumerate(lb.items()):
        result.append({
            "rank":              i + 1,
            "address":           addr,
            "moniker":           account_to_moniker.get(addr, ""),
            "submit_job":        d["submit_job"],
            "submit_job_result": d["submit_job_result"],
            "total":             d["submit_job"] + d["submit_job_result"],
            "uptime":            account_to_uptime.get(addr, None)
        })
    return {
        "data":                    result[:limit],
        "last_scanned_height":     cache.get("last_scanned_height", 0),
        "last_scan_time":          cache.get("last_scan_time", "Never"),
        "total_miners":            len(lb),
        "validator_cache_updated": vcache.get("updated_at", "Never")
    }

@app.get("/api/validators/refresh")
async def refresh_validators():
    vcache = await fetch_validator_data()
    return {"success": True, "validators": len(vcache.get("account_to_moniker", {})), "updated_at": vcache.get("updated_at")}

@app.get("/api/miner/{address}")
async def get_miner(address: str):
    cache = load_cache()
    lb    = cache.get("leaderboard", {})
    if address not in lb:
        raise HTTPException(status_code=404, detail="Miner not found")
    d    = lb[address]
    rank = list(lb.keys()).index(address) + 1
    vcache = load_validator_cache()
    if not vcache:
        vcache = await fetch_validator_data()
    return {
        "address":             address,
        "rank":                rank,
        "moniker":             vcache.get("account_to_moniker", {}).get(address, ""),
        "submit_job":          d["submit_job"],
        "submit_job_result":   d["submit_job_result"],
        "total":               d["submit_job"] + d["submit_job_result"],
        "uptime":              vcache.get("account_to_uptime", {}).get(address, None),
        "last_scanned_height": cache.get("last_scanned_height", 0),
        "last_scan_time":      cache.get("last_scan_time", "Never")
    }

CATEGORIES = ["DeFi","AI Agents","Model Hosting","Inference","Data Marketplace","Research Lab","Developer Tooling","Other"]

class ProjectSubmit(BaseModel):
    name: str; description: str; category: str
    website: Optional[str] = ""; twitter: Optional[str] = ""
    telegram: Optional[str] = ""; github: Optional[str] = ""
    submitted_by: Optional[str] = ""

@app.get("/api/ecosystem")
def get_ecosystem(category: Optional[str] = None):
    projects = load_projects()
    if category:
        projects = [p for p in projects if p.get("category") == category]
    return {"data": projects, "total": len(projects), "categories": CATEGORIES}

@app.post("/api/ecosystem/submit")
def submit_project(project: ProjectSubmit):
    if project.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid category")
    projects = load_projects()
    for p in projects:
        if p["name"].lower() == project.name.lower():
            raise HTTPException(status_code=400, detail="Project already exists")
    new = {"id": len(projects)+1, "name": project.name, "description": project.description,
           "category": project.category, "website": project.website, "twitter": project.twitter,
           "telegram": project.telegram, "github": project.github,
           "submitted_by": project.submitted_by,
           "submitted_at": datetime.now().strftime("%Y-%m-%d"), "verified": False}
    projects.append(new)
    save_projects(projects)
    return {"success": True, "project": new}

@app.get("/api/chain_status")
async def chain_status():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE}/cosmos/base/tendermint/v1beta1/blocks/latest", timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    d      = await r.json()
                    height = int(d["block"]["header"]["height"])
                    t      = d["block"]["header"]["time"]
                    cache  = load_cache()
                    last_scanned = cache.get("last_scanned_height", 0)

                    # ✅ FIX: Time-based check — agar last block 5 min se zyada purana ho tabhi HALTED
                    block_dt     = datetime.fromisoformat(t.replace("Z", "+00:00"))
                    age_seconds  = (datetime.now(timezone.utc) - block_dt).total_seconds()
                    is_live      = age_seconds < 300  # 5 minutes threshold

                    return {
                        "is_live":      is_live,
                        "latest_block": height,
                        "last_scanned": last_scanned,
                        "block_time":   t,
                        "block_age_seconds": int(age_seconds)
                    }
    except:
        pass

    # Fallback: RPC down ho to cache se check karo
    cache = load_cache()
    last_scan_time = cache.get("last_scan_time", "Never")
    is_live = False
    if last_scan_time and last_scan_time != "Never":
        try:
            scan_dt     = datetime.strptime(last_scan_time, "%Y-%m-%d %H:%M UTC").replace(tzinfo=timezone.utc)
            age_seconds = (datetime.now(timezone.utc) - scan_dt).total_seconds()
            is_live     = age_seconds < 600  # 10 min fallback threshold
        except:
            pass

    return {
        "is_live":      is_live,
        "latest_block": cache.get("last_scanned_height", 0),
        "last_scanned": cache.get("last_scanned_height", 0),
        "block_time":   None,
        "block_age_seconds": None
    }

@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}
