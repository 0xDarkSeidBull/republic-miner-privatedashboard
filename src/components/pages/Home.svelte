<script>
  import { onMount, onDestroy } from 'svelte';
  import { API, fmt, shortAddr, rankClass, uptimeBadgeHtml, getSortVal, showToast, copyText, topScore, homeRawData, currentPage } from '../../stores/app.js';
  import MinerDetail from '../MinerDetail.svelte';

  let statsData = {};
  let homeSortKey = 'total';
  let sortedData = [];
  let activeDetailAddr = null;
  let searchAddr = '';
  let searchResult = null;
  let searchEstPoints = 0;
  let searchLoading = false;
  let searchError = '';
  let interval;
  let allTimePointsMap = {};

  // ── GEO POPUP ──
  let geoPopupOpen = false;
  let geoAddr = '';
  let geoLoading = false;
  let geoResult = null;
  let geoError = '';
  let geoAllData = [];
  let geoPopupEl;

  async function loadGeoData() {
    try {
      const r = await fetch(`${API}/api/weekly/geo`, { signal: AbortSignal.timeout(15000) });
      if (!r.ok) return;
      const d = await r.json();
      geoAllData = d.data || [];
    } catch(e) {}
  }

  function openGeoPopup() {
    geoPopupOpen = true;
    if (geoAllData.length === 0) loadGeoData();
  }

  function closeGeoPopup() {
    geoPopupOpen = false;
    geoResult = null;
    geoError = '';
  }

  function handlePopupKey(e) {
    if (e.key === 'Escape') closeGeoPopup();
  }

  async function searchGeo() {
    if (!geoAddr.trim()) return;
    geoLoading = true;
    geoResult = null;
    geoError = '';

    if (geoAllData.length === 0) await loadGeoData();

    const q = geoAddr.trim().toLowerCase();
    const miner = geoAllData.find(m =>
      (m.address || '').toLowerCase() === q ||
      (m.address || '').toLowerCase().includes(q) ||
      (m.moniker || '').toLowerCase() === q ||
      (m.moniker || '').toLowerCase().includes(q)
    );

    if (!miner) {
      geoError = 'Not found in this week\'s data.';
      geoLoading = false;
      return;
    }

    // Calculate 240K target
    const now = new Date();
    const utcDay = now.getUTCDay();
    const elapsedHours = utcDay * 24 + now.getUTCHours() + now.getUTCMinutes() / 60;
    const remainingHours = Math.max(0, 168 - elapsedHours);
    const efc = miner.effort_completed || 0;
    const sr = miner.success_rate || 0.8;
    const ratePerHour = elapsedHours > 0 ? efc / elapsedHours : 0;
    const projectedEfc = Math.round(efc + ratePerHour * remainingHours);

    const topMiner = geoAllData.reduce((best, m) => m.final_score > (best?.final_score || 0) ? m : best, null);
    const topFinal = topMiner?.final_score || 1;
    const multiplier = sr * (miner.jc || 1) * (miner.pres || 0.05) * (miner.steady || 1/7) * (miner.help || 1) * (miner.build || 1);
    const efcNeeded = multiplier > 0 ? Math.ceil(Math.pow(topFinal / multiplier, 2)) : 999999;
    const efcTarget = Math.max(5000, efcNeeded);
    const efcStillNeeded = Math.max(0, efcTarget - efc);
    const requiredRate = remainingHours > 0 ? Math.ceil(efcStillNeeded / remainingHours) : Infinity;
    const canReach = projectedEfc >= efcTarget;

    const projFinal = projectedEfc >= 5000
      ? Math.sqrt(projectedEfc) * sr * (miner.jc||1) * (miner.pres||0.05) * (miner.steady||1/7) * (miner.help||1) * (miner.build||1)
      : 0;
    const totalFinalSum = (geoAllData.reduce((s, m) => s + (m.final_score || 0), 0) - (miner.final_score || 0)) + projFinal;
    const projPoints = totalFinalSum > 0 ? Math.min(240000, Math.round((projFinal / totalFinalSum) * 1600000)) : 0;

    geoResult = {
      ...miner,
      elapsedHours: elapsedHours.toFixed(1),
      remainingHours: remainingHours.toFixed(1),
      ratePerHour: ratePerHour.toFixed(0),
      projectedEfc,
      efcTarget,
      efcStillNeeded,
      requiredRate: isFinite(requiredRate) ? requiredRate : '∞',
      canReach,
      projPoints,
      threshold5k: efc >= 5000,
    };
    geoLoading = false;
  }

  async function loadAllTimeMap() {
    try {
      const r = await fetch(`${API}/api/weekly`, { signal: AbortSignal.timeout(8000) });
      const wc = await r.json();
      const weeks = wc.available_weeks || [];
      const totals = {};
      for (const week of weeks) {
        const wr = await fetch(`${API}/api/weekly?week=${week}`, { signal: AbortSignal.timeout(8000) });
        const wd = await wr.json();
        for (const m of (wd.data || [])) {
          totals[m.address] = (totals[m.address] || 0) + m.estimated_points;
        }
      }
      allTimePointsMap = totals;
    } catch(e) {}
  }

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
      if (raw.length) topScore.set(raw[0].total || 0);
    } catch(e) { console.warn(e); }
  }

  $: {
    const data = $homeRawData;
    sortedData = [...data].sort((a, b) => getSortVal(b, homeSortKey) - getSortVal(a, homeSortKey));
  }

  function setSort(key) { homeSortKey = key; }
  function openDetail(addr) { activeDetailAddr = activeDetailAddr === addr ? null : addr; }

  async function searchMiner() {
    if (!searchAddr.trim()) return;
    searchLoading = true;
    searchResult = null;
    searchError = '';
    try {
      const r = await fetch(API + '/api/miner/' + encodeURIComponent(searchAddr.trim()), { signal: AbortSignal.timeout(8000) });
      if (!r.ok) throw new Error('Not found');
      searchResult = await r.json();
      try {
        const wr = await fetch(`${API}/api/weekly`, { signal: AbortSignal.timeout(8000) });
        const wc = await wr.json();
        const weeks = wc.available_weeks || [];
        let total = 0;
        for (const week of weeks) {
          const weekR = await fetch(`${API}/api/weekly?week=${week}`, { signal: AbortSignal.timeout(8000) });
          const weekD = await weekR.json();
          const miner = (weekD.data || []).find(m => m.address === searchResult.address);
          if (miner) total += miner.estimated_points;
        }
        searchEstPoints = total;
      } catch(e) { searchEstPoints = 0; }
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
    loadAllTimeMap();
    interval = setInterval(loadStats, 60000);
  });

  onDestroy(() => clearInterval(interval));

  $: statMiners = fmt(statsData.total_miners || statsData.miners || statsData.miner_count);
  $: statJobs = fmt(statsData.total_jobs || statsData.jobs);
  $: statSubmit = fmt(statsData.total_submit_job);
  $: statResult = fmt(statsData.total_submit_result);
  $: statBlock = fmt(statsData.last_scanned_height || statsData.height || statsData.block_height || statsData.latest_height);
  $: statScanTime = statsData.last_scan_time || statsData.scan_time || statsData.updated_at || '';
  $: topMiner = $homeRawData[0];
  $: searchPct = searchResult && $topScore > 0 ? Math.min(100, Math.round((searchResult.total / $topScore) * 100)) : 0;
