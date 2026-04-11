<script>
  import { onMount, onDestroy } from 'svelte';
  import { API, fmt } from '../../stores/app.js';

  let data = null;
  let loading = true;
  let activeTab = 'active';
  let selectedValidator = null;
  let searchQuery = '';
  let interval;

  async function loadData() {
    try {
      const r = await fetch(`${API}/api/validators_all`);
      data = await r.json();
    } catch(e) { console.error(e); }
    loading = false;
  }

  function fmtRai(tokens_rai) {
    if (!tokens_rai) return '—';
    if (tokens_rai >= 1e6) return (tokens_rai / 1e6).toFixed(2) + 'M';
    if (tokens_rai >= 1e3) return (tokens_rai / 1e3).toFixed(2) + 'K';
    return tokens_rai.toFixed(2);
  }

  $: currentList = data ? (data[activeTab] || []).filter(v =>
    v.moniker.toLowerCase().includes(searchQuery.toLowerCase()) ||
    v.operator_address.toLowerCase().includes(searchQuery.toLowerCase())
  ) : [];

  $: totalTokens = data ? (data[activeTab] || []).reduce((s, v) => s + v.tokens_rai, 0) : 0;

  onMount(() => { loadData(); interval = setInterval(loadData, 60000); });
  onDestroy(() => clearInterval(interval));
</script>

