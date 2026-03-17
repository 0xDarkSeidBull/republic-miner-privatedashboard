<script>
  import { onMount } from 'svelte';
  import { API, fmt, shortAddr } from '../../stores/app.js';

  let weeklyData = [];
  let availableWeeks = [];
  let selectedWeek = '';
  let loading = true;
  let totalJobs = 0;
  let allTimePoints = {};
let allTimeLoading = false;

async function loadAllTimePoints() {
  allTimeLoading = true;
  const totals = {};
  for (const week of availableWeeks) {
    try {
      const r = await fetch(`${API}/api/weekly?week=${week}`, { signal: AbortSignal.timeout(8000) });
      const d = await r.json();
      for (const m of (d.data || [])) {
        if (!totals[m.address]) totals[m.address] = { points: 0, weeks: 0 };
        totals[m.address].points += m.estimated_points;
        totals[m.address].weeks += 1;
      }
    } catch(e) {}
  }
  allTimePoints = Object.entries(totals)
    .sort((a, b) => b[1].points - a[1].points)
    .map(([addr, d], i) => ({ rank: i+1, address: addr, total_points: d.points, weeks: d.weeks }));
  allTimeLoading = false;
}

  async function loadWeekly(week = '') {
    loading = true;
    try {
      const url = week ? `${API}/api/weekly?week=${week}` : `${API}/api/weekly`;
      const r = await fetch(url, { signal: AbortSignal.timeout(8000) });
      const d = await r.json();
      weeklyData = d.data || [];
      availableWeeks = d.available_weeks || [];
      selectedWeek = d.week || '';
      totalJobs = weeklyData.reduce((s, m) => s + m.total_jobs, 0);
      if (availableWeeks.length > 0 && Object.keys(allTimePoints).length === 0) loadAllTimePoints();
    } catch(e) { console.warn(e); }
    loading = false;
  }

  onMount(async () => { 
  await loadWeekly(); 
  loadAllTimePoints(); 
});
</script>

<div class="lb-hero">
  <h2>WEEKLY <span>POINTS</span></h2>
  <p>Estimated GPU miner points distribution — 1,600,000 pts pool per week</p>
</div>

