<script>
  import { onMount } from 'svelte';
  import { API, fmt, shortAddr } from '../../stores/app.js';

  let walletAddress = '';
  let keplrConnected = false;
  let connecting = false;
  let statsLoading = false;
  let mintLoading = false;
  let badgeStatus = null;
  let error = '';
  let mintSuccess = null;
  let mintError = '';

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
      await fetchBadgeStatus();
    } catch(e) {
      error = 'Failed to connect Keplr: ' + e.message;
    }
    connecting = false;
  }

  async function fetchBadgeStatus() {
    if (!walletAddress) return;
    statsLoading = true;
    try {
      const r = await fetch(`${API}/api/badge/status/${walletAddress}`, {
        signal: AbortSignal.timeout(10000)
      });
      badgeStatus = await r.json();
    } catch(e) {
      error = 'Failed to fetch stats.';
    }
    statsLoading = false;
  }

  async function mintBadge() {
    mintLoading = true;
    mintError = '';
    mintSuccess = null;
    try {
      if (!window.keplr) throw new Error('Keplr not found');

      const CHAIN_ID = 'raitestnet_77701-1';
      const TREASURY = badgeStatus.treasury;
      const AMOUNT = '10000000000000000000'; // 10 RAI

      await window.keplr.enable(CHAIN_ID);
      const offlineSigner = window.keplr.getOfflineSigner(CHAIN_ID);
      const accounts = await offlineSigner.getAccounts();

      // Use keplr to send TX
      const { SigningStargateClient } = await import('https://cdn.jsdelivr.net/npm/@cosmjs/stargate@0.32.4/+esm');
      const { GasPrice } = await import('https://cdn.jsdelivr.net/npm/@cosmjs/stargate@0.32.4/+esm');

      const client = await SigningStargateClient.connectWithSigner(
        'https://rpc-test.republic.vinjan-inc.com',
        offlineSigner,
        { gasPrice: GasPrice.fromString('25000000000arai') }
      );

      const result = await client.sendTokens(
        accounts[0].address,
        TREASURY,
        [{ denom: 'arai', amount: AMOUNT }],
        'auto',
        'Republic AI GPU Miner Badge Mint'
      );

      if (result.code !== 0) throw new Error('TX failed: ' + result.rawLog);

      // Verify with backend
      const verifyRes = await fetch(`${API}/api/badge/verify-mint`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address: walletAddress, tx_hash: result.transactionHash })
      });
      const verifyData = await verifyRes.json();

      if (verifyData.success) {
        mintSuccess = verifyData;
        await fetchBadgeStatus();
      } else {
        mintError = verifyData.reason;
      }
    } catch(e) {
      mintError = 'Mint failed: ' + e.message;
    }
    mintLoading = false;
  }

  function disconnect() {
    walletAddress = '';
    keplrConnected = false;
    badgeStatus = null;
    mintSuccess = null;
    error = '';
  }

  function tierColor(tier) {
    if (tier === 'Gold') return '#FFD700';
    if (tier === 'Silver') return '#C0C0C0';
    return '#CD7F32';
  }

  function tierEmoji(tier) {
    if (tier === 'Gold') return '🥇';
    if (tier === 'Silver') return '🥈';
    return '🥉';
  }
</script>

<!-- HERO -->
<div class="hero">
  <div class="hero-bg"></div>
  <div style="position:relative;z-index:1">
    <div class="hero-eyebrow"><span class="hero-eyebrow-dot"></span>Republic AI · User Dashboard</div>
    <h1><span class="line1">YOUR</span><span class="line2">DASHBOARD</span></h1>
    <p class="hero-sub">Connect your Keplr wallet to view your GPU stats and mint your badge</p>
  </div>
</div>

