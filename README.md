Republic AI — GPU Miner Dashboard

> GPU Miner Tracker & Ecosystem Dashboard for Republic AI Testnet

**Live Dashboard → [republicstats.xyz](https://republicstats.xyz)**  
**Telegram Bot → [@republicgpuminerstatsbot](https://t.me/republicgpuminerstatsbot)**

---

## 📁 Files

| File | Description |
|------|-------------|
| `republic_bot.py` | Telegram bot — scans chain, tracks miners |
| `api.py` | FastAPI backend — serves data to dashboard |
| `index.html` | Frontend dashboard — hosted on Netlify |
| `requirements.txt` | Python dependencies |

---

## 🤖 Telegram Bot (`republic_bot.py`)

Tracks `SubmitJob` & `SubmitJobResult` transactions per address on Republic AI Testnet.

### Commands
| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Show all commands |
| `/myjobs <rai1...>` | Check your job count & rank |
| `/leaderboard` | Top 25 GPU miners |
| `/stats` | Network overview |
| `/refresh` | Manual refresh & rescan |

### Features
- ✅ Scans from genesis block
- ✅ Incremental scanning (fast after first scan)
- ✅ Auto-scans every 500 new blocks
- ✅ Persistent cache — survives restarts (`scan_cache.json`)
- ✅ Explorer links for each address
- ✅ Full English interface

---

## 🌐 Web Dashboard (`index.html`)

Live at **[republicstats.xyz](https://republicstats.xyz)** — hosted on Netlify

### Features
- ⛓️ Real-time chain status — Live vs Halted + countdown timer
- 📊 Network stats — miners, jobs, last block
- 🏆 Leaderboard — Top 25 with podium (🥇🥈🥉)
- 🔍 Miner search — rank, stats, progress bar vs top miner
- 📋 One-click address copy
- 𝕏 Share your rank on Twitter
- 🤖 Track on Telegram Bot button
- 📚 Guides page — CPU node + GPU miner + Snapshot + Commands
- 🌍 Ecosystem directory — submit & discover projects
- 📱 Mobile friendly — hamburger menu
- 🔄 Auto refresh every 60 seconds

---

## ⚡ API (`api.py`)

Permanent HTTPS endpoint: **[api.republicstats.xyz](https://api.republicstats.xyz)**

| Endpoint | Description |
|----------|-------------|
| `GET /api/stats` | Network overview |
| `GET /api/leaderboard?limit=25` | Ranked miners |
| `GET /api/miner/{address}` | Individual miner stats |
| `GET /api/chain_status` | Live/Halted chain detection |
| `GET /api/ecosystem` | Project directory |
| `POST /api/ecosystem/submit` | Submit new project |
| `GET /api/health` | Health check |

---

## 🛠️ Tech Stack

| Layer | Tech |
|-------|------|
| Bot | Python, python-telegram-bot, aiohttp |
| API | FastAPI, Uvicorn |
| Web Server | Nginx + Let's Encrypt SSL |
| Frontend | Vanilla HTML/CSS/JS |
| Hosting | Netlify (frontend), Hetzner VPS (API + Bot) |
| Domain | republicstats.xyz (GoDaddy) |

---

## 🚀 Setup

### Bot + API
```bash
pip install -r requirements.txt

# Run bot
python3 republic_bot.py

# Run API
uvicorn api:app --host 0.0.0.0 --port 8000
```

### Nginx Config (api.republicstats.xyz)
```nginx
server {
    listen 80;
    server_name api.republicstats.xyz;
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### SSL
```bash
certbot --nginx -d api.republicstats.xyz
```

---

## 🌍 Network Info

| Property | Value |
|----------|-------|
| Chain ID | `raitestnet_77701-1` |
| RPC | `https://rpc.republicai.io` |
| Explorer | `https://explorer.republicai.io` |
| Points Portal | `https://points.republicai.io` |

---

## 👤 Built by

**0xDarkSeidBull** — Republic AI Testnet Validator

- GitHub: [@0xDarkSeidBull](https://github.com/0xDarkSeidBull)
- Twitter: [@cryptobhartiyax](https://x.com/cryptobhartiyax)
- Telegram: [@DarkSeidBull](https://t.me/DarkSeidBull)

---

⭐ Star this repo if it helped you!  
🔁 Share with new Republic AI builders
