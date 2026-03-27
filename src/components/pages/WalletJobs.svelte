<script>
  import { onMount } from 'svelte';
  import { API, fmt, shortAddr } from '../../stores/app.js';

  let walletAddr = '';
  let loading = false;
  let error = '';
  let jobsData = null;
  let activeJob = null;
  let jobDetailLoading = false;
  let jobDetailData = null;
  let jobDetailError = '';

  async function searchWalletJobs() {
    if (!walletAddr.trim()) return;
    loading = true;
    error = '';
    jobsData = null;
    activeJob = null;
    jobDetailData = null;

    try {
      const r = await fetch(`${API}/api/wallet/${encodeURIComponent(walletAddr.trim())}/jobs`, {
        signal: AbortSignal.timeout(10000)
      });
      if (!r.ok) throw new Error('Not found');
      jobsData = await r.json();
    } catch {
      error = 'Wallet not found or no jobs. Check address and try again.';
    }
    loading = false;
  }

  async function openJobDetail(jobId) {
    if (activeJob === jobId) {
      activeJob = null;
      jobDetailData = null;
      return;
    }
    activeJob = jobId;
    jobDetailLoading = true;
    jobDetailError = '';
    jobDetailData = null;

    try {
      const r = await fetch(`${API}/api/job/${encodeURIComponent(jobId)}`, {
        signal: AbortSignal.timeout(10000)
      });
      if (!r.ok) throw new Error('Job not found');
      jobDetailData = await r.json();
    } catch {
      jobDetailError = 'Could not load job detail.';
    }
    jobDetailLoading = false;
  }

  $: pendingExec = jobsData?.PendingExecution || [];
  $: pendingVal = jobsData?.PendingValidation || [];
  $: totalJobs = pendingExec.length + pendingVal.length;
</script>

<!-- HERO -->
<div class="hero">
  <div class="hero-bg"></div>
  <div style="position:relative;z-index:1">
    <div class="hero-eyebrow"><span class="hero-eyebrow-dot"></span>Republic AI · Wallet Jobs</div>
    <h1><span class="line1">WALLET</span><span class="line2">JOB TRACKER</span></h1>
    <p class="hero-sub">Search any wallet address to see pending execution & validation jobs.</p>
  </div>
</div>

