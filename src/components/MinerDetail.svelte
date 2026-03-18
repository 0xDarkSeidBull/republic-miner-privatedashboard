<script>
  import { onMount, afterUpdate, tick } from 'svelte';
  import { API, fmt, shortAddr, uptimeBadgeHtml, statusBadgeHtml, copyText } from '../stores/app.js';

  export let addr = '';
  export let page = 'home';
  export let cachedData = {};
  export let onClose = () => {};

  let miner = { address: addr };
  let loading = true;
  let chartInstance = null;
let weeklyPoints = [];
let weeklyLoading = false;
let totalEstPoints = 0;

async function loadMinerWeekly(address) {
  weeklyLoading = true;
  try {
    const r = await fetch(`${API}/api/weekly`, { signal: AbortSignal.timeout(8000) });
    const current = await r.json();
    const weeks = current.available_weeks || [];
    const allData = {};
    for (const week of weeks) {
      const wr = await fetch(`${API}/api/weekly?week=${week}`, { signal: AbortSignal.timeout(8000) });
      const wd = await wr.json();
      const miner = (wd.data || []).find(m => m.address === address);
      if (miner) allData[week] = miner;
    }
    weeklyPoints = Object.entries(allData).sort((a,b) => b[0].localeCompare(a[0]));
    totalEstPoints = weeklyPoints.reduce((s, [,m]) => s + m.estimated_points, 0);
  } catch(e) { console.warn(e); }
  weeklyLoading = false;
}

  onMount(async () => {
    try {
      const res = await fetch(`${API}/api/miner/${encodeURIComponent(addr)}`, { signal: AbortSignal.timeout(8000) });
      if (res.ok) {
        const d = await res.json();
        miner = { address: addr, ...d };
      } else {
        miner = { address: addr, ...cachedData };
      }
    } catch {
      miner = { address: addr, ...cachedData };
    }
    await tick();
    document.querySelector('.miner-detail-panel')?.scrollIntoView({behavior:'smooth', block:'start'});
    loading = false;
loadMinerWeekly(addr);
  });

  afterUpdate(() => {
    if (!loading) renderChart();
  });

  function renderChart() {
    const ctx = document.getElementById('detailChartCanvas');
    if (!ctx || typeof Chart === 'undefined') return;
    if (chartInstance) { chartInstance.destroy(); chartInstance = null; }
    const submit = miner.submit_job || 0;
    const dailyData = miner.daily_jobs || miner.daily || null;
    const hasDaily = dailyData && Object.keys(dailyData).length > 0;
    let labels, values;
    if (hasDaily) {
      const e = Object.entries(dailyData).sort((a, b) => a[0].localeCompare(b[0])).slice(-14);
      labels = e.map(x => x[0].slice(5));
      values = e.map(x => x[1]);
    } else {
      labels = Array.from({ length: 14 }, (_, i) => {
        const d = new Date(); d.setDate(d.getDate() - 13 + i);
        return (d.getMonth() + 1) + '/' + d.getDate();
      });
      const base = Math.max(1, Math.floor(submit / 14));
      values = labels.map((_, i) => i < 13 ? Math.max(0, base + Math.floor((Math.random() - .5) * base * .8)) : 0);
    }
    chartInstance = new Chart(ctx, {
      type: 'bar',
      data: { labels, datasets: [{ label: 'Jobs', data: values, backgroundColor: 'rgba(255,60,0,0.4)', borderColor: 'rgba(255,106,0,0.8)', borderWidth: 1, borderRadius: 2, borderSkipped: false }] },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { callbacks: { title: t => 'Date: ' + t[0].label, label: t => 'Jobs: ' + t.raw }, backgroundColor: 'rgba(8,9,15,.95)', titleColor: '#fff', bodyColor: '#ff6a00', borderColor: 'rgba(255,60,0,.3)', borderWidth: 1 } },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 10 }, color: '#4a5280' } },
          y: { grid: { color: 'rgba(255,255,255,.04)' }, ticks: { font: { size: 10 }, color: '#4a5280', stepSize: 1 }, beginAtZero: true }
        }
      }
    });
  }

  $: moniker = miner.moniker || miner.name || 'Unknown';
  $: initials = moniker.replace(/[^a-zA-Z0-9]/g, '').slice(0, 2).toUpperCase() || '??';
  $: submit = miner.submit_job || 0;
  $: result = miner.submit_job_result || 0;
  $: total = miner.total || miner.total_points || 0;
  $: valoper = miner.valoper || miner.validator_address || miner.operator_address || '—';
  $: efficiency = submit > 0 ? Math.round(result / submit * 100) : 0;
  $: effColor = efficiency >= 80 ? 'var(--green)' : efficiency >= 50 ? 'var(--accent3)' : 'var(--red)';
</script>

<svelte:head>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
</svelte:head>

<div class="miner-detail-panel">
  <button class="detail-close" on:click={onClose}>✕</button>

  {#if loading}
    <div class="detail-loading">Loading miner data...</div>
  {:else}
    <div class="detail-top">
      <div class="detail-avatar">{initials}</div>
      <div style="flex:1">
        <div class="detail-name">{moniker}</div>
        <div class="detail-status-row">
          {@html statusBadgeHtml(miner)}
          {@html uptimeBadgeHtml(miner.uptime)}
          <span style="font-family:var(--font-mono);font-size:10px;color:var(--muted);letter-spacing:.1em">RANK #{miner.rank || '—'}</span>
        </div>
      </div>
    </div>

    <div class="detail-addr-grid">
      <div class="detail-addr-item" style="grid-column:1/-1">
        <div class="detail-addr-label">Wallet Address</div>
        <div class="detail-addr-value">
          <span style="flex:1;word-break:break-all">{addr}</span>
          <button class="copy-btn" on:click={() => copyText(addr)}>⎘</button>
        </div>
      </div>
      {#if valoper !== '—'}
      <div class="detail-addr-item" style="grid-column:1/-1">
        <div class="detail-addr-label">Validator Address</div>
        <div class="detail-addr-value">
          <span style="flex:1;word-break:break-all">{valoper}</span>
          <button class="copy-btn" on:click={() => copyText(valoper)}>⎘</button>
        </div>
      </div>
      {/if}
      <div class="detail-addr-item">
        <div class="detail-addr-label">Last Scanned Block</div>
        <div class="detail-addr-value" style="font-size:14px">{fmt(miner.last_scanned_height) || '—'}</div>
      </div>
      <div class="detail-addr-item">
        <div class="detail-addr-label">Last Scan Time</div>
        <div class="detail-addr-value" style="font-size:12px">{miner.last_scan_time || '—'}</div>
      </div>
    </div>

    <div class="detail-stats-row">
      <div class="detail-stat"><div class="detail-stat-label">Submit Jobs</div><div class="detail-stat-value">{fmt(submit)}</div></div>
      <div class="detail-stat"><div class="detail-stat-label">Submit Results</div><div class="detail-stat-value">{fmt(result)}</div></div>
      <div class="detail-stat"><div class="detail-stat-label">Efficiency</div><div class="detail-stat-value" style="color:{effColor}">{efficiency}%</div></div>
      <div class="detail-stat">
        <div class="detail-stat-label">Est. Points (All Weeks)</div>
        <div class="detail-stat-value" style="background:linear-gradient(135deg,var(--accent),var(--accent3));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">{fmt(totalEstPoints || total)}</div>
      </div>
    </div>

    <div class="detail-chart-title">Daily Job Distribution (Est.)</div>
    <div class="detail-chart-wrap"><canvas id="detailChartCanvas"></canvas></div>
  {/if}
</div>
