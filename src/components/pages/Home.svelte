<script>
  import { onMount, onDestroy } from 'svelte';
  import { API, fmt, shortAddr, rankClass, uptimeBadgeHtml, getSortVal, showToast, copyText, topScore, homeRawData, currentPage } from '../stores/app.js';
  import MinerDetail from '../components/MinerDetail.svelte';

  let statsData = {};
  let homeSortKey = 'total';
  let sortedData = [];
  let activeDetailAddr = null;
  let searchAddr = '';
  let searchResult = null;
  let searchLoading = false;
  let searchError = '';
  let interval;

  async function loadStats() {
    try {
      const r = await fetch(API + '/api/stats', { signal: AbortSignal.timeout(8000) });
      statsData = await r.json();
    } catch(e) { console.warn(e); }
  }

  async function loadTopMiners() {
    try {
      const r = await fetch(API + '/api/leaderboard?limit=10', { signal: AbortSignal.timeout(8000) });
      const d = await r.json();
      const raw = d.data || d;
      homeRawData.set(raw);
      if (raw.length) {
        topScore.set(raw[0].total || 0);
      }
    } catch(e) { console.warn(e); }
  }

  $: {
    const data = $homeRawData;
    sortedData = [...data].sort((a, b) => getSortVal(b, homeSortKey) - getSortVal(a, homeSortKey));
  }

  function setSort(key) { homeSortKey = key; }

  function openDetail(addr) {
    activeDetailAddr = activeDetailAddr === addr ? null : addr;
  }

  async function searchMiner() {
    if (!searchAddr.trim()) return;
    searchLoading = true;
    searchResult = null;
    searchError = '';
    try {
      const r = await fetch(API + '/api/miner/' + encodeURIComponent(searchAddr.trim()), { signal: AbortSignal.timeout(8000) });
      if (!r.ok) throw new Error('Not found');
      searchResult = await r.json();
    } catch {
      searchError = 'Miner not found. Check address and try again.';
    }
    searchLoading = false;
  }

  async function triggerRefresh() {
    showToast('🔄 Chain scan triggered...');
    try {
      const r = await fetch(`${API}/api/refresh`, { method: 'POST' });
      const d = await r.json();
      if (d.status === 'ok' || d.status === 'scanning') {
        showToast('✅ Scan started! Updating in ~30s');
        setTimeout(() => { loadTopMiners(); loadStats(); showToast('✅ Data updated!'); }, 30000);
      } else { showToast('⚠️ ' + (d.message || 'Refresh queued')); }
    } catch { showToast('❌ Refresh failed'); }
  }

  async function downloadCsv(address) {
    showToast('⏳ Fetching your jobs...');
    try {
      const r = await fetch(`${API}/api/miner/${encodeURIComponent(address)}/jobs.csv`);
      if (!r.ok) throw new Error();
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = `jobs_${address.slice(0,10)}.csv`; a.click();
      URL.revokeObjectURL(url);
      showToast('✅ CSV downloaded!');
    } catch { showToast('❌ Download failed'); }
  }

  function prefillPoints(address, moniker) {
    currentPage.set('points');
    setTimeout(() => {
      const w = document.getElementById('pf-wallet'), m = document.getElementById('pf-moniker');
      if (w) w.value = address;
      if (m) m.value = moniker || '';
      w?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 150);
  }

  onMount(() => {
    loadStats();
    loadTopMiners();
    interval = setInterval(loadStats, 60000);
  });

  onDestroy(() => clearInterval(interval));

  $: statMiners = fmt(statsData.total_miners || statsData.miners || statsData.miner_count);
  $: statJobs = fmt(statsData.total_jobs || statsData.jobs);
  $: statSubmit = fmt(statsData.submit_job || statsData.total_submit || statsData.submit_jobs || statsData.totalSubmitJob);
  $: statResult = fmt(statsData.submit_job_result || statsData.total_result || statsData.submit_results || statsData.totalSubmitResult);
  $: statBlock = fmt(statsData.last_scanned_height || statsData.height || statsData.block_height || statsData.latest_height);
  $: statScanTime = statsData.last_scan_time || statsData.scan_time || statsData.updated_at || '';
  $: topMiner = $homeRawData[0];
  $: searchPct = searchResult && $topScore > 0 ? Math.min(100, Math.round((searchResult.total / $topScore) * 100)) : 0;
</script>

<!-- HERO -->
<div class="hero">
  <div class="hero-bg"></div>
  <div style="position:relative;z-index:1">
    <div class="hero-eyebrow"><span class="hero-eyebrow-dot"></span>Republic AI Testnet · Live</div>
    <h1><span class="line1">GPU MINER</span><span class="line2">DASHBOARD</span></h1>
    <p class="hero-sub">Track miner activity, explore the leaderboard, and discover projects building on Republic AI.</p>
  </div>
</div>

<!-- STATS GRID -->
<div class="stats-grid">
  <div class="stat-card"><div class="stat-label">Total Miners</div><div class="stat-value fire">{statMiners}</div></div>
  <div class="stat-card"><div class="stat-label">Total Jobs</div><div class="stat-value">{statJobs}</div></div>
  <div class="stat-card"><div class="stat-label">Submit Job</div><div class="stat-value">{statSubmit}</div></div>
  <div class="stat-card"><div class="stat-label">Submit Result</div><div class="stat-value">{statResult}</div></div>
  <div class="stat-card"><div class="stat-label">Last Block</div><div class="stat-value">{statBlock}</div><div class="stat-sub">{statScanTime}</div></div>
  <div class="stat-card">
    <div class="stat-label">Top Miner</div>
    <div class="stat-value fire" style="font-size:20px">{topMiner ? (topMiner.moniker || shortAddr(topMiner.address)) : '—'}</div>
    {#if topMiner}<div class="stat-sub">{fmt(topMiner.total)} pts</div>{/if}
  </div>
</div>

<!-- SEARCH -->
<div class="search-section">
  <div class="search-label">Search Miner by Address</div>
  <div class="search-box">
    <input class="search-input" placeholder="rai1..." bind:value={searchAddr} on:keypress={e => e.key === 'Enter' && searchMiner()}/>
    <button class="btn-search" on:click={searchMiner}>SEARCH</button>
  </div>

  {#if searchLoading}
    <div class="loading">Searching...</div>
  {:else if searchError}
    <div class="error-msg">{searchError}</div>
  {:else if searchResult}
    {@const m = searchResult}
    <div class="miner-card">
      <div class="miner-card-header">
        <div class="miner-rank-badge">#{m.rank || '—'}</div>
        <div>
          <div class="miner-name">{m.moniker || shortAddr(m.address)}</div>
          <div class="miner-addr"><span>{m.address}</span><button class="copy-btn" on:click={() => copyText(m.address)}>⎘</button></div>
          <div class="miner-badges" style="margin-top:6px">
            {@html uptimeBadgeHtml(m.uptime)}
            {#if m.moniker}<span class="uptime-badge uptime-unknown" style="color:var(--blue);border-color:rgba(0,204,255,.3)">{m.moniker}</span>{/if}
          </div>
        </div>
      </div>
      <div class="miner-stats">
        <div class="miner-stat"><div class="miner-stat-label">Submit</div><div class="miner-stat-value">{fmt(m.submit_job)}</div></div>
        <div class="miner-stat"><div class="miner-stat-label">Result</div><div class="miner-stat-value">{fmt(m.submit_job_result)}</div></div>
        <div class="miner-stat"><div class="miner-stat-label">Total</div><div class="miner-stat-value" style="background:linear-gradient(135deg,var(--accent),var(--accent3));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">{fmt(m.total)}</div></div>
      </div>
      <div class="progress-bar-wrap">
        <div class="progress-bar-label"><span>VS TOP MINER</span><span>{searchPct}%</span></div>
        <div class="progress-bar-track"><div class="progress-bar-fill" style="width:{searchPct}%"></div></div>
      </div>
      <button class="share-btn" on:click={() => window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(`🏆 My RepublicAI GPU Mining Stats:\n📊 Rank: #${m.rank}\n⛏️ ${m.moniker ? 'Moniker: '+m.moniker+'\n' : ''}Total: ${fmt(m.total)} pts\n🔗 republicstats.xyz`)}`, '_blank')}>𝕏 Share on X</button>
      <button class="share-btn fire" on:click={() => downloadCsv(m.address)}>⬇️ Download All Jobs (CSV)</button>
    </div>
  {/if}
</div>

<!-- TOP MINERS TABLE -->
<div class="section">
  <div class="section-header">
    <div class="section-title"><div class="section-title-bar"></div>Top Miners</div>
    <button class="refresh-btn" on:click={triggerRefresh}>↻ Refresh</button>
  </div>
  <div class="sort-bar">
    {#each [['total','Total Pts'],['submit','Submit'],['result','Result'],['uptime','Uptime']] as [key, label]}
      <button class="sort-btn {homeSortKey === key ? 'active' : ''}" on:click={() => setSort(key)}>{label}</button>
    {/each}
  </div>
  <div class="table-wrap">
    <table>
      <thead><tr>
        <th>Rank</th><th>Moniker / Address</th>
        <th style="text-align:right">Submit</th><th style="text-align:right">Result</th>
        <th style="text-align:right">Uptime</th><th style="text-align:right">Total</th>
        <th style="text-align:center">Action</th>
      </tr></thead>
      <tbody>
        {#if sortedData.length === 0}
          <tr><td colspan="7" class="loading">Loading stats...</td></tr>
        {:else}
          {#each sortedData as m, i}
            <tr class="clickable-row {activeDetailAddr === m.address ? 'row-selected' : ''}" on:click={() => openDetail(m.address)}>
              <td class="rank-cell {rankClass(m.rank)}">#{ m.rank || i+1 }</td>
              <td>
                <div class="moniker-cell {!m.moniker ? 'empty' : ''}">{m.moniker || '—'}</div>
                <div class="addr-cell" style="margin-top:3px"><span class="addr-text">{m.address || ''}</span></div>
              </td>
              <td class="num-cell">{fmt(m.submit_job)}</td>
              <td class="num-cell">{fmt(m.submit_job_result)}</td>
              <td class="num-cell">{@html uptimeBadgeHtml(m.uptime)}</td>
              <td class="num-cell" style="color:var(--accent);font-size:14px">{fmt(m.total)}</td>
              <td style="text-align:center">
                <button
                  on:click|stopPropagation={() => prefillPoints(m.address, m.moniker || '')}
                  style="background:rgba(255,60,0,.1);border:1px solid rgba(255,60,0,.3);color:var(--accent);padding:5px 12px;cursor:pointer;font-family:var(--font-body);font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;transition:all .2s">
                  Submit
                </button>
              </td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>
</div>

<!-- DETAIL PANEL -->
{#if activeDetailAddr}
  <div style="margin:0 28px 40px;max-width:1224px;margin-left:auto;margin-right:auto">
    <MinerDetail
      addr={activeDetailAddr}
      page="home"
      cachedData={$homeRawData.find(m => m.address === activeDetailAddr) || {}}
      onClose={() => { activeDetailAddr = null; }}
    />
  </div>
{/if}
