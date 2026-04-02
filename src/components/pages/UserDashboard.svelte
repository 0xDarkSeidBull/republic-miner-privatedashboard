<script>
  import { onMount } from 'svelte';
  import { API, fmt } from '../../stores/app.js';

  let walletAddress = '';
  let keplrConnected = false;
  let connecting = false;
  let statsLoading = false;
  let badgeData = null;
  let error = '';
  let mintingTier = null;
  let mintResults = {};

  async function connectKeplr() {
    connecting = true;
    error = '';
    try {
      if (!window.keplr) {
        error = 'Keplr wallet not found! Please install Keplr extension.';
        connecting = false;
        return;
      }
      await window.keplr.enable('raitestnet_77701-1');
      const offlineSigner = window.keplr.getOfflineSigner('raitestnet_77701-1');
      const accounts = await offlineSigner.getAccounts();
      walletAddress = accounts[0].address;
      keplrConnected = true;
      await fetchBadgeData();
    } catch(e) {
      error = 'Failed to connect Keplr: ' + e.message;
    }
    connecting = false;
  }

  async function fetchBadgeData() {
    if (!walletAddress) return;
    statsLoading = true;
    try {
      const r = await fetch(`${API}/api/badge/status/v2/${walletAddress}`, {
        signal: AbortSignal.timeout(10000)
      });
      badgeData = await r.json();
    } catch(e) {
      error = 'Failed to fetch stats.';
    }
    statsLoading = false;
  }

  async function mintBadge(tier) {
    mintingTier = tier;
    mintResults[tier] = null;
    try {
      if (!window.keplr) throw new Error('Keplr not found');
      await window.keplr.enable('raitestnet_77701-1');
      const key = await window.keplr.getKey('raitestnet_77701-1');
      const sender = key.bech32Address;
      const res = await fetch(`${API}/api/badge/mint/v2`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address: sender, tier })
      });
      const data = await res.json();
      if (data.success) {
        mintResults[tier] = { success: true, tx_hash: data.tx_hash, explorer: data.explorer };
        await fetchBadgeData();
      } else {
        mintResults[tier] = { success: false, reason: data.reason };
      }
    } catch(e) {
      mintResults[tier] = { success: false, reason: e.message };
    }
    mintingTier = null;
  }

  function disconnect() {
    walletAddress = '';
    keplrConnected = false;
    badgeData = null;
    mintResults = {};
    error = '';
  }

  function tierColor(tier) {
    if (tier === 'Gold') return '#FFD700';
    if (tier === 'Silver') return '#C0C0C0';
    return '#CD7F32';
  }

  function tierGlow(tier) {
    if (tier === 'Gold') return '0 0 32px rgba(255,215,0,0.25)';
    if (tier === 'Silver') return '0 0 32px rgba(192,192,192,0.2)';
    return '0 0 32px rgba(205,127,50,0.2)';
  }

  function tierBg(tier) {
    if (tier === 'Gold') return 'radial-gradient(ellipse at top, rgba(255,215,0,0.1) 0%, var(--bg2) 70%)';
    if (tier === 'Silver') return 'radial-gradient(ellipse at top, rgba(192,192,192,0.08) 0%, var(--bg2) 70%)';
    return 'radial-gradient(ellipse at top, rgba(205,127,50,0.1) 0%, var(--bg2) 70%)';
  }

  function tierBorder(tier) {
    if (tier === 'Gold') return 'rgba(255,215,0,0.35)';
    if (tier === 'Silver') return 'rgba(192,192,192,0.3)';
    return 'rgba(205,127,50,0.35)';
  }

  // SVG coin badge
  function badgeSvg(tier, minted) {
    const c = tierColor(tier);
    const opacity = minted ? '1' : '0.35';
    const label = tier === 'Gold' ? 'GOLD' : tier === 'Silver' ? 'SILVER' : 'BRONZE';
    const icon = tier === 'Gold' ? '🥇' : tier === 'Silver' ? '🥈' : '🥉';
    return `data:image/svg+xml;utf8,${encodeURIComponent(`
<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
  <defs>
    <radialGradient id="bg${tier}" cx="50%" cy="40%" r="60%">
      <stop offset="0%" stop-color="${c}" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="${c}" stop-opacity="0.05"/>
    </radialGradient>
  </defs>
  <circle cx="60" cy="60" r="55" fill="url(#bg${tier})" stroke="${c}" stroke-width="2.5" opacity="${opacity}"/>
  <circle cx="60" cy="60" r="46" fill="none" stroke="${c}" stroke-width="1" opacity="${opacity}" stroke-dasharray="4 3"/>
  <text x="60" y="52" text-anchor="middle" font-size="32" opacity="${opacity}">${icon}</text>
  <text x="60" y="76" text-anchor="middle" font-family="'Bebas Neue',sans-serif" font-size="13" fill="${c}" opacity="${opacity}" letter-spacing="2">${label}</text>
  <text x="60" y="90" text-anchor="middle" font-family="monospace" font-size="8" fill="${c}" opacity="${minted ? '0.6' : '0.2'}">${minted ? 'ON-CHAIN' : 'LOCKED'}</text>
</svg>`)}`;
  }
