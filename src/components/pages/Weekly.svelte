<script>
  import { onMount, onDestroy } from 'svelte';
  import { API, fmt, shortAddr } from '../../stores/app.js';

  let geoData = [];
  let geoLoading = false;
  let geoError = '';
  let geoMeta = {};
  let lastUpdated = '';
  let weekProgress = 0;
  let interval;

  // ── SEARCH / FILTER / SORT ──
  let searchQuery = '';
  let sortKey = 'rank';
  let sortAsc = true;
  let showOnlyScored = false;

  // ── 240K CALCULATOR ──
  let calcAddr = '';
  let calcResult = null;
  let showCalc = false;

  // ── FETCH ──
  async function loadGeo() {
    geoLoading = true;
    geoError = '';
    try {
      fetch(`${API}/api/weekly/geo/refresh`, { method: 'POST' }).catch(() => {});
      await new Promise(r => setTimeout(r, 30000));
      const r = await fetch(`${API}/api/weekly/geo`, { signal: AbortSignal.timeout(15000) });
      if (!r.ok) throw new Error('Failed');
      const d = await r.json();
      geoData = d.data || [];
      geoMeta = { week: d.week, total_jobs: d.total_jobs, miners: d.miners, pool: d.pool };
      lastUpdated = new Date().toLocaleTimeString();
      calcWeekProgress();
    } catch(e) {
      geoError = 'Failed to load. Retrying...';
    }
    geoLoading = false;
  }

  async function quickLoad() {
    // Just fetch cached data without triggering scan
    try {
      const r = await fetch(`${API}/api/weekly/geo`, { signal: AbortSignal.timeout(15000) });
      if (!r.ok) return;
      const d = await r.json();
      geoData = d.data || [];
      geoMeta = { week: d.week, total_jobs: d.total_jobs, miners: d.miners, pool: d.pool };
      lastUpdated = new Date().toLocaleTimeString();
      calcWeekProgress();
    } catch(e) {}
  }

  function calcWeekProgress() {
    const now = new Date();
    const day = now.getUTCDay();
    const elapsed = day * 24 * 60 + now.getUTCHours() * 60 + now.getUTCMinutes();
    weekProgress = Math.min(100, Math.round((elapsed / (7 * 24 * 60)) * 100));
  }

  // ── SORT / FILTER LOGIC ──
  function setSort(key) {
    if (sortKey === key) sortAsc = !sortAsc;
    else { sortKey = key; sortAsc = key === 'rank'; }
  }

  $: filtered = geoData
    .filter(m => {
      if (showOnlyScored && m.final_score === 0) return false;
      if (!searchQuery.trim()) return true;
      const q = searchQuery.trim().toLowerCase();
      return (m.address || '').toLowerCase().includes(q) ||
             (m.moniker || '').toLowerCase().includes(q);
    })
    .sort((a, b) => {
      let av = a[sortKey], bv = b[sortKey];
      if (sortKey === 'moniker') { av = (av || '').toLowerCase(); bv = (bv || '').toLowerCase(); }
      if (av === undefined) av = 0;
      if (bv === undefined) bv = 0;
      return sortAsc ? (av > bv ? 1 : -1) : (av < bv ? 1 : -1);
    });

  // ── 240K CALCULATOR ──
  function calc240k(addr) {
    const miner = geoData.find(m =>
      m.address === addr || m.address === addr.trim() ||
      (m.moniker || '').toLowerCase() === addr.trim().toLowerCase()
    );
    if (!miner) { calcResult = { error: 'Address not found in current week data' }; return; }

    const now = new Date();
    const utcDay = now.getUTCDay(); // 0=Sun
    const utcHour = now.getUTCHours();
    const utcMin = now.getUTCMinutes();

    const elapsedHours = utcDay * 24 + utcHour + utcMin / 60;
    const totalHours = 7 * 24; // 168
    const remainingHours = Math.max(0, totalHours - elapsedHours);

    const efc = miner.effort_completed || 0;
    const sr = miner.success_rate || 0.8;
    const pres = miner.pres || 0;
    const steady = miner.steady || (1/7);
    const help = miner.help || 1.0;
    const build = miner.build || 1.0;
    const jc = miner.jc || 1.0;

    const ratePerHour = elapsedHours > 0 ? efc / elapsedHours : 0;
    const projectedEfc = efc + ratePerHour * remainingHours;

    // What EfC needed to match top scorer (dipy.me or whoever has highest final)
    // 240K target: need to be top or close to cap
    // Geo formula: final = sqrt(efc)*sr * jc * pres * steady * help * build
    // For 240K we need final > current top final OR be top scorer
    const topMiner = geoData.reduce((best, m) => m.final_score > (best?.final_score || 0) ? m : best, null);
    const topFinal = topMiner?.final_score || 1;

    // Solve for EfC: sqrt(efc) * sr * jc * pres * steady * help * build = topFinal
    // sqrt(efc) = topFinal / (sr * jc * pres * steady * help * build)
    // efc = (topFinal / (sr * jc * pres * steady * help * build))^2
    const multiplier = sr * jc * (pres > 0 ? pres : 0.05) * (steady > 0 ? steady : 1/7) * help * build;
    const efcNeeded = multiplier > 0 ? Math.ceil(Math.pow(topFinal / multiplier, 2)) : 999999;
    const efcNeeded5k = Math.max(5000, efcNeeded); // at minimum need 5K

    const efcStillNeeded = Math.max(0, efcNeeded5k - efc);
    const requiredRate = remainingHours > 0 ? efcStillNeeded / remainingHours : Infinity;
    const canReach = projectedEfc >= efcNeeded5k;

    // Points at current rate
    const projFinal = projectedEfc >= 5000
      ? Math.sqrt(projectedEfc) * sr * jc * (pres || 0.05) * (steady || 1/7) * help * build
      : 0;
    const totalFinalSum = (geoData.reduce((s, m) => s + (m.final_score || 0), 0) - (miner.final_score || 0)) + projFinal;
    const projPoints = totalFinalSum > 0 ? Math.min(240000, Math.round((projFinal / totalFinalSum) * 1600000)) : 0;

    calcResult = {
      miner,
      efc,
      sr,
      elapsedHours: elapsedHours.toFixed(1),
      remainingHours: remainingHours.toFixed(1),
      ratePerHour: ratePerHour.toFixed(0),
      projectedEfc: Math.round(projectedEfc),
      efcNeeded: efcNeeded5k,
      efcStillNeeded,
      requiredRate: isFinite(requiredRate) ? requiredRate.toFixed(0) : '∞',
      canReach,
      projPoints,
      threshold5k: efc >= 5000,
    };
  }

  function runCalc() {
    if (!calcAddr.trim()) return;
    calc240k(calcAddr.trim());
    showCalc = true;
  }

  onMount(() => {
    quickLoad();
    calcWeekProgress();
    interval = setInterval(quickLoad, 5 * 60 * 1000);
  });
  onDestroy(() => clearInterval(interval));

  const colMap = {
    rank: 'rank', effort_completed: 'EfC', jc: 'JC', eff: 'Eff',
    pres: 'Pres', steady: 'Steady', help: 'Help', build: 'Build',
    final_score: 'Final', estimated_rai: 'Points'
  };