<!-- WEEK SELECTOR -->
<div style="padding:0 28px 24px;max-width:1280px;margin:0 auto;display:flex;align-items:center;gap:12px;flex-wrap:wrap">
  <span style="font-family:var(--font-mono);font-size:11px;color:var(--muted);letter-spacing:.15em;text-transform:uppercase">Week:</span>
  {#each availableWeeks as week}
    <button
      on:click={() => loadWeekly(week)}
      style="padding:6px 16px;font-family:var(--font-body);font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;cursor:pointer;border:1px solid {selectedWeek === week ? 'var(--accent)' : 'var(--border2)'};background:{selectedWeek === week ? 'rgba(255,60,0,.1)' : 'var(--surface)'};color:{selectedWeek === week ? 'var(--accent)' : 'var(--muted)'};transition:all .2s">
      {week}
    </button>
  {/each}
</div>

<!-- PODIUM TOP 3 -->
{#if !loading && weeklyData.length >= 3}
<div class="podium-wrap">
  {#each [1, 0, 2] as i}
    {@const m = weeklyData[i]}
    {#if m}
      <div class="podium-item {i === 0 ? 'p1' : ''}">
        <div class="podium-medal">{['🥇','🥈','🥉'][i]}</div>
        <div class="podium-rank-num">Rank #{m.rank}</div>
        <div class="podium-moniker">{shortAddr(m.address)}</div>
        <div class="podium-score">{fmt(m.estimated_points)}</div>
        <div style="font-family:var(--font-mono);font-size:10px;color:var(--muted)">{m.share_pct}%</div>
      </div>
    {/if}
  {/each}
</div>
{/if}

<!-- TABLE -->
<div class="section">
  <div class="section-header">
    <div class="section-title"><div class="section-title-bar"></div>Points Leaderboard — {selectedWeek}</div>
  </div>

  <!-- INFO BAR -->
  <div style="display:flex;gap:1px;background:var(--border);border:1px solid var(--border);margin-bottom:14px">
    <div style="background:var(--surface);padding:12px 20px;flex:1;text-align:center">
      <div style="font-family:var(--font-mono);font-size:10px;color:var(--muted);letter-spacing:.15em;text-transform:uppercase;margin-bottom:4px">Points Pool</div>
      <div style="font-family:var(--font-display);font-size:22px;background:linear-gradient(135deg,var(--accent),var(--accent3));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">1,600,000</div>
    </div>
    <div style="background:var(--surface);padding:12px 20px;flex:1;text-align:center">
      <div style="font-family:var(--font-mono);font-size:10px;color:var(--muted);letter-spacing:.15em;text-transform:uppercase;margin-bottom:4px">Total Jobs</div>
      <div style="font-family:var(--font-display);font-size:22px;color:var(--text)">{fmt(totalJobs)}</div>
    </div>
    <div style="background:var(--surface);padding:12px 20px;flex:1;text-align:center">
      <div style="font-family:var(--font-mono);font-size:10px;color:var(--muted);letter-spacing:.15em;text-transform:uppercase;margin-bottom:4px">Miners</div>
      <div style="font-family:var(--font-display);font-size:22px;color:var(--text)">{weeklyData.length}</div>
    </div>
    <div style="background:var(--surface);padding:12px 20px;flex:1;text-align:center">
      <div style="font-family:var(--font-mono);font-size:10px;color:var(--muted);letter-spacing:.15em;text-transform:uppercase;margin-bottom:4px">Reset</div>
      <div style="font-family:var(--font-display);font-size:22px;color:var(--text)">Sunday 00:00 UTC</div>
    </div>
  </div>

  <div class="table-wrap">
    <table>
      <thead><tr>
        <th>Rank</th>
        <th>Address</th>
        <th style="text-align:right">Submit</th>
        <th style="text-align:right">Result</th>
        <th style="text-align:right">Total Jobs</th>
        <th style="text-align:right">Share %</th>
        <th style="text-align:right">Est. Points</th>
      </tr></thead>
      <tbody>
        {#if loading}
          <tr><td colspan="7" class="loading">Loading...</td></tr>
        {:else if weeklyData.length === 0}
          <tr><td colspan="7" class="empty-state">No data available</td></tr>
        {:else}
          {#each weeklyData as m}
            <tr>
              <td class="rank-cell {m.rank === 1 ? 'rank-1' : m.rank === 2 ? 'rank-2' : m.rank === 3 ? 'rank-3' : ''}">#{ m.rank }</td>
              <td class="addr-cell"><span class="addr-text">{m.address}</span></td>
              <td class="num-cell">{fmt(m.submit_job)}</td>
              <td class="num-cell">{fmt(m.submit_job_result)}</td>
              <td class="num-cell">{fmt(m.total_jobs)}</td>
              <td class="num-cell">{m.share_pct}%</td>
              <td class="num-cell" style="color:var(--accent);font-size:14px">{fmt(m.estimated_points)}</td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>

  <div style="margin-top:14px;font-family:var(--font-mono);font-size:10px;color:var(--muted);letter-spacing:.08em">
    ⚠️ Estimated points based on job share. Actual distribution by Republic AI team may vary. Pool: 1.6M pts (32% of 5M weekly).
 <!-- ALL TIME TABLE -->
<div class="section-header" style="margin-top:32px">
  <div class="section-title"><div class="section-title-bar"></div>All-Time Points (All Weeks)</div>
</div>
<div class="table-wrap">
  <table>
    <thead><tr>
      <th>Rank</th>
      <th>Address</th>
      <th style="text-align:right">Weeks Active</th>
      <th style="text-align:right">Total Est. Points</th>
    </tr></thead>
    <tbody>
      {#if allTimeLoading}
        <tr><td colspan="4" class="loading">Calculating all-time points...</td></tr>
      {:else if allTimePoints.length === 0}
        <tr><td colspan="4" class="loading">Loading...</td></tr>
      {:else}
        {#each allTimePoints as m}
          <tr>
            <td class="rank-cell {m.rank === 1 ? 'rank-1' : m.rank === 2 ? 'rank-2' : m.rank === 3 ? 'rank-3' : ''}">#{ m.rank }</td>
            <td class="addr-cell"><span class="addr-text">{m.address}</span></td>
            <td class="num-cell">{m.weeks} week{m.weeks > 1 ? 's' : ''}</td>
            <td class="num-cell" style="color:var(--accent);font-size:14px">{fmt(m.total_points)}</td>
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>
</div>
  </div>
</div>