</script>

<!-- GEO POPUP TRIGGER BUTTON (floating) -->
<button
  on:click={openGeoPopup}
  style="position:fixed;bottom:28px;right:28px;z-index:999;background:linear-gradient(135deg,var(--accent),var(--accent3));border:none;border-radius:50px;padding:12px 20px;color:#000;font-weight:800;font-size:12px;letter-spacing:.08em;cursor:pointer;box-shadow:0 4px 24px rgba(255,170,0,.4);display:flex;align-items:center;gap:8px"
>
  🎯 My Geo Score
</button>

<!-- GEO POPUP MODAL -->
{#if geoPopupOpen}
  <!-- Backdrop -->
  <div
    style="position:fixed;inset:0;z-index:1000;background:rgba(0,0,0,.7);backdrop-filter:blur(4px)"
    on:click={closeGeoPopup}
    on:keydown={handlePopupKey}
    role="button"
    tabindex="-1"
  ></div>

  <!-- Popup -->
  <div
    bind:this={geoPopupEl}
    style="position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:1001;width:min(560px,95vw);background:var(--bg2);border:1px solid var(--border);border-radius:16px;padding:24px;box-shadow:0 20px 60px rgba(0,0,0,.6)"
  >
    <!-- Header -->
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px">
      <div>
        <div style="font-size:11px;color:var(--accent);font-weight:700;letter-spacing:.1em;text-transform:uppercase">Weekly Geo Points</div>
        <div style="font-size:18px;font-weight:800;color:var(--text);margin-top:2px">🎯 Your Score & 240K Tracker</div>
      </div>
      <button
        on:click={closeGeoPopup}
        style="background:var(--bg1);border:1px solid var(--border);border-radius:8px;width:32px;height:32px;color:var(--muted);cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center"
      >✕</button>
    </div>

    <!-- Search -->
    <div style="display:flex;gap:8px;margin-bottom:14px">
      <input
        style="flex:1;background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:10px 14px;color:var(--text);font-size:13px;outline:none"
        placeholder="rai1... or raivaloper1... or moniker"
        bind:value={geoAddr}
        on:keypress={e => e.key === 'Enter' && searchGeo()}
      />
      <button
        on:click={searchGeo}
        disabled={geoLoading}
        style="background:linear-gradient(135deg,var(--accent),var(--accent3));border:none;border-radius:8px;padding:10px 16px;color:#000;font-weight:700;font-size:12px;letter-spacing:.06em;cursor:pointer;white-space:nowrap"
      >{geoLoading ? '...' : 'SEARCH'}</button>
    </div>

    {#if geoError}
      <div style="font-size:13px;color:var(--accent);padding:10px 12px;background:rgba(255,170,0,.08);border-radius:8px;border:1px solid rgba(255,170,0,.2)">{geoError}</div>
    {:else if geoResult}
      {@const r = geoResult}

      <!-- Miner Header -->
      <div style="display:flex;align-items:center;gap:12px;padding:12px 14px;background:var(--bg1);border:1px solid var(--border);border-radius:10px;margin-bottom:12px">
        <div style="font-size:22px;font-weight:900;color:{r.rank===1 ? '#FFD700' : r.rank===2 ? '#C0C0C0' : r.rank===3 ? '#CD7F32' : 'var(--muted)'};min-width:44px">#{r.rank}</div>
        <div style="flex:1;min-width:0">
          <div style="font-weight:700;font-size:15px;color:var(--text)">{r.moniker || '—'}</div>
          <div style="font-size:11px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{r.address}</div>
        </div>
        <div style="text-align:right">
          <div style="font-size:18px;font-weight:800;color:{r.capped ? 'var(--accent)' : 'var(--accent3)'}">{fmt(Math.round(r.estimated_rai))}</div>
          <div style="font-size:10px;color:var(--muted)">Est. POINTS {r.capped ? '🔒' : ''}</div>
        </div>
      </div>

      <!-- Score Grid -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px">
        {#each [['EfC', fmt(r.effort_completed), ''], ['JC', r.jc?.toFixed(3), 'var(--blue)'], ['Eff', r.eff?.toFixed(2), 'var(--accent)'], ['Pres', r.pres?.toFixed(4), ''], ['Steady', r.steady?.toFixed(4), ''], ['Help', r.help?.toFixed(4), ''], ['Build', r.build?.toFixed(4), 'var(--accent3)'], ['Final', r.final_score?.toFixed(4), 'var(--accent)']] as [label, val, color]}
          <div style="background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:8px 10px;text-align:center">
            <div style="font-size:9px;color:var(--muted);text-transform:uppercase;margin-bottom:3px">{label}</div>
            <div style="font-size:12px;font-weight:700;color:{color || 'var(--text)'}">{val}</div>
          </div>
        {/each}
      </div>

      <!-- 240K Calculator -->
      <div style="background:var(--bg1);border:1px solid var(--border);border-radius:10px;padding:14px;margin-bottom:10px">
        <div style="font-size:10px;font-weight:700;color:var(--accent);letter-spacing:.08em;text-transform:uppercase;margin-bottom:10px">🎯 240K Target Calculator</div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:10px">
          <div style="text-align:center">
            <div style="font-size:9px;color:var(--muted);text-transform:uppercase">Rate/hr</div>
            <div style="font-size:14px;font-weight:700;color:var(--text)">{r.ratePerHour}</div>
          </div>
          <div style="text-align:center">
            <div style="font-size:9px;color:var(--muted);text-transform:uppercase">Hrs Left</div>
            <div style="font-size:14px;font-weight:700;color:var(--accent3)">{r.remainingHours}h</div>
          </div>
          <div style="text-align:center">
            <div style="font-size:9px;color:var(--muted);text-transform:uppercase">Proj. EfC</div>
            <div style="font-size:14px;font-weight:700;color:var(--text)">{fmt(r.projectedEfc)}</div>
          </div>
        </div>

        {#if !r.threshold5k}
          <div style="font-size:12px;padding:8px 10px;border-radius:6px;background:rgba(255,170,0,.08);border:1px solid rgba(255,170,0,.2);color:var(--accent);margin-bottom:8px">
            ⚠️ Need <strong>{fmt(5000 - r.effort_completed)}</strong> more EfC to activate scoring (min 5,000)
          </div>
        {/if}

        <div style="padding:10px 12px;border-radius:8px;border:1px solid {r.canReach ? 'rgba(0,255,170,.3)' : 'rgba(255,170,0,.3)'};background:{r.canReach ? 'rgba(0,255,170,.06)' : 'rgba(255,170,0,.06)'}">
          {#if r.canReach}
            <div style="font-size:12px;font-weight:700;color:var(--accent3)">✅ On track for 240K at current rate!</div>
          {:else}
            <div style="font-size:12px;font-weight:700;color:var(--accent)">⚡ Need <strong>{fmt(r.efcStillNeeded)}</strong> more EfC</div>
            <div style="font-size:11px;color:var(--muted);margin-top:4px">Required: <strong style="color:var(--text)">{r.requiredRate} jobs/hr</strong> · Current: <strong style="color:var(--text)">{r.ratePerHour} jobs/hr</strong></div>
          {/if}
          <div style="font-size:11px;color:var(--muted);margin-top:4px">Est. Points at week end: <strong style="color:var(--accent3)">{fmt(r.projPoints)}</strong></div>
        </div>
      </div>

      <!-- Weekly Points Page Link -->
      <button
        on:click={() => { closeGeoPopup(); currentPage.set('weekly'); }}
        style="width:100%;background:transparent;border:1px solid var(--border);border-radius:8px;padding:10px;color:var(--muted);font-size:12px;cursor:pointer;text-align:center"
      >View full leaderboard → Weekly Points</button>

    {:else if !geoLoading}
      <div style="text-align:center;padding:20px 0;font-size:13px;color:var(--muted)">
        Enter your wallet or validator address to see your weekly geo score and 240K target.
      </div>
    {/if}
  </div>
{/if}

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
        <div class="miner-stat"><div class="miner-stat-label">Est. Points</div><div class="miner-stat-value" style="background:linear-gradient(135deg,var(--accent),var(--accent3));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">{fmt(allTimePointsMap[searchResult.address] || 0)}</div></div>
      </div>
      <div class="progress-bar-wrap">
        <div class="progress-bar-label"><span>VS TOP MINER</span><span>{searchPct}%</span></div>
        <div class="progress-bar-track"><div class="progress-bar-fill" style="width:{searchPct}%"></div></div>
      </div>
      <!-- Geo Score Quick Button -->
      <button
        class="share-btn"
        style="background:rgba(255,170,0,.1);border-color:rgba(255,170,0,.3);color:var(--accent)"
        on:click={() => { geoAddr = m.address; openGeoPopup(); setTimeout(searchGeo, 300); }}
      >🎯 See Weekly Geo Score</button>
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
        <th style="text-align:right">Est. Points</th>
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
              <td class="num-cell" style="color:var(--accent3)">{fmt(allTimePointsMap[m.address] || 0)}</td>
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