</script>

<!-- HERO -->
<div class="hero">
  <div class="hero-bg"></div>
  <div style="position:relative;z-index:1">
    <div class="hero-eyebrow"><span class="hero-eyebrow-dot"></span>Republic AI · Weekly Points</div>
    <h1><span class="line1">WEEKLY GPU</span><span class="line2">MINER POINTS</span></h1>
    <p class="hero-sub">Live GPU miner scores — Sunday 00:00 UTC to Saturday 23:59 UTC</p>
  </div>
</div>

<!-- WEEK PROGRESS -->
<div style="max-width:1224px;margin:0 auto;padding:0 28px 24px">
  <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:20px 24px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
      <div style="font-size:13px;color:var(--muted)">
        📅 {geoMeta.week || 'Current Week'} &nbsp;·&nbsp; Pool: <span style="color:var(--accent)">1,600,000 POINTS</span>
      </div>
      <div style="font-size:12px;color:var(--muted)">Week Progress: <span style="color:var(--accent3)">{weekProgress}%</span></div>
    </div>
    <div style="background:var(--bg1);border-radius:999px;height:8px;overflow:hidden">
      <div style="height:100%;width:{weekProgress}%;background:linear-gradient(90deg,var(--accent),var(--accent3));border-radius:999px;transition:width 1s"></div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:6px;font-size:11px;color:var(--muted)">
      <span>Sun 00:00 UTC</span>
      <span>Sat 23:59 UTC</span>
    </div>
  </div>