<div class="validators-page">
  <!-- Header -->
  <div class="page-header">
    <div class="header-left">
      <h1>⚡ Validator Explorer</h1>
      <p class="subtitle">Browse all Republic blockchain validators</p>
    </div>
    {#if data}
      <div class="counts-row">
        <div class="count-badge green" on:click={() => { activeTab = 'active'; selectedValidator = null; }}>
          ✅ Active: {data.counts.active}
        </div>
        <div class="count-badge muted" on:click={() => { activeTab = 'inactive'; selectedValidator = null; }}>
          ⏸ Inactive: {data.counts.inactive}
        </div>
        <div class="count-badge red" on:click={() => { activeTab = 'jailed'; selectedValidator = null; }}>
          ⛓ Jailed: {data.counts.jailed}
        </div>
      </div>
    {/if}
  </div>

  {#if loading}
    <div class="loading">Loading validators...</div>
  {:else if selectedValidator}
    <!-- Validator Detail -->
    <div class="detail-view">
      <button class="back-btn" on:click={() => selectedValidator = null}>← Back to Validators</button>

      <div class="detail-card">
        <div class="detail-header">
          <div class="detail-avatar">{selectedValidator.moniker.slice(0,2).toUpperCase()}</div>
          <div class="detail-info">
            <h2>{selectedValidator.moniker}</h2>
            {#if selectedValidator.website}
              <a href={selectedValidator.website} target="_blank" rel="noopener" class="val-website">{selectedValidator.website}</a>
            {/if}
            <div class="detail-status {selectedValidator.status}">
              {selectedValidator.status === 'active' ? '✅ Active' : selectedValidator.status === 'jailed' ? '⛓ Jailed' : '⏸ Inactive'}
            </div>
          </div>
        </div>

        <div class="detail-stats-grid">
          <div class="detail-stat">
            <div class="ds-label">VOTING POWER</div>
            <div class="ds-value orange">{fmtRai(selectedValidator.tokens_rai)} RAI</div>
          </div>
          <div class="detail-stat">
            <div class="ds-label">COMMISSION</div>
            <div class="ds-value">{selectedValidator.commission}%</div>
          </div>
          <div class="detail-stat">
            <div class="ds-label">STATUS</div>
            <div class="ds-value {selectedValidator.status === 'active' ? 'green' : selectedValidator.status === 'jailed' ? 'red' : 'muted'}">
              {selectedValidator.status.toUpperCase()}
            </div>
          </div>
          <div class="detail-stat">
            <div class="ds-label">JAILED</div>
            <div class="ds-value {selectedValidator.jailed ? 'red' : 'green'}">{selectedValidator.jailed ? 'YES' : 'NO'}</div>
          </div>
        </div>

        <div class="detail-address">
          <div class="addr-label">OPERATOR ADDRESS</div>
          <div class="addr-value">{selectedValidator.operator_address}</div>
        </div>

        {#if selectedValidator.identity}
          <div class="detail-address">
            <div class="addr-label">IDENTITY</div>
            <div class="addr-value">{selectedValidator.identity}</div>
          </div>
        {/if}

        <!-- Voting power bar -->
        <div class="power-bar-section">
          <div class="ds-label">VOTING POWER SHARE</div>
          <div class="power-bar-bg">
            <div class="power-bar-fill" style="width:{Math.min((selectedValidator.tokens_rai / totalTokens * 100), 100).toFixed(2)}%"></div>
          </div>
          <div class="power-pct">{(selectedValidator.tokens_rai / totalTokens * 100).toFixed(2)}% of total bonded</div>
        </div>
      </div>
    </div>
  {:else}
    <!-- Tabs -->
    <div class="tabs">
      <button class="tab {activeTab === 'active' ? 'active' : ''}" on:click={() => activeTab = 'active'}>
        Active ({data?.counts.active || 0})
      </button>
      <button class="tab {activeTab === 'inactive' ? 'active' : ''}" on:click={() => activeTab = 'inactive'}>
        Inactive ({data?.counts.inactive || 0})
      </button>
      <button class="tab {activeTab === 'jailed' ? 'active' : ''}" on:click={() => activeTab = 'jailed'}>
        Jailed ({data?.counts.jailed || 0})
      </button>
    </div>

    <!-- Search -->
    <div class="search-bar">
      <span class="search-icon">🔍</span>
      <input
        bind:value={searchQuery}
        placeholder="Search validators by name or address..."
        class="search-input"
      />
    </div>

    <!-- Table -->
    <div class="val-table">
      <div class="table-header">
        <span class="th">#</span>
        <span class="th">Validator</span>
        <span class="th right">Voting Power</span>
        <span class="th right">VP %</span>
        <span class="th right">Commission</span>
        <span class="th center">Status</span>
      </div>

      {#each currentList as val, i}
        <div class="table-row" on:click={() => selectedValidator = val}>
          <span class="td rank">{i + 1}</span>
          <span class="td validator-cell">
            <div class="val-avatar">{val.moniker.slice(0,2).toUpperCase()}</div>
            <div class="val-info">
              <div class="val-moniker">{val.moniker}</div>
              <div class="val-addr">{val.operator_address.slice(0,20)}...{val.operator_address.slice(-6)}</div>
            </div>
          </span>
          <span class="td right orange">{fmtRai(val.tokens_rai)} RAI</span>
          <span class="td right muted">{(val.tokens_rai / totalTokens * 100).toFixed(1)}%</span>
          <span class="td right">{val.commission}%</span>
          <span class="td center">
            <span class="status-badge {val.status}">
              {val.status === 'active' ? '✅' : val.status === 'jailed' ? '⛓' : '⏸'}
              {val.status}
            </span>
          </span>
        </div>
      {/each}

      {#if currentList.length === 0}
        <div class="empty">No validators found</div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .validators-page { padding: 32px; max-width: 1200px; }

  .page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 28px;
    flex-wrap: wrap;
    gap: 16px;
  }
  h1 { font-family: var(--font-display); font-size: 28px; letter-spacing: 2px; margin: 0; }
  .subtitle { font-size: 13px; color: var(--muted); margin-top: 4px; }

  .counts-row { display: flex; gap: 10px; flex-wrap: wrap; }
  .count-badge {
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 0.2s;
  }
  .count-badge.green { background: rgba(0,255,136,0.08); border-color: rgba(0,255,136,0.2); color: #00ff88; }
  .count-badge.muted { background: rgba(74,82,128,0.15); border-color: rgba(74,82,128,0.3); color: var(--muted); }
  .count-badge.red { background: rgba(255,34,68,0.08); border-color: rgba(255,34,68,0.2); color: var(--red); }
  .count-badge:hover { transform: translateY(-1px); }

  .loading { text-align: center; padding: 60px; color: var(--muted); font-family: var(--font-mono); }

  /* Tabs */
  .tabs { display: flex; gap: 4px; margin-bottom: 20px; border-bottom: 1px solid var(--border); }
  .tab {
    background: none;
    border: none;
    padding: 10px 20px;
    font-family: var(--font-body);
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1px;
    color: var(--muted);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    transition: all 0.2s;
    text-transform: uppercase;
  }
  .tab:hover { color: var(--text); }
  .tab.active { color: var(--accent); border-bottom-color: var(--accent); }

  /* Search */
  .search-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 16px;
    margin-bottom: 16px;
  }
  .search-icon { font-size: 16px; }
  .search-input {
    background: none;
    border: none;
    color: var(--text);
    font-family: var(--font-mono);
    font-size: 13px;
    outline: none;
    width: 100%;
  }
  .search-input::placeholder { color: var(--muted); }

  /* Table */
  .val-table { background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
  .table-header {
    display: grid;
    grid-template-columns: 50px 1fr 140px 80px 100px 100px;
    padding: 12px 20px;
    background: rgba(255,60,0,0.05);
    border-bottom: 1px solid var(--border);
  }
  .th {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--muted);
    letter-spacing: 1.5px;
    text-transform: uppercase;
  }
  .th.right { text-align: right; }
  .th.center { text-align: center; }

  .table-row {
    display: grid;
    grid-template-columns: 50px 1fr 140px 80px 100px 100px;
    padding: 14px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    cursor: pointer;
    transition: background 0.15s;
    align-items: center;
  }
  .table-row:hover { background: rgba(255,60,0,0.04); }
  .table-row:last-child { border-bottom: none; }

  .td { font-size: 13px; }
  .td.right { text-align: right; }
  .td.center { text-align: center; }
  .td.rank { color: var(--muted); font-family: var(--font-mono); font-size: 12px; }

  .validator-cell { display: flex; align-items: center; gap: 12px; }
  .val-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: rgba(255,60,0,0.15);
    border: 1px solid rgba(255,60,0,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-display);
    font-size: 13px;
    color: var(--accent);
    flex-shrink: 0;
  }
  .val-moniker { font-size: 14px; font-weight: 600; }
  .val-addr { font-family: var(--font-mono); font-size: 10px; color: var(--muted); margin-top: 2px; }

  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .status-badge.active { background: rgba(0,255,136,0.1); color: #00ff88; }
  .status-badge.inactive { background: rgba(74,82,128,0.2); color: var(--muted); }
  .status-badge.jailed { background: rgba(255,34,68,0.1); color: var(--red); }

  .empty { text-align: center; padding: 40px; color: var(--muted); font-family: var(--font-mono); }

  /* Colors */
  .orange { color: var(--accent3); }
  .green { color: var(--green); }
  .red { color: var(--red); }
  .muted { color: var(--muted); }

  /* Detail View */
  .back-btn {
    background: none;
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 8px 16px;
    border-radius: 8px;
    cursor: pointer;
    font-family: var(--font-mono);
    font-size: 12px;
    margin-bottom: 20px;
    transition: all 0.2s;
  }
  .back-btn:hover { color: var(--text); border-color: var(--accent); }

  .detail-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 28px;
  }
  .detail-header {
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 28px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border);
  }
  .detail-avatar {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: rgba(255,60,0,0.15);
    border: 2px solid rgba(255,60,0,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-display);
    font-size: 22px;
    color: var(--accent);
    flex-shrink: 0;
  }
  .detail-info h2 { font-family: var(--font-display); font-size: 24px; letter-spacing: 2px; margin: 0 0 4px; }
  .val-website { font-size: 12px; color: var(--blue); text-decoration: none; }
  .val-website:hover { text-decoration: underline; }
  .detail-status {
    display: inline-block;
    margin-top: 8px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
  }
  .detail-status.active { background: rgba(0,255,136,0.1); color: #00ff88; }
  .detail-status.inactive { background: rgba(74,82,128,0.2); color: var(--muted); }
  .detail-status.jailed { background: rgba(255,34,68,0.1); color: var(--red); }

  .detail-stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 20px;
  }
  .detail-stat {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
  }
  .ds-label { font-family: var(--font-mono); font-size: 10px; color: var(--muted); letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 8px; }
  .ds-value { font-family: var(--font-display); font-size: 22px; letter-spacing: 1px; }

  .detail-address {
    background: rgba(255,255,255,0.02);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 12px;
  }
  .addr-label { font-family: var(--font-mono); font-size: 10px; color: var(--muted); letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 6px; }
  .addr-value { font-family: var(--font-mono); font-size: 12px; color: var(--accent3); word-break: break-all; }

  .power-bar-section { margin-top: 16px; }
  .power-bar-bg { background: rgba(255,255,255,0.05); border-radius: 4px; height: 8px; margin: 8px 0; overflow: hidden; }
  .power-bar-fill { height: 100%; background: var(--accent); border-radius: 4px; transition: width 1s ease; }
  .power-pct { font-family: var(--font-mono); font-size: 11px; color: var(--muted); }

  @media (max-width: 768px) {
    .validators-page { padding: 16px; }
    .table-header, .table-row { grid-template-columns: 40px 1fr 100px 80px; }
    .th:nth-child(5), .th:nth-child(6), .td:nth-child(5), .td:nth-child(6) { display: none; }
    .detail-stats-grid { grid-template-columns: repeat(2, 1fr); }
  }
</style>