<!-- SEARCH -->
<div class="search-section">
  <div class="search-label">Enter Wallet Address</div>
  <div class="search-box">
    <input
      class="search-input"
      placeholder="rai1... or raivaloper1..."
      bind:value={walletAddr}
      on:keypress={e => e.key === 'Enter' && searchWalletJobs()}
    />
    <button class="btn-search" on:click={searchWalletJobs}>SEARCH</button>
  </div>

  {#if loading}
    <div class="loading">Fetching jobs...</div>
  {:else if error}
    <div class="error-msg">{error}</div>
  {/if}
</div>

<!-- STATS CARDS -->
{#if jobsData}
<div class="stats-grid" style="margin-top:0">
  <div class="stat-card">
    <div class="stat-label">Total Jobs</div>
    <div class="stat-value fire">{fmt(totalJobs)}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Pending Execution</div>
    <div class="stat-value" style="color:var(--accent)">{fmt(pendingExec.length)}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Pending Validation</div>
    <div class="stat-value" style="color:var(--accent3)">{fmt(pendingVal.length)}</div>
  </div>
</div>

<!-- PENDING EXECUTION TABLE -->
<div class="section">
  <div class="section-header">
    <div class="section-title">
      <div class="section-title-bar"></div>
      Pending Execution
      <span style="margin-left:8px;font-size:13px;color:var(--accent);opacity:0.7">({pendingExec.length})</span>
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
            <th>Result URL</th>
            <th style="text-align:right">Status</th>
          </tr>
        </thead>
        <tbody>
          {#each pendingExec as job}
            <tr
              class="clickable-row {activeJob === job.job_id ? 'row-selected' : ''}"
              on:click={() => openJobDetail(job.job_id)}
            >
              <td>
                <div class="addr-cell">
                  <span class="addr-text" style="color:var(--accent);font-size:12px">{job.job_id}</span>
                </div>
              </td>
              <td>
                <div class="addr-cell">
                  <span class="addr-text">{shortAddr(job.creator || '—')}</span>
                </div>
              </td>
              <td>
                {#if job.result_url}
                  
                    href={job.result_url}
                    target="_blank"
                    rel="noopener"
                    style="color:var(--blue);font-size:12px;word-break:break-all"
                    on:click|stopPropagation={() => {}}
                  >{job.result_url.length > 40 ? job.result_url.slice(0,40)+'...' : job.result_url}</a>
                {:else}
                  <span style="opacity:0.4">—</span>
                {/if}
              </td>
              <td class="num-cell">
                <span class="uptime-badge" style="color:var(--accent);border-color:rgba(255,170,0,.3)">Pending Exec</span>
              </td>
            </tr>

            <!-- INLINE DETAIL ROW -->
            {#if activeJob === job.job_id}
              <tr>
                <td colspan="4" style="padding:0;background:var(--bg2)">
                  <div style="padding:20px 24px;border-left:3px solid var(--accent)">
                    {#if jobDetailLoading}
                      <div class="loading">Loading job detail...</div>
                    {:else if jobDetailError}
                      <div class="error-msg">{jobDetailError}</div>
                    {:else if jobDetailData}
                      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px">
                        {#each Object.entries(jobDetailData) as [k, v]}
                          <div style="background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:12px 14px">
                            <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px">{k}</div>
                            <div style="font-size:12px;color:var(--text);word-break:break-all;opacity:.9">
                              {#if typeof v === 'string' && v.startsWith('http')}
                                <a href={v} target="_blank" rel="noopener" style="color:var(--blue)">{v.length > 50 ? v.slice(0,50)+'…' : v}</a>
                              {:else}
                                {JSON.stringify(v)}
                              {/if}
                            </div>
                          </div>
                        {/each}
                      </div>
                    {/if}
                  </div>
                </td>
              </tr>
            {/if}
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
      <span style="margin-left:8px;font-size:13px;color:var(--accent3);opacity:0.7">({pendingVal.length})</span>
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
            <th>Result URL</th>
            <th style="text-align:right">Status</th>
          </tr>
        </thead>
        <tbody>
          {#each pendingVal as job}
            <tr
              class="clickable-row {activeJob === job.job_id ? 'row-selected' : ''}"
              on:click={() => openJobDetail(job.job_id)}
            >
              <td>
                <div class="addr-cell">
                  <span class="addr-text" style="color:var(--accent3);font-size:12px">{job.job_id}</span>
                </div>
              </td>
              <td>
                <div class="addr-cell">
                  <span class="addr-text">{shortAddr(job.creator || '—')}</span>
                </div>
              </td>
              <td>
                {#if job.result_url}
                  
                    href={job.result_url}
                    target="_blank"
                    rel="noopener"
                    style="color:var(--blue);font-size:12px;word-break:break-all"
                    on:click|stopPropagation
                  >{job.result_url.length > 40 ? job.result_url.slice(0,40)+'…' : job.result_url}</a>
                {:else}
                  <span style="opacity:0.4">—</span>
                {/if}
              </td>
              <td class="num-cell">
                <span class="uptime-badge" style="color:var(--accent3);border-color:rgba(0,255,170,.3)">Pending Val</span>
              </td>
            </tr>

            <!-- INLINE DETAIL ROW -->
            {#if activeJob === job.job_id}
              <tr>
                <td colspan="4" style="padding:0;background:var(--bg2)">
                  <div style="padding:20px 24px;border-left:3px solid var(--accent3)">
                    {#if jobDetailLoading}
                      <div class="loading">Loading job detail...</div>
                    {:else if jobDetailError}
                      <div class="error-msg">{jobDetailError}</div>
                    {:else if jobDetailData}
                      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px">
                        {#each Object.entries(jobDetailData) as [k, v]}
                          <div style="background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:12px 14px">
                            <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px">{k}</div>
                            <div style="font-size:12px;color:var(--text);word-break:break-all;opacity:.9">
                              {#if typeof v === 'string' && v.startsWith('http')}
                                <a href={v} target="_blank" rel="noopener" style="color:var(--blue)">{v.length > 50 ? v.slice(0,50)+'…' : v}</a>
                              {:else}
                                {JSON.stringify(v)}
                              {/if}
                            </div>
                          </div>
                        {/each}
                      </div>
                    {/if}
                  </div>
                </td>
              </tr>
            {/if}
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
{/if}