</div>

<!-- STATS CARDS -->
<div class="stats-grid" style="margin-top:0">
  <div class="stat-card">
    <div class="stat-label">Total Miners</div>
    <div class="stat-value fire">{geoMeta.miners || '—'}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Total Jobs</div>
    <div class="stat-value">{fmt(geoMeta.total_jobs || 0)}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Reward Pool</div>
    <div class="stat-value" style="color:var(--accent)">1.6M POINTS</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Max Per Wallet</div>
    <div class="stat-value" style="color:var(--accent3)">240K POINTS</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Last Updated</div>
    <div class="stat-value" style="font-size:16px">{lastUpdated || '—'}</div>
    <div class="stat-sub">Auto-refresh 5 min</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Capped Wallets</div>
    <div class="stat-value fire">{geoData.filter(m => m.capped).length}</div>
    <div class="stat-sub">240K POINTS max hit</div>
  </div>
</div>

<!-- 240K CALCULATOR -->
<div style="max-width:1224px;margin:0 auto;padding:0 28px 24px">
  <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:20px 24px">
    <div style="font-size:13px;font-weight:700;color:var(--accent);margin-bottom:12px;letter-spacing:.05em">🎯 240K POINTS CALCULATOR</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap">
      <input
        style="flex:1;min-width:220px;background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:10px 14px;color:var(--text);font-size:13px;outline:none"
        placeholder="Enter rai1... or raivaloper1... or moniker"
        bind:value={calcAddr}
        on:keypress={e => e.key === 'Enter' && runCalc()}
      />
      <button
        style="background:linear-gradient(135deg,var(--accent),var(--accent3));border:none;border-radius:8px;padding:10px 20px;color:#000;font-weight:700;font-size:12px;letter-spacing:.08em;cursor:pointer"
        on:click={runCalc}
      >CALCULATE</button>
    </div>

    {#if showCalc && calcResult}
      {#if calcResult.error}
        <div style="margin-top:14px;color:var(--accent);font-size:13px">⚠️ {calcResult.error}</div>
      {:else}
        {@const r = calcResult}
        <div style="margin-top:16px;display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px">
          <div style="background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:12px 14px">
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:4px">Current EfC</div>
            <div style="font-size:18px;font-weight:700;color:var(--accent)">{fmt(r.efc)}</div>
          </div>
          <div style="background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:12px 14px">
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:4px">Rate / Hour</div>
            <div style="font-size:18px;font-weight:700;color:var(--text)">{r.ratePerHour} jobs/hr</div>
          </div>
          <div style="background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:12px 14px">
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:4px">Time Elapsed</div>
            <div style="font-size:18px;font-weight:700;color:var(--text)">{r.elapsedHours}h</div>
          </div>
          <div style="background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:12px 14px">
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:4px">Time Remaining</div>
            <div style="font-size:18px;font-weight:700;color:var(--accent3)">{r.remainingHours}h</div>
          </div>
          <div style="background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:12px 14px">
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:4px">5K Threshold</div>
            <div style="font-size:18px;font-weight:700;color:{r.threshold5k ? 'var(--accent3)' : 'var(--accent)'}">{r.threshold5k ? '✅ Passed' : `Need ${fmt(5000 - r.efc)} more`}</div>
          </div>
          <div style="background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:12px 14px">
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:4px">EfC Needed (240K)</div>
            <div style="font-size:18px;font-weight:700;color:var(--text)">{fmt(r.efcNeeded)}</div>
          </div>
          <div style="background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:12px 14px">
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:4px">Still Needed</div>
            <div style="font-size:18px;font-weight:700;color:var(--accent)">{fmt(r.efcStillNeeded)}</div>
          </div>
          <div style="background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:12px 14px">
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:4px">Required Rate</div>
            <div style="font-size:18px;font-weight:700;color:{r.canReach ? 'var(--accent3)' : 'var(--accent)'}">{r.requiredRate} jobs/hr</div>
          </div>
        </div>

        <!-- Summary -->
        <div style="margin-top:14px;padding:14px 16px;border-radius:8px;border:1px solid {r.canReach ? 'rgba(0,255,170,.3)' : 'rgba(255,170,0,.3)'};background:{r.canReach ? 'rgba(0,255,170,.05)' : 'rgba(255,170,0,.05)'}">
          {#if r.canReach}
            <div style="font-size:13px;color:var(--accent3);font-weight:600">✅ At current rate you'll reach 240K this week!</div>
            <div style="font-size:12px;color:var(--muted);margin-top:4px">Projected EfC by week end: <strong style="color:var(--text)">{fmt(r.projectedEfc)}</strong> · Est. Points: <strong style="color:var(--accent3)">{fmt(r.projPoints)}</strong></div>
          {:else}
            <div style="font-size:13px;color:var(--accent);font-weight:600">⚡ Speed up! You need {r.requiredRate} jobs/hr to reach 240K</div>
            <div style="font-size:12px;color:var(--muted);margin-top:4px">At current rate ({r.ratePerHour}/hr) projected EfC: <strong style="color:var(--text)">{fmt(r.projectedEfc)}</strong> → Est. Points: <strong style="color:var(--accent3)">{fmt(r.projPoints)}</strong></div>
            {#if !r.threshold5k}
              <div style="font-size:12px;color:var(--accent);margin-top:6px">⚠️ First reach 5,000 EfC to activate Eff score — below that Final = 0!</div>
            {/if}
          {/if}
        </div>
      {/if}
    {/if}
  </div>
</div>

<!-- SEARCH + FILTER BAR -->
<div style="max-width:1224px;margin:0 auto;padding:0 28px 16px">
  <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">
    <!-- Search -->
    <div style="flex:1;min-width:220px;display:flex;gap:8px">
      <input
        style="flex:1;background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:9px 14px;color:var(--text);font-size:13px;outline:none"
        placeholder="🔍 Search address or moniker..."
        bind:value={searchQuery}
      />
      {#if searchQuery}
        <button
          style="background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:9px 12px;color:var(--muted);cursor:pointer;font-size:13px"
          on:click={() => searchQuery = ''}
        >✕</button>
      {/if}
    </div>
    <!-- Filter -->
    <label style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted);cursor:pointer;white-space:nowrap">
      <input type="checkbox" bind:checked={showOnlyScored} style="accent-color:var(--accent)" />
      Only scored (Final &gt; 0)
    </label>
    <!-- Refresh -->
    <button class="refresh-btn" on:click={loadGeo} disabled={geoLoading}>
      {geoLoading ? '⏳ Scanning...' : '↻ Refresh'}
    </button>
  </div>
  {#if searchQuery && filtered.length === 0}
    <div style="margin-top:10px;font-size:13px;color:var(--muted)">No miners found for "<strong style="color:var(--text)">{searchQuery}</strong>"</div>
  {:else if searchQuery}
    <div style="margin-top:8px;font-size:12px;color:var(--muted)">{filtered.length} result{filtered.length !== 1 ? 's' : ''} found</div>
  {/if}
</div>

<!-- TABLE -->
<div class="section" style="padding-top:0">
  <div class="section-header">
    <div class="section-title">
      <div class="section-title-bar"></div>
      Live Scores
      {#if filtered.length !== geoData.length}
        <span style="font-size:12px;color:var(--muted);font-weight:400;margin-left:8px">({filtered.length} of {geoData.length})</span>
      {/if}
    </div>
    <!-- Sort buttons -->
    <div style="display:flex;gap:6px;flex-wrap:wrap">
      {#each [['rank','Rank'],['effort_completed','EfC'],['final_score','Final'],['estimated_rai','Points'],['pres','Pres'],['steady','Steady'],['build','Build']] as [key, label]}
        <button
          style="padding:5px 10px;border-radius:6px;font-size:11px;font-weight:600;letter-spacing:.04em;cursor:pointer;border:1px solid {sortKey===key ? 'var(--accent)' : 'var(--border)'};background:{sortKey===key ? 'rgba(255,170,0,.12)' : 'var(--bg2)'};color:{sortKey===key ? 'var(--accent)' : 'var(--muted)'}"
          on:click={() => setSort(key)}
        >{label} {sortKey===key ? (sortAsc ? '↑' : '↓') : ''}</button>
      {/each}
    </div>
  </div>

  {#if geoLoading && geoData.length === 0}
    <div class="loading" style="padding:60px;text-align:center">Calculating scores... (~30s)</div>
  {:else if geoError}
    <div class="error-msg" style="margin:20px">{geoError}</div>
  {:else}
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th style="cursor:pointer" on:click={() => setSort('rank')}>Rank {sortKey==='rank' ? (sortAsc?'↑':'↓') : ''}</th>
            <th style="cursor:pointer" on:click={() => setSort('moniker')}>Miner {sortKey==='moniker' ? (sortAsc?'↑':'↓') : ''}</th>
            <th style="text-align:right;cursor:pointer" title="Effort Completed" on:click={() => setSort('effort_completed')}>EfC {sortKey==='effort_completed' ? (sortAsc?'↑':'↓') : ''}</th>
            <th style="text-align:right;cursor:pointer" title="Job Creation Score" on:click={() => setSort('jc')}>JC {sortKey==='jc' ? (sortAsc?'↑':'↓') : ''}</th>
            <th style="text-align:right;cursor:pointer" title="Effort Score" on:click={() => setSort('eff')}>Eff {sortKey==='eff' ? (sortAsc?'↑':'↓') : ''}</th>
            <th style="text-align:right;cursor:pointer" title="Presence Score" on:click={() => setSort('pres')}>Pres {sortKey==='pres' ? (sortAsc?'↑':'↓') : ''}</th>
            <th style="text-align:right;cursor:pointer" title="Steadiness Score" on:click={() => setSort('steady')}>Steady {sortKey==='steady' ? (sortAsc?'↑':'↓') : ''}</th>
            <th style="text-align:right;cursor:pointer" title="Helpfulness Score" on:click={() => setSort('help')}>Help {sortKey==='help' ? (sortAsc?'↑':'↓') : ''}</th>
            <th style="text-align:right;cursor:pointer" title="Builder Bonus" on:click={() => setSort('build')}>Build {sortKey==='build' ? (sortAsc?'↑':'↓') : ''}</th>
            <th style="text-align:right;cursor:pointer" title="Final Score" on:click={() => setSort('final_score')}>Final {sortKey==='final_score' ? (sortAsc?'↑':'↓') : ''}</th>
            <th style="text-align:right;cursor:pointer" title="Estimated Points" on:click={() => setSort('estimated_rai')}>Est. POINTS {sortKey==='estimated_rai' ? (sortAsc?'↑':'↓') : ''}</th>
          </tr>
        </thead>
        <tbody>
          {#if filtered.length === 0}
            <tr><td colspan="11" class="loading" style="padding:40px;text-align:center">
              {geoData.length === 0 ? 'No data yet — week just started!' : 'No results match your search.'}
            </td></tr>
          {:else}
            {#each filtered as m}
              <tr
                class="{m.capped ? 'row-selected' : ''}"
                style="cursor:pointer"
                on:click={() => { calcAddr = m.address; runCalc(); document.querySelector('.calc-section')?.scrollIntoView({behavior:'smooth',block:'center'}); }}
              >
                <td class="rank-cell {m.rank === 1 ? 'rank-gold' : m.rank === 2 ? 'rank-silver' : m.rank === 3 ? 'rank-bronze' : ''}">
                  #{m.rank}
                </td>
                <td>
                  <div class="moniker-cell">{m.moniker || '—'}</div>
                  <div class="addr-cell" style="margin-top:3px">
                    <span class="addr-text">{m.address || ''}</span>
                  </div>
                </td>
                <td class="num-cell">{fmt(m.effort_completed)}</td>
                <td class="num-cell" style="color:var(--blue)">{m.jc?.toFixed(4)}</td>
                <td class="num-cell" style="color:var(--accent)">{m.eff?.toFixed(2)}</td>
                <td class="num-cell">{m.pres?.toFixed(4)}</td>
                <td class="num-cell">{m.steady?.toFixed(4)}</td>
                <td class="num-cell">{m.help?.toFixed(4)}</td>
                <td class="num-cell" style="color:var(--accent3)">{m.build?.toFixed(4)}</td>
                <td class="num-cell" style="color:var(--accent);font-weight:600">{m.final_score?.toFixed(4)}</td>
                <td class="num-cell">
                  <span style="color:{m.capped ? 'var(--accent)' : 'var(--accent3)'};font-weight:600">
                    {fmt(Math.round(m.estimated_rai))}
                    {#if m.capped}<span style="font-size:10px;margin-left:3px">🔒</span>{/if}
                  </span>
                </td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  {/if}
</div>