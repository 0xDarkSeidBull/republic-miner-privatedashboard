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

  async function loadGeo() {
    geoLoading = true;
    geoError = '';
    try {
      const r = await fetch(`${API}/api/weekly/geo`, { signal: AbortSignal.timeout(120000) });
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

  function calcWeekProgress() {
    const now = new Date();
    const day = now.getUTCDay();
    const elapsed = day * 24 * 60 + now.getUTCHours() * 60 + now.getUTCMinutes();
    weekProgress = Math.min(100, Math.round((elapsed / (7 * 24 * 60)) * 100));
  }

  onMount(() => {
    loadGeo();
    interval = setInterval(loadGeo, 5 * 60 * 1000);
  });
  onDestroy(() => clearInterval(interval));
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
        📅 {geoMeta.week || 'Current Week'} &nbsp;·&nbsp; Pool: <span style="color:var(--accent)">1,600,000 RAI</span>
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
    <div class="stat-value" style="color:var(--accent)">1.6M RAI</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Max Per Wallet</div>
    <div class="stat-value" style="color:var(--accent3)">240K RAI</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Last Updated</div>
    <div class="stat-value" style="font-size:16px">{lastUpdated || '—'}</div>
    <div class="stat-sub">Auto-refresh 5 min</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Capped Wallets</div>
    <div class="stat-value fire">{geoData.filter(m => m.capped).length}</div>
    <div class="stat-sub">240K RAI max hit</div>
  </div>
</div>

<!-- TABLE -->
<div class="section">
  <div class="section-header">
    <div class="section-title">
      <div class="section-title-bar"></div>
      Live Geo Scores
    </div>
    <button class="refresh-btn" on:click={loadGeo}>↻ Refresh</button>
  </div>

  {#if geoLoading && geoData.length === 0}
    <div class="loading" style="padding:60px;text-align:center">Calculating scores... (may take 1-2 min)</div>
  {:else if geoError}
    <div class="error-msg" style="margin:20px">{geoError}</div>
  {:else}
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Miner</th>
            <th style="text-align:right" title="Effort Completed">EfC</th>
            <th style="text-align:right" title="Job Creation Score">JC</th>
            <th style="text-align:right" title="Effort Score">Eff</th>
            <th style="text-align:right" title="Presence Score">Pres</th>
            <th style="text-align:right" title="Steadiness Score">Steady</th>
            <th style="text-align:right" title="Helpfulness Score">Help</th>
            <th style="text-align:right" title="Builder Bonus">Build</th>
            <th style="text-align:right" title="Final Score">Final</th>
            <th style="text-align:right" title="Estimated RAI">Est. RAI</th>
          </tr>
        </thead>
        <tbody>
          {#if geoData.length === 0}
            <tr><td colspan="11" class="loading" style="padding:40px;text-align:center">No data yet — week just started!</td></tr>
          {:else}
            {#each geoData as m}
              <tr class="{m.capped ? 'row-selected' : ''}">
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