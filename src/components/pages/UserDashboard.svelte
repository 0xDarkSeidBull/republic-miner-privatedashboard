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

  function tierBg(tier) {
    if (tier === 'Gold') return 'rgba(255,215,0,0.08)';
    if (tier === 'Silver') return 'rgba(192,192,192,0.08)';
    return 'rgba(205,127,50,0.08)';
  }

  function tierBorder(tier) {
    if (tier === 'Gold') return 'rgba(255,215,0,0.3)';
    if (tier === 'Silver') return 'rgba(192,192,192,0.3)';
    return 'rgba(205,127,50,0.3)';
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

<div style="max-width:900px;margin:0 auto;padding:0 28px 60px">

  {#if !keplrConnected}
    <div style="text-align:center;padding:60px 20px">
      <div style="font-size:64px;margin-bottom:20px">🔗</div>
      <h2 style="font-size:28px;font-family:'Bebas Neue',sans-serif;color:var(--accent);margin-bottom:12px">
        CONNECT WALLET TO CHECK YOUR STATS
      </h2>
      <p style="color:var(--muted);font-size:14px;margin-bottom:32px">
        Connect your Keplr wallet to view your GPU mining stats and mint your achievement badges
      </p>
      <button
        on:click={connectKeplr}
        disabled={connecting}
        style="background:var(--accent);color:#000;border:none;padding:16px 40px;font-size:16px;font-family:'Bebas Neue',sans-serif;letter-spacing:2px;border-radius:8px;cursor:pointer;font-weight:700">
        {connecting ? 'CONNECTING...' : '⚡ CONNECT KEPLR'}
      </button>
      {#if error}
        <div class="error-msg" style="margin-top:16px">{error}</div>
      {/if}
    </div>

  {:else}
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

      <div style="margin-top:28px">
        <div style="font-size:13px;color:var(--muted);margin-bottom:16px;text-transform:uppercase;letter-spacing:1px">Achievement Badges</div>
        <div style="display:flex;flex-direction:column;gap:16px">
          {#each badgeData.badges as badge}
            <div style="background:{tierBg(badge.tier)};border:1px solid {tierBorder(badge.tier)};border-radius:16px;padding:24px">
              <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
                <div style="display:flex;align-items:center;gap:16px">
                  <div style="font-size:48px">{badge.emoji}</div>
                  <div>
                    <div style="font-family:'Bebas Neue',sans-serif;font-size:22px;color:{tierColor(badge.tier)}">
                      GPU MINER {badge.tier.toUpperCase()} BADGE
                    </div>
                    <div style="font-size:12px;color:var(--muted);margin-top:2px">
                      Required: <span style="color:{tierColor(badge.tier)}">{fmt(badge.required)} results</span>
                    </div>
                    {#if badge.minted}
                      <div style="font-size:11px;color:var(--muted);margin-top:4px">
                        Minted {new Date(badge.minted_at).toLocaleDateString()}
                      </div>
                    {/if}
                  </div>
                </div>

                <div style="text-align:right">
                  {#if badge.minted}
                    <div style="color:#00ff64;font-size:13px;font-weight:600;margin-bottom:6px">✅ MINTED</div>
                    <a href="https://explorer.vinjan-inc.com/republic-testnet/tx/{badge.tx_hash}"
                      target="_blank" rel="noopener"
                      style="color:var(--blue);font-size:11px">
                      View TX ↗
                    </a>
                  {:else if badge.eligible}
                    {#if mintResults[badge.tier]?.success}
                      <div style="color:#00ff64;font-size:12px;margin-bottom:6px">✅ Just Minted!</div>
                      <a href={mintResults[badge.tier].explorer} target="_blank" rel="noopener"
                        style="color:var(--blue);font-size:11px">View TX ↗</a>
                    {:else}
                      {#if mintResults[badge.tier]?.reason}
                        <div style="color:#ff4444;font-size:11px;margin-bottom:6px;max-width:200px">{mintResults[badge.tier].reason}</div>
                      {/if}
                      <button
                        on:click={() => mintBadge(badge.tier)}
                        disabled={mintingTier !== null}
                        style="background:{tierColor(badge.tier)};color:#000;border:none;padding:10px 24px;font-size:14px;font-family:'Bebas Neue',sans-serif;letter-spacing:1px;border-radius:8px;cursor:pointer;font-weight:700;opacity:{mintingTier === badge.tier ? 0.7 : 1}">
                        {mintingTier === badge.tier ? '⏳ MINTING...' : '⚡ MINT'}
                      </button>
                    {/if}
                  {:else}
                    <div style="font-size:12px;color:var(--muted);margin-bottom:8px">
                      Need {fmt(badge.required - badgeData.submit_job_result)} more
                    </div>
                    <div style="background:var(--bg1);border-radius:999px;height:6px;width:120px;overflow:hidden">
                      <div style="height:100%;width:{badge.progress}%;background:{tierColor(badge.tier)};border-radius:999px"></div>
                    </div>
                    <div style="font-size:10px;color:var(--muted);margin-top:4px">{badge.progress}%</div>
                  {/if}
                </div>
              </div>

              {#if badge.minted && badge.tx_hash}
                <div style="margin-top:12px;background:var(--bg1);border-radius:8px;padding:8px 12px;font-size:10px;font-family:monospace;color:var(--muted);word-break:break-all">
                  TX: {badge.tx_hash}
                </div>
              {/if}
            </div>
          {/each}
        </div>
      </div>

      <div style="margin-top:32px">
        <div style="font-size:13px;color:var(--muted);margin-bottom:12px;text-transform:uppercase;letter-spacing:1px">Coming Soon</div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px">
          {#each [
            {name:'Validator Badge', icon:'🛡️', desc:'Run a validator node'},
            {name:'Project Badge', icon:'🚀', desc:'Deploy a project'},
            {name:'Ambassador Badge', icon:'📢', desc:'Community evangelist'},
            {name:'OG Badge', icon:'👑', desc:'Early testnet participant'},
          ] as b}
            <div style="background:var(--bg2);border:1px dashed var(--border);border-radius:10px;padding:16px;text-align:center;opacity:0.5">
              <div style="font-size:28px;margin-bottom:6px">{b.icon}</div>
              <div style="font-size:11px;font-weight:600;color:var(--muted)">{b.name}</div>
              <div style="font-size:10px;color:var(--muted);margin-top:4px">{b.desc}</div>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  {/if}
</div>