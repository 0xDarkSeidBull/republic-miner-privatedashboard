#!/usr/bin/env python3
"""
Republic AI - Dashboard API
FastAPI backend serving bot cache data + ecosystem directory
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json, os
from datetime import datetime

app = FastAPI(title="Republic AI Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
    expose_headers=["*"],
    max_age=3600,
)

CACHE_FILE     = "/root/republic_bot/scan_cache.json"
PROJECTS_FILE  = "/root/republic_bot/projects.json"

# ══════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {"leaderboard": {}, "last_scanned_height": 0, "last_scan_time": "Never"}
    with open(CACHE_FILE) as f:
        return json.load(f)

def load_projects():
    if not os.path.exists(PROJECTS_FILE):
        return []
    with open(PROJECTS_FILE) as f:
        return json.load(f)

def save_projects(projects):
    with open(PROJECTS_FILE, 'w') as f:
        json.dump(projects, f, indent=2)

# ══════════════════════════════════════════════
#  MINER ENDPOINTS
# ══════════════════════════════════════════════

@app.get("/api/stats")
def get_stats():
    cache = load_cache()
    lb    = cache.get("leaderboard", {})
    if not lb:
        return {"error": "No data yet"}
    total_sj  = sum(d["submit_job"] for d in lb.values())
    total_sjr = sum(d["submit_job_result"] for d in lb.values())
    top1      = list(lb.items())[0] if lb else None
    return {
        "total_miners":        len(lb),
        "total_jobs":          total_sj + total_sjr,
        "total_submit_job":    total_sj,
        "total_submit_result": total_sjr,
        "last_scanned_height": cache.get("last_scanned_height", 0),
        "last_scan_time":      cache.get("last_scan_time", "Never"),
        "top_miner": {
            "address": top1[0],
            "jobs":    top1[1]["submit_job"] + top1[1]["submit_job_result"]
        } if top1 else None
    }

@app.get("/api/leaderboard")
def get_leaderboard(limit: int = 25):
    cache = load_cache()
    lb    = cache.get("leaderboard", {})
    result = []
    for rank, (addr, d) in enumerate(lb.items(), 1):
        result.append({
            "rank":               rank,
            "address":            addr,
            "submit_job":         d["submit_job"],
            "submit_job_result":  d["submit_job_result"],
            "total":              d["submit_job"] + d["submit_job_result"]
        })
    return {
        "data":                result[:limit],
        "last_scanned_height": cache.get("last_scanned_height", 0),
        "last_scan_time":      cache.get("last_scan_time", "Never"),
        "total_miners":        len(lb)
    }

@app.get("/api/miner/{address}")
def get_miner(address: str):
    cache = load_cache()
    lb    = cache.get("leaderboard", {})
    if address not in lb:
        raise HTTPException(status_code=404, detail="Miner not found")
    d    = lb[address]
    keys = list(lb.keys())
    rank = keys.index(address) + 1
    return {
        "address":            address,
        "rank":               rank,
        "submit_job":         d["submit_job"],
        "submit_job_result":  d["submit_job_result"],
        "total":              d["submit_job"] + d["submit_job_result"],
        "last_scanned_height": cache.get("last_scanned_height", 0),
        "last_scan_time":     cache.get("last_scan_time", "Never")
    }

# ══════════════════════════════════════════════
#  ECOSYSTEM ENDPOINTS
# ══════════════════════════════════════════════

CATEGORIES = ["DeFi", "AI Agents", "Model Hosting", "Inference", 
              "Data Marketplace", "Research Lab", "Developer Tooling", "Other"]

class ProjectSubmit(BaseModel):
    name:        str
    description: str
    category:    str
    website:     Optional[str] = ""
    twitter:     Optional[str] = ""
    telegram:    Optional[str] = ""
    github:      Optional[str] = ""
    logo_url:    Optional[str] = ""
    submitted_by: Optional[str] = ""

@app.get("/api/ecosystem")
def get_ecosystem(category: Optional[str] = None):
    projects = load_projects()
    if category:
        projects = [p for p in projects if p.get("category") == category]
    return {
        "data":       projects,
        "total":      len(projects),
        "categories": CATEGORIES
    }

@app.post("/api/ecosystem/submit")
def submit_project(project: ProjectSubmit):
    if project.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Choose from: {CATEGORIES}")
    projects = load_projects()
    # Check duplicate
    for p in projects:
        if p["name"].lower() == project.name.lower():
            raise HTTPException(status_code=400, detail="Project already exists")
    new_project = {
        "id":           len(projects) + 1,
        "name":         project.name,
        "description":  project.description,
        "category":     project.category,
        "website":      project.website,
        "twitter":      project.twitter,
        "telegram":     project.telegram,
        "github":       project.github,
        "logo_url":     project.logo_url,
        "submitted_by": project.submitted_by,
        "submitted_at": datetime.now().strftime("%Y-%m-%d"),
        "verified":     False
    }
    projects.append(new_project)
    save_projects(projects)
    return {"success": True, "project": new_project}

@app.put("/api/ecosystem/{project_id}")
def update_project(project_id: int, project: ProjectSubmit):
    projects = load_projects()
    for i, p in enumerate(projects):
        if p["id"] == project_id:
            projects[i].update({
                "name":        project.name,
                "description": project.description,
                "category":    project.category,
                "website":     project.website,
                "twitter":     project.twitter,
                "telegram":    project.telegram,
                "github":      project.github,
                "logo_url":    project.logo_url,
            })
            save_projects(projects)
            return {"success": True, "project": projects[i]}
    raise HTTPException(status_code=404, detail="Project not found")

@app.get("/api/chain_status")
async def chain_status():
    import aiohttp, hashlib, base64
    API_BASE = "https://api-test.republic.vinjan-inc.com"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE}/cosmos/base/tendermint/v1beta1/blocks/latest",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as r:
                if r.status == 200:
                    d = await r.json()
                    height = int(d["block"]["header"]["height"])
                    time   = d["block"]["header"]["time"]
                    # Load last scanned
                    cache = load_cache()
                    last_scanned = cache.get("last_scanned_height", 0)
                    # If latest block > last scanned — chain is live
                    is_live = height > last_scanned
                    return {
                        "is_live": is_live,
                        "latest_block": height,
                        "last_scanned": last_scanned,
                        "block_time": time
                    }
    except Exception as e:
        pass
    # Fallback — chain halted
    cache = load_cache()
    return {
        "is_live": False,
        "latest_block": cache.get("last_scanned_height", 0),
        "last_scanned": cache.get("last_scanned_height", 0),
        "block_time": None
    }

@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}

