<script>
  import { onMount } from 'svelte';
  import { API, fmt, shortAddr } from '../../stores/app.js';

  let walletAddr = '';
  let loading = false;
  let error = '';
  let jobsData = null;

  async function searchWalletJobs() {
    if (!walletAddr.trim()) return;
    loading = true;
    error = '';
    jobsData = null;
    try {
      const r = await fetch(`${API}/api/wallet/${encodeURIComponent(walletAddr.trim())}/jobs`, {
        signal: AbortSignal.timeout(15000)
      });
      if (!r.ok) throw new Error('Not found');
      jobsData = await r.json();
    } catch {
      error = 'Wallet not found or no jobs. Check address and try again.';
    }
    loading = false;
  }

  $: pendingExec = jobsData?.pending_execution || [];
  $: pendingVal = jobsData?.pending_validation || [];
  $: stats = jobsData?.stats || {};
</script>

<!-- HERO -->
<div class="hero">
  <div class="hero-bg"></div>
  <div style="position:relative;z-index:1">
    <div class="hero-eyebrow"><span class="hero-eyebrow-dot"></span>Republic AI · Wallet Jobs</div>
    <h1><span class="line1">WALLET</span><span class="line2">JOB TRACKER</span></h1>
    <p class="hero-sub">Search any wallet address to see Pending Execution & Validation jobs.</p>
  </div>
</div>

<!-- SEARCH -->
<div class="search-section">
  <div class="search-label">Enter Wallet or Validator Address</div>
  <div class="search-box">
    <input
      class="search-input"
      placeholder="rai1... or raivaloper1..."
      bind:value={walletAddr}
      on:keypress={e => e.key === 'Enter' && searchWalletJobs()}
    />
    <button class="btn-search" on:click={searchWalletJobs}>SEARCH</button>
  </div>
  {#if loading}<div class="loading">Fetching jobs...</div>{/if}
  {#if error}<div class="error-msg">{error}</div>{/if}
</div>

{#if jobsData}
<!-- STATS -->
<div class="stats-grid" style="margin-top:0">
  <div class="stat-card">
    <div class="stat-label">Total Jobs</div>
    <div class="stat-value fire">{fmt(jobsData.total_jobs || 0)}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Pending Execution</div>
    <div class="stat-value" style="color:var(--accent)">{fmt(stats.PendingExecution || 0)}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Pending Validation</div>
    <div class="stat-value" style="color:var(--accent3)">{fmt(stats.PendingValidation || 0)}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Address</div>
    <div class="stat-value" style="font-size:11px;word-break:break-all;color:var(--muted)">{jobsData.valoper || jobsData.address}</div>
  </div>
</div>

<!-- PENDING EXECUTION TABLE -->
<div class="section">
  <div class="section-header">
    <div class="section-title">
      <div class="section-title-bar"></div>
      Pending Execution
      <span style="font-size:13px;color:var(--accent);opacity:0.7;margin-left:6px">({fmt(stats.PendingExecution || 0)} total · showing {pendingExec.length})</span>
    </div>
  </div>
  {#if pendingExec.length === 0}
    <div class="loading" style="padding:32px;text-align:center;opacity:0.5">No pending execution jobs</div>
  {:else}
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Job ID</th>
            <th>Creator</th>
            <th>Result Endpoint</th>
            <th style="text-align:right">Status</th>
          </tr>
        </thead>
        <tbody>
          {#each pendingExec as job}
            <tr>
              <td><span style="color:var(--accent);font-size:12px;font-weight:600">{job.job_id}</span></td>
              <td><span class="addr-text">{shortAddr(job.creator || '—')}</span></td>
              <td><span style="font-size:11px;color:var(--muted)">{job.result_fetch_endpoint || '—'}</span></td>
              <td class="num-cell">
                <span class="uptime-badge" style="color:var(--accent);border-color:rgba(255,170,0,.3)">Pending Exec</span>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<!-- PENDING VALIDATION TABLE -->
<div class="section">
  <div class="section-header">
    <div class="section-title">
      <div class="section-title-bar" style="background:var(--accent3)"></div>
      Pending Validation
      <span style="font-size:13px;color:var(--accent3);opacity:0.7;margin-left:6px">({fmt(stats.PendingValidation || 0)} total · showing {pendingVal.length})</span>
    </div>
  </div>
  {#if pendingVal.length === 0}
    <div class="loading" style="padding:32px;text-align:center;opacity:0.5">No pending validation jobs</div>
  {:else}
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Job ID</th>
            <th>Creator</th>
            <th>Result Endpoint</th>
            <th style="text-align:right">Status</th>
          </tr>
        </thead>
        <tbody>
          {#each pendingVal as job}
            <tr>
              <td><span style="color:var(--accent3);font-size:12px;font-weight:600">{job.job_id}</span></td>
              <td><span class="addr-text">{shortAddr(job.creator || '—')}</span></td>
              <td><span style="font-size:11px;color:var(--muted)">{job.result_fetch_endpoint || '—'}</span></td>
              <td class="num-cell">
                <span class="uptime-badge" style="color:var(--accent3);border-color:rgba(0,255,170,.3)">Pending Val</span>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
{/if}