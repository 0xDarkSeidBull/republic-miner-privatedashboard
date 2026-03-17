<script>
  import { onMount } from 'svelte';
  import { API, fmt, shortAddr, rankClass, uptimeBadgeHtml, getSortVal, copyText } from '$lib/stores/app.js';
  import { allLbData } from '$lib/stores/app.js';
  import MinerDetail from '../MinerDetail.svelte';

  let lbSortKey = 'total';
  let searchQ = '';
  let activeDetailAddr = null;

  async function loadLeaderboard() {
    try {
      const r = await fetch(API + '/api/leaderboard?limit=100', { signal: AbortSignal.timeout(10000) });
      const d = await r.json();
      allLbData.set(d.data || d);
    } catch(e) { console.warn(e); }
  }

  $: filtered = searchQ
    ? $allLbData.filter(m => (m.address||'').toLowerCase().includes(searchQ.toLowerCase()) || (m.moniker||'').toLowerCase().includes(searchQ.toLowerCase()))
    : $allLbData;

  $: sorted = [...filtered].sort((a, b) => getSortVal(b, lbSortKey) - getSortVal(a, lbSortKey));

  $: podiumTop = $allLbData.slice(0, 3);

  function openDetail(addr) {
    activeDetailAddr = activeDetailAddr === addr ? null : addr;
  }

  onMount(loadLeaderboard);
</script>

<div class="lb-hero">
  <h2>FULL <span>LEADERBOARD</span></h2>
  <p>All miners ranked by total job score on Republic AI Testnet</p>
</div>

<!-- PODIUM -->
<div class="podium-wrap">
  {#if podiumTop.length === 0}
    <div class="loading">Loading podium...</div>
  {:else}
    {#each [1, 0, 2] as i}
      {@const m = podiumTop[i]}
      {#if m}
        <div class="podium-item {i === 0 ? 'p1' : i === 1 ? 'p2' : 'p3'}" on:click={() => openDetail(m.address)}>
          <div class="podium-medal">{['🥇','🥈','🥉'][i]}</div>
          <div class="podium-rank-num">Rank #{m.rank}</div>
          <div class="podium-moniker">{m.moniker || shortAddr(m.address)}</div>
          {#if m.moniker}<div class="podium-addr">{shortAddr(m.address)}</div>{/if}
          <div class="podium-score">{fmt(m.total)}</div>
          <div>{@html uptimeBadgeHtml(m.uptime)}</div>
        </div>
      {/if}
    {/each}
  {/if}
</div>

<!-- SEARCH -->
<div class="lb-search-wrap">
  <input class="lb-search-input" placeholder="🔍  Search by moniker or address..." bind:value={searchQ}/>
</div>

<!-- TABLE -->
<div class="section">
  <div class="section-header">
    <div class="section-title"><div class="section-title-bar"></div>Full Leaderboard · {$allLbData.length} miners</div>
    <button class="refresh-btn" on:click={loadLeaderboard}>↻ Refresh</button>
  </div>
  <div class="sort-bar">
    {#each [['total','Total Pts'],['submit','Submit'],['result','Result'],['uptime','Uptime']] as [key, label]}
      <button class="sort-btn {lbSortKey === key ? 'active' : ''}" on:click={() => lbSortKey = key}>{label}</button>
    {/each}
  </div>
  <div class="table-wrap">
    <table>
      <thead><tr>
        <th>Rank</th><th>Moniker</th><th>Address</th>
        <th style="text-align:right">Submit</th><th style="text-align:right">Result</th>
        <th style="text-align:right">Uptime</th><th style="text-align:right">Total</th>
      </tr></thead>
      <tbody>
        {#if sorted.length === 0}
          <tr><td colspan="7" class="loading">Loading...</td></tr>
        {:else}
          {#each sorted as m}
            <tr class="clickable-row {activeDetailAddr === m.address ? 'row-selected' : ''}" on:click={() => openDetail(m.address)}>
              <td class="rank-cell {rankClass(m.rank)}">#{ m.rank }</td>
              <td class="moniker-cell {!m.moniker ? 'empty' : ''}">{m.moniker || '—'}</td>
              <td class="addr-cell"><span class="addr-text">{m.address||''}</span><button class="copy-btn" on:click|stopPropagation={() => copyText(m.address)}>⎘</button></td>
              <td class="num-cell">{fmt(m.submit_job)}</td>
              <td class="num-cell">{fmt(m.submit_job_result)}</td>
              <td class="num-cell">{@html uptimeBadgeHtml(m.uptime)}</td>
              <td class="num-cell" style="color:var(--accent)">{fmt(m.total)}</td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>
</div>

{#if activeDetailAddr}
  <div style="margin:0 28px 40px;max-width:1224px;margin-left:auto;margin-right:auto">
    <MinerDetail
      addr={activeDetailAddr}
      page="leaderboard"
      cachedData={$allLbData.find(m => m.address === activeDetailAddr) || {}}
      onClose={() => { activeDetailAddr = null; }}
    />
  </div>
{/if}
