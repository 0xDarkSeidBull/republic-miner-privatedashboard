<script>
  import { onMount, onDestroy } from 'svelte';
  import { API, fmt, currentPage } from '../../stores/app.js';

  let stats = null;
  let chainStatus = null;
  let loading = true;
  let interval;

  function navigate(page) {
    currentPage.set(page);
    window.history.pushState({}, '', '/' + page);
    window.scrollTo(0, 0);
  }

  async function loadData() {
    try {
      const [statsRes, chainRes] = await Promise.all([
        fetch(`${API}/api/network_stats`),
        fetch(`${API}/api/chain_status`)
      ]);
      stats = await statsRes.json();
      chainStatus = await chainRes.json();
    } catch(e) {
      console.error(e);
    }
    loading = false;
  }

  function fmt18(n) {
    if (!n) return '—';
    const val = Number(BigInt(n) / BigInt(10 ** 15)) / 1000;
    if (val >= 1e9) return (val / 1e9).toFixed(2) + 'B';
    if (val >= 1e6) return (val / 1e6).toFixed(2) + 'M';
    if (val >= 1e3) return (val / 1e3).toFixed(2) + 'K';
    return val.toFixed(2);
  }

  onMount(() => {
    loadData();
    interval = setInterval(loadData, 30000);
  });
  onDestroy(() => clearInterval(interval));
</script>