</script>

<!-- HERO -->
<div class="hero">
  <div class="hero-bg"></div>
  <div style="position:relative;z-index:1">
    <div class="hero-eyebrow"><span class="hero-eyebrow-dot"></span>Republic AI · User Dashboard</div>
    <h1><span class="line1">YOUR</span><span class="line2">DASHBOARD</span></h1>
    <p class="hero-sub">Connect your Keplr wallet to view your GPU stats and mint your badges</p>
  </div>
</div>

<div style="max-width:1000px;margin:0 auto;padding:0 28px 60px">

  {#if !keplrConnected}
    <div style="text-align:center;padding:60px 20px">
      <div style="font-size:64px;margin-bottom:20px">🔗</div>
      <h2 style="font-size:28px;font-family:'Bebas Neue',sans-serif;color:var(--accent);margin-bottom:12px">
        CONNECT WALLET TO CHECK YOUR STATS
      </h2>
      <p style="color:var(--muted);font-size:14px;margin-bottom:32px">
        Connect your Keplr wallet to view your GPU mining stats and mint your achievement badges
      </p>
      <button on:click={connectKeplr} disabled={connecting}
        style="background:var(--accent);color:#000;border:none;padding:16px 40px;font-size:16px;font-family:'Bebas Neue',sans-serif;letter-spacing:2px;border-radius:8px;cursor:pointer;font-weight:700">
        {connecting ? 'CONNECTING...' : '⚡ CONNECT KEPLR'}
      </button>
      {#if error}<div class="error-msg" style="margin-top:16px">{error}</div>{/if}
    </div>

  {:else}
    <!-- Wallet bar -->
    <div style="display:flex;justify-content:space-between;align-items:center;padding:20px 0 24px">
      <div>
        <div style="font-size:11px;color:var(--muted);text-transform:uppercase;margin-bottom:4px">Connected Wallet</div>
        <div style="font-size:13px;color:var(--accent);font-family:monospace">{walletAddress}</div>
      </div>
      <button on:click={disconnect}
        style="background:transparent;border:1px solid var(--border);color:var(--muted);padding:8px 16px;border-radius:6px;cursor:pointer;font-size:12px">
        Disconnect
      </button>
    </div>

    {#if statsLoading}
      <div class="loading" style="text-align:center;padding:40px">Loading your stats...</div>

    {:else if badgeData}
      <!-- Stats -->
      <div class="stats-grid" style="margin-top:0">
        <div class="stat-card">
          <div class="stat-label">Submit Results</div>
          <div class="stat-value fire">{fmt(badgeData.submit_job_result)}</div>
          <div class="stat-sub">GPU Jobs Completed</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Submit Jobs</div>
          <div class="stat-value">{fmt(badgeData.submit_job)}</div>
          <div class="stat-sub">Jobs Submitted</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Badges Minted</div>
          <div class="stat-value fire">{badgeData.badges.filter(b => b.minted).length} / 3</div>
          <div class="stat-sub">Achievement Badges</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Eligible For</div>
          <div class="stat-value" style="color:var(--accent3)">{badgeData.badges.filter(b => b.eligible && !b.minted).length} Badges</div>
          <div class="stat-sub">Ready to mint</div>
        </div>
      </div>

      <!-- Badge Grid -->
      <div style="margin-top:32px">
        <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:2px;margin-bottom:20px">Achievement Badges</div>

        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px">
          {#each badgeData.badges as badge}
            <div style="background:{tierBg(badge.tier)};border:1px solid {tierBorder(badge.tier)};border-radius:20px;padding:28px 20px;text-align:center;box-shadow:{badge.minted ? tierGlow(badge.tier) : 'none'};transition:box-shadow .3s;position:relative;overflow:hidden">

              <!-- Minted ribbon -->
              {#if badge.minted}
                <div style="position:absolute;top:14px;right:-22px;background:{tierColor(badge.tier)};color:#000;font-size:9px;font-weight:800;letter-spacing:.1em;padding:3px 32px;transform:rotate(35deg);font-family:'Bebas Neue',sans-serif">
                  MINTED
                </div>
              {/if}

              <!-- Badge coin SVG -->
              <div style="margin-bottom:16px;display:flex;justify-content:center">
                <img src={badgeSvg(badge.tier, badge.minted)} alt="{badge.tier} badge" width="100" height="100" style="filter:{badge.minted ? `drop-shadow(0 0 12px ${tierColor(badge.tier)}66)` : 'grayscale(0.3)'}"/>
              </div>

              <!-- Title -->
              <div style="font-family:'Bebas Neue',sans-serif;font-size:18px;color:{badge.minted || badge.eligible ? tierColor(badge.tier) : 'var(--muted)'};letter-spacing:1px;margin-bottom:4px">
                GPU MINER {badge.tier.toUpperCase()}
              </div>
              <div style="font-size:11px;color:var(--muted);margin-bottom:16px">
                {fmt(badge.required)} results required
              </div>

              <!-- Progress bar (if not eligible) -->
              {#if !badge.eligible}
                <div style="margin-bottom:12px">
                  <div style="background:var(--bg1);border-radius:999px;height:5px;overflow:hidden;margin-bottom:6px">
                    <div style="height:100%;width:{badge.progress}%;background:{tierColor(badge.tier)};border-radius:999px;transition:width .5s"></div>
                  </div>
                  <div style="font-size:10px;color:var(--muted)">{badge.progress}% · Need {fmt(badge.required - badgeData.submit_job_result)} more</div>
                </div>
              {/if}

              <!-- Action -->
              {#if badge.minted}
                <div style="margin-bottom:8px">
                  <span style="color:#00ff88;font-size:12px;font-weight:600">✅ ON-CHAIN</span>
                </div>
                <a href="https://explorer.vinjan-inc.com/republic-testnet/tx/{badge.tx_hash}"
                  target="_blank" rel="noopener"
                  style="color:var(--blue);font-size:11px;text-decoration:none">View TX ↗</a>
                {#if badge.minted_at}
                  <div style="font-size:10px;color:var(--muted);margin-top:4px">{new Date(badge.minted_at).toLocaleDateString()}</div>
                {/if}

              {:else if badge.eligible}
                {#if mintResults[badge.tier]?.success}
                  <div style="color:#00ff88;font-size:12px;font-weight:600;margin-bottom:6px">✅ Just Minted!</div>
                  <a href={mintResults[badge.tier].explorer} target="_blank" rel="noopener"
                    style="color:var(--blue);font-size:11px">View TX ↗</a>
                {:else}
                  {#if mintResults[badge.tier]?.reason}
                    <div style="color:#ff4444;font-size:10px;margin-bottom:8px;line-height:1.4">{mintResults[badge.tier].reason}</div>
                  {/if}
                  <button
                    on:click={() => mintBadge(badge.tier)}
                    disabled={mintingTier !== null}
                    style="background:{tierColor(badge.tier)};color:#000;border:none;padding:10px 28px;font-size:13px;font-family:'Bebas Neue',sans-serif;letter-spacing:1.5px;border-radius:8px;cursor:pointer;font-weight:700;width:100%;opacity:{mintingTier === badge.tier ? 0.6 : 1};transition:opacity .2s">
                    {mintingTier === badge.tier ? '⏳ MINTING...' : '⚡ MINT FREE'}
                  </button>
                {/if}

              {:else}
                <div style="background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:8px 12px;font-size:11px;color:var(--muted)">
                  🔒 Locked
                </div>
              {/if}

              <!-- TX hash -->
              {#if badge.minted && badge.tx_hash}
                <div style="margin-top:10px;background:var(--bg1);border-radius:6px;padding:6px 8px;font-size:9px;font-family:monospace;color:var(--muted);word-break:break-all;text-align:left">
                  {badge.tx_hash.slice(0,20)}...{badge.tx_hash.slice(-8)}
                </div>
              {/if}
            </div>
          {/each}
        </div>
      </div>

      <!-- Coming Soon -->
      <div style="margin-top:32px">
        <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:2px;margin-bottom:16px">Coming Soon</div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px">
          {#each [
            {name:'Validator Badge', icon:'🛡️', desc:'Run a validator node'},
            {name:'Project Badge', icon:'🚀', desc:'Deploy a project'},
            {name:'Ambassador Badge', icon:'📢', desc:'Community evangelist'},
            {name:'OG Badge', icon:'👑', desc:'Early testnet participant'},
          ] as b}
            <div style="background:var(--bg2);border:1px dashed var(--border);border-radius:14px;padding:20px 12px;text-align:center;opacity:0.4">
              <div style="font-size:32px;margin-bottom:8px">{b.icon}</div>
              <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:4px">{b.name}</div>
              <div style="font-size:10px;color:var(--muted)">{b.desc}</div>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  {/if}
</div>