<div style="max-width:900px;margin:0 auto;padding:0 28px 60px">

  {#if !keplrConnected}
    <!-- Connect Section -->
    <div style="text-align:center;padding:60px 20px">
      <div style="font-size:64px;margin-bottom:20px">🔗</div>
      <h2 style="font-size:28px;font-family:'Bebas Neue',sans-serif;color:var(--accent);margin-bottom:12px">
        CONNECT WALLET TO CHECK YOUR STATS
      </h2>
      <p style="color:var(--muted);font-size:14px;margin-bottom:32px">
        Connect your Keplr wallet to view your GPU mining stats and mint your achievement badge
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
    <!-- Connected -->
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

    {:else if badgeStatus}
      <!-- Stats Cards -->
      <div class="stats-grid" style="margin-top:0">
        <div class="stat-card">
          <div class="stat-label">Submit Results</div>
          <div class="stat-value fire">{fmt(badgeStatus.submit_job_result)}</div>
          <div class="stat-sub">GPU Jobs Completed</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Submit Jobs</div>
          <div class="stat-value">{fmt(badgeStatus.submit_job)}</div>
          <div class="stat-sub">Jobs Submitted</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Eligibility</div>
          <div class="stat-value" style="color:{badgeStatus.eligible ? 'var(--accent3)' : 'var(--muted)'}">
            {badgeStatus.eligible ? '✅ ELIGIBLE' : '❌ NOT YET'}
          </div>
          <div class="stat-sub">10,000 results needed</div>
        </div>
        {#if badgeStatus.eligible}
          <div class="stat-card">
            <div class="stat-label">Badge Tier</div>
            <div class="stat-value" style="color:{tierColor(badgeStatus.tier)}">
              {tierEmoji(badgeStatus.tier)} {badgeStatus.tier}
            </div>
            <div class="stat-sub">
              {badgeStatus.tier === 'Bronze' ? '10K+ results' : badgeStatus.tier === 'Silver' ? '25K+ results' : '50K+ results'}
            </div>
          </div>
        {/if}
      </div>

      <!-- Badge Section -->
      <div style="background:var(--bg2);border:1px solid var(--border);border-radius:16px;padding:32px;margin-top:24px;text-align:center">

        {#if badgeStatus.minted}
          <!-- Already Minted -->
          <div style="font-size:72px;margin-bottom:16px">
            {tierEmoji(badgeStatus.badge.tier)}
          </div>
          <h3 style="font-family:'Bebas Neue',sans-serif;font-size:28px;color:{tierColor(badgeStatus.badge.tier)};margin-bottom:8px">
            GPU MINER {badgeStatus.badge.tier.toUpperCase()} BADGE
          </h3>
          <p style="color:var(--muted);font-size:13px;margin-bottom:16px">
            Minted on {new Date(badgeStatus.badge.minted_at).toLocaleDateString()}
          </p>
          <div style="background:var(--bg1);border-radius:8px;padding:12px;font-size:11px;font-family:monospace;color:var(--accent3);word-break:break-all">
            TX: {badgeStatus.badge.tx_hash}
          </div>

        {:else if badgeStatus.eligible}
          <!-- Eligible - Mint Now -->
          <div style="font-size:64px;margin-bottom:16px">🏅</div>
          <h3 style="font-family:'Bebas Neue',sans-serif;font-size:28px;color:var(--accent);margin-bottom:8px">
            MINT YOUR {badgeStatus.tier.toUpperCase()} BADGE
          </h3>
          <p style="color:var(--muted);font-size:13px;margin-bottom:8px">
            You have <span style="color:var(--accent)">{fmt(badgeStatus.submit_job_result)}</span> completed jobs — eligible for GPU Miner Badge!
          </p>
          <p style="color:var(--muted);font-size:12px;margin-bottom:24px">
            Mint fee: <span style="color:var(--accent3)">10 RAI</span> — Non-transferable SBT Badge
          </p>

          {#if mintSuccess}
            <div style="background:rgba(0,255,100,0.1);border:1px solid rgba(0,255,100,0.3);border-radius:8px;padding:16px;margin-bottom:16px">
              <div style="color:#00ff64;font-weight:600;margin-bottom:4px">✅ Badge Minted Successfully!</div>
              <div style="font-size:12px;color:var(--muted)">Tier: {mintSuccess.tier} | TX: {mintSuccess.tx_hash?.slice(0,20)}...</div>
            </div>
          {/if}

          {#if mintError}
            <div class="error-msg" style="margin-bottom:16px">{mintError}</div>
          {/if}

          <button
            on:click={mintBadge}
            disabled={mintLoading}
            style="background:var(--accent);color:#000;border:none;padding:16px 48px;font-size:18px;font-family:'Bebas Neue',sans-serif;letter-spacing:2px;border-radius:8px;cursor:pointer;font-weight:700;opacity:{mintLoading ? 0.7 : 1}">
            {mintLoading ? '⏳ MINTING...' : '⚡ MINT BADGE — 10 RAI'}
          </button>

        {:else}
          <!-- Not Eligible -->
          <div style="font-size:64px;margin-bottom:16px">⛏️</div>
          <h3 style="font-family:'Bebas Neue',sans-serif;font-size:24px;color:var(--muted);margin-bottom:8px">
            KEEP MINING!
          </h3>
          <p style="color:var(--muted);font-size:13px;margin-bottom:16px">
            You need <span style="color:var(--accent)">{fmt(10000 - badgeStatus.submit_job_result)}</span> more completed jobs to qualify
          </p>
          <div style="background:var(--bg1);border-radius:999px;height:10px;overflow:hidden;max-width:400px;margin:0 auto">
            <div style="height:100%;width:{Math.min(100, (badgeStatus.submit_job_result/10000)*100).toFixed(1)}%;background:linear-gradient(90deg,var(--accent),var(--accent3));border-radius:999px;transition:width 1s"></div>
          </div>
          <div style="font-size:12px;color:var(--muted);margin-top:8px">
            {Math.min(100, ((badgeStatus.submit_job_result/10000)*100)).toFixed(1)}% complete
          </div>
        {/if}
      </div>

      <!-- Future Badges -->
      <div style="margin-top:24px">
        <div style="font-size:13px;color:var(--muted);margin-bottom:12px;text-transform:uppercase;letter-spacing:1px">Coming Soon</div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px">
          {#each [
            {name:'Validator Badge', icon:'🛡️', desc:'Run a validator node'},
            {name:'Project Badge', icon:'🚀', desc:'Deploy a project'},
            {name:'Ambassador Badge', icon:'📢', desc:'Community evangelist'},
            {name:'OG Badge', icon:'👑', desc:'Early testnet participant'},
          ] as badge}
            <div style="background:var(--bg2);border:1px dashed var(--border);border-radius:10px;padding:16px;text-align:center;opacity:0.5">
              <div style="font-size:28px;margin-bottom:6px">{badge.icon}</div>
              <div style="font-size:11px;font-weight:600;color:var(--muted)">{badge.name}</div>
              <div style="font-size:10px;color:var(--muted);margin-top:4px">{badge.desc}</div>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  {/if}
</div>