<div class="dashboard">
  <!-- Header -->
  <div class="page-header">
    <div class="header-left">
      <div class="page-title">
        <span class="title-icon">📊</span>
        <div>
          <h1>Network Dashboard</h1>
          <p class="subtitle">Real-time Republic blockchain statistics and analytics</p>
        </div>
      </div>
    </div>
    <div class="live-badge">
      <span class="live-dot"></span>
      Live Network
    </div>
  </div>

  {#if loading}
    <div class="loading-grid">
      {#each Array(8) as _}
        <div class="stat-card skeleton"></div>
      {/each}
    </div>
  {:else}
    <!-- Chain Info Row -->
    <div class="info-row">
      <div class="info-card">
        <div class="info-label">Network</div>
        <div class="info-value blue">Republic Testnet</div>
      </div>
      <div class="info-card">
        <div class="info-label">Cosmos Chain ID</div>
        <div class="info-value blue">raitestnet_77701-1</div>
      </div>
      <div class="info-card">
        <div class="info-label">EVM Chain ID</div>
        <div class="info-value orange">77701</div>
      </div>
      <div class="info-card">
        <div class="info-label">Token</div>
        <div class="info-value orange">RAI</div>
      </div>
    </div>

    <!-- Main Stats Grid -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-header">
          <span class="stat-label">LATEST BLOCK</span>
          <span class="stat-icon">⬡</span>
        </div>
        <div class="stat-value">{chainStatus?.latest_block?.toLocaleString() || '—'}</div>
      </div>

      <div class="stat-card">
        <div class="stat-header">
          <span class="stat-label">BLOCK AGE</span>
          <span class="stat-icon">⏱</span>
        </div>
        <div class="stat-value">{chainStatus?.block_age_seconds || '—'}<span class="stat-unit">s</span></div>
      </div>

      <div class="stat-card">
        <div class="stat-header">
          <span class="stat-label">TOTAL VALIDATORS</span>
          <span class="stat-icon">👥</span>
        </div>
        <div class="stat-value orange">{stats?.total_validators?.toLocaleString() || '—'}</div>
      </div>

      <div class="stat-card">
        <div class="stat-header">
          <span class="stat-label">ACTIVE VALIDATORS</span>
          <span class="stat-icon">✅</span>
        </div>
        <div class="stat-value green">{stats?.active_validators || '—'}</div>
      </div>

      <div class="stat-card">
        <div class="stat-header">
          <span class="stat-label">TOTAL SUPPLY</span>
          <span class="stat-icon">💰</span>
        </div>
        <div class="stat-value orange">{fmt18(stats?.total_supply)}<span class="stat-unit"> RAI</span></div>
      </div>

      <div class="stat-card">
        <div class="stat-header">
          <span class="stat-label">BONDED TOKENS</span>
          <span class="stat-icon">🔒</span>
        </div>
        <div class="stat-value">{fmt18(stats?.bonded_tokens)}<span class="stat-unit"> RAI</span></div>
      </div>

      <div class="stat-card">
        <div class="stat-header">
          <span class="stat-label">STAKING RATIO</span>
          <span class="stat-icon">📈</span>
        </div>
        <div class="stat-value">{stats?.staking_ratio || '—'}<span class="stat-unit">%</span></div>
      </div>

      <div class="stat-card">
        <div class="stat-header">
          <span class="stat-label">JAILED</span>
          <span class="stat-icon">⛓</span>
        </div>
        <div class="stat-value red">{stats?.jailed_validators || '—'}</div>
      </div>
    </div>

    <!-- Validator Status -->
    <div class="section">
      <div class="section-header">
        <h2>Validator Status</h2>
      </div>
      <div class="val-status-grid">
        <div class="val-status-card active" on:click={() => navigate('leaderboard')}>
          <div class="vs-number green">{stats?.active_validators || 0}</div>
          <div class="vs-label">Active</div>
          <div class="vs-bar" style="width:{(stats?.active_validators/stats?.total_validators*100)||0}%;background:#00ff88"></div>
        </div>
        <div class="val-status-card">
          <div class="vs-number muted">{stats?.inactive_validators || 0}</div>
          <div class="vs-label">Inactive</div>
          <div class="vs-bar" style="width:{(stats?.inactive_validators/stats?.total_validators*100)||0}%;background:#4a5280"></div>
        </div>
        <div class="val-status-card">
          <div class="vs-number red">{stats?.jailed_validators || 0}</div>
          <div class="vs-label">Jailed</div>
          <div class="vs-bar" style="width:{(stats?.jailed_validators/stats?.total_validators*100)||0}%;background:#ff2244"></div>
        </div>
      </div>
    </div>

    <!-- Quick Links -->
    <div class="section">
      <div class="section-header">
        <h2>Quick Access</h2>
      </div>
      <div class="quick-grid">
        {#each [
          { page: 'leaderboard', icon: '🏆', title: 'Leaderboard', desc: 'All miners ranked by score' },
          { page: 'weekly', icon: '📊', title: 'Weekly Points', desc: 'Current epoch standings' },
          { page: 'hyperscale', icon: '🤖', title: 'Hyperscale Jobs', desc: 'Submit AI inference on-chain' },
          { page: 'fastgpu', icon: '⚡', title: 'Fast GPU', desc: 'GPU compute leaderboard' },
          { page: 'submitjob', icon: '📤', title: 'Submit Job', desc: 'Submit mining job' },
          { page: 'ecosystem', icon: '🌐', title: 'Ecosystem', desc: 'Republic AI projects' },
        ] as item}
          <div class="quick-card" on:click={() => navigate(item.page)}>
            <div class="quick-icon">{item.icon}</div>
            <div>
              <div class="quick-title">{item.title}</div>
              <div class="quick-desc">{item.desc}</div>
            </div>
            <span class="quick-arrow">→</span>
          </div>
        {/each}
      </div>
    </div>

    <!-- Footer Stats -->
    <div class="footer-stats">
      <div class="footer-stat">
        <span class="fs-label">Network Status</span>
        <span class="fs-value"><span class="live-dot"></span> Live</span>
      </div>
      <div class="footer-stat">
        <span class="fs-label">Total Blocks</span>
        <span class="fs-value blue">{chainStatus?.latest_block?.toLocaleString() || '—'}</span>
      </div>
      <div class="footer-stat">
        <span class="fs-label">Active Set</span>
        <span class="fs-value orange">{stats?.active_validators || '—'}</span>
      </div>
      <div class="footer-stat">
        <span class="fs-label">Total Validators</span>
        <span class="fs-value">{stats?.total_validators || '—'}</span>
      </div>
    </div>
  {/if}
</div>

<style>
  .dashboard {
    padding: 32px;
    max-width: 1200px;
    min-height: 100vh;
  }

  /* Header */
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 28px;
    flex-wrap: wrap;
    gap: 12px;
  }
  .header-left { display: flex; align-items: center; gap: 16px; }
  .page-title { display: flex; align-items: center; gap: 14px; }
  .title-icon { font-size: 28px; }
  h1 {
    font-family: var(--font-display);
    font-size: 28px;
    letter-spacing: 2px;
    color: var(--text);
    margin: 0;
  }
  .subtitle { font-size: 13px; color: var(--muted); margin-top: 2px; }
  .live-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(0,255,136,0.08);
    border: 1px solid rgba(0,255,136,0.2);
    color: #00ff88;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1px;
  }
  .live-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #00ff88;
    animation: pulse 2s infinite;
    display: inline-block;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  /* Info Row */
  .info-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 16px;
  }
  .info-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 18px;
    text-align: center;
  }
  .info-label { font-size: 10px; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; }
  .info-value { font-family: var(--font-mono); font-size: 13px; font-weight: 700; }

  /* Stats Grid */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 28px;
  }
  .stat-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    transition: border-color 0.2s;
  }
  .stat-card:hover { border-color: rgba(255,60,0,0.3); }
  .stat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }
  .stat-label {
    font-size: 10px;
    color: var(--muted);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    font-family: var(--font-mono);
  }
  .stat-icon { font-size: 18px; opacity: 0.6; }
  .stat-value {
    font-family: var(--font-display);
    font-size: 28px;
    letter-spacing: 1px;
    color: var(--text);
    line-height: 1;
  }
  .stat-unit { font-size: 14px; color: var(--muted); }

  /* Colors */
  .orange { color: var(--accent3) !important; }
  .green { color: var(--green) !important; }
  .red { color: var(--red) !important; }
  .blue { color: var(--blue) !important; }
  .muted { color: var(--muted) !important; }

  /* Skeleton */
  .skeleton {
    background: linear-gradient(90deg, var(--bg2) 25%, var(--bg3) 50%, var(--bg2) 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    height: 100px;
  }
  @keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }
  .loading-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }

  /* Section */
  .section { margin-bottom: 28px; }
  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }
  .section-header h2 {
    font-family: var(--font-display);
    font-size: 18px;
    letter-spacing: 2px;
    color: var(--text);
  }

  /* Validator Status */
  .val-status-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }
  .val-status-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .val-status-card:hover { border-color: rgba(255,60,0,0.3); transform: translateY(-2px); }
  .vs-number {
    font-family: var(--font-display);
    font-size: 36px;
    letter-spacing: 1px;
    margin-bottom: 4px;
  }
  .vs-label { font-size: 12px; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 12px; }
  .vs-bar { height: 3px; border-radius: 3px; transition: width 1s ease; }

  /* Quick Links */
  .quick-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }
  .quick-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 20px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 14px;
    transition: all 0.2s;
  }
  .quick-card:hover { border-color: rgba(255,60,0,0.4); background: rgba(255,60,0,0.04); }
  .quick-icon { font-size: 24px; flex-shrink: 0; }
  .quick-title { font-size: 14px; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 2px; }
  .quick-desc { font-size: 11px; color: var(--muted); }
  .quick-arrow { margin-left: auto; color: var(--muted); font-size: 16px; }

  /* Footer Stats */
  .footer-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }
  .footer-stat { text-align: center; }
  .fs-label { display: block; font-size: 10px; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; }
  .fs-value {
    font-family: var(--font-display);
    font-size: 18px;
    letter-spacing: 1px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }

  @media (max-width: 1024px) {
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
    .info-row { grid-template-columns: repeat(2, 1fr); }
    .quick-grid { grid-template-columns: repeat(2, 1fr); }
    .footer-stats { grid-template-columns: repeat(2, 1fr); }
  }

  @media (max-width: 640px) {
    .dashboard { padding: 16px; }
    .stats-grid { grid-template-columns: 1fr 1fr; }
    .val-status-grid { grid-template-columns: 1fr; }
    .quick-grid { grid-template-columns: 1fr; }
    .footer-stats { grid-template-columns: repeat(2, 1fr); }
  }
</style>