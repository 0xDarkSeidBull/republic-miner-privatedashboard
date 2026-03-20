<script>
  import { onMount } from 'svelte';

  const API = 'https://api.republicstats.xyz';

  // State
  let miners = [];
  let selectedMiner = null;
  let prompt = '';
  let isSubmitting = false;
  let trackingId = null;
  let jobStatus = null;
  let pollInterval = null;
  let step = 'input'; // input | submitting | polling | done | error
  // Job history
let jobHistory = [];

async function loadJobHistory() {
  try {
    const res = await fetch(`${API}/api/jobs/history`);
    const data = await res.json();
    jobHistory = data.jobs || [];
  } catch(e) {
    jobHistory = [];
  }
}

function saveJob(jobId, minerAddress) {
  const job = {
    id: jobId,
    miner: minerAddress,
    status: 'PendingExecution',
    time: new Date().toISOString()
  };
  jobHistory = [job, ...jobHistory].slice(0, 50);
  localStorage.setItem('republic_jobs', JSON.stringify(jobHistory));
}

async function refreshJobStatuses() {
  for (let job of jobHistory) {
    try {
      const res = await fetch(`${API}/api/jobs/${job.tracking_id}/status`);
      const data = await res.json();
      if (data.chain_job_id) {
        // Check chain status
        job.chainStatus = data.status;
      }
    } catch(e) {}
  }
  jobHistory = [...jobHistory];
}

onMount(async () => {
  await loadMiners();
  loadJobHistory();
    await loadJobHistory();
  await refreshJobStatuses();
});

  // Status steps for progress bar
  const STATUS_STEPS = {
    submitting:          1,
    tx_submitted:        2,
    waiting_result:      3,
    fetching_result:     4,
    completed:           5,
    failed:              5,
    timeout:             5,
    result_fetch_failed: 5,
  };

  const STATUS_LABELS = {
    submitting:          '⏳ Submitting to chain...',
    tx_submitted:        '📡 Transaction broadcast...',
    waiting_result:      '⚙️ Miner processing...',
    fetching_result:     '📥 Fetching result...',
    completed:           '✅ Job sent to miner!',
    failed:              '❌ Failed',
    timeout:             '⏱️ Timed out',
    result_fetch_failed: '⚠️ Result unavailable',
  };

  onMount(async () => {
    await loadMiners();
  });

  async function loadMiners() {
    try {
      const res = await fetch(`${API}/api/leaderboard?limit=50`);
      const data = await res.json();
      miners = (data.data || []).filter(m => m.submit_job_result > 0);
    } catch (e) {
      console.error('Failed to load miners', e);
    }
  }

  function selectMiner(miner) {
    selectedMiner = miner;
  }

  async function submitJob() {
    if (!prompt.trim()) return;
    if (!selectedMiner) return;

    isSubmitting = true;
    step = 'submitting';
    trackingId = null;
    jobStatus = null;

    try {
      const res = await fetch(`${API}/api/jobs/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: prompt.trim(),
          miner_address: selectedMiner.address
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Submission failed');
      }

      const data = await res.json();
      trackingId = data.tracking_id;
      step = 'polling';
      startPolling();
      saveJob(data.tracking_id, selectedMiner.address);
    } catch (e) {
      step = 'error';
      jobStatus = { error: e.message, status: 'failed' };
      isSubmitting = false;
    }
  }

  function startPolling() {
    pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`${API}/api/jobs/${trackingId}/status`);
        jobStatus = await res.json();

        const terminal = ['completed', 'failed', 'timeout', 'result_fetch_failed'];
        if (terminal.includes(jobStatus.status)) {
          clearInterval(pollInterval);
          step = 'done';
          isSubmitting = false;
        }
      } catch (e) {
        console.error('Poll error', e);
      }
    }, 3000);
  }

  function reset() {
    if (pollInterval) clearInterval(pollInterval);
    step = 'input';
    isSubmitting = false;
    trackingId = null;
    jobStatus = null;
    prompt = '';
    selectedMiner = null;
  }

  function shortAddr(addr) {
    if (!addr) return '';
    return addr.slice(0, 10) + '...' + addr.slice(-6);
  }

  $: progressStep = jobStatus ? (STATUS_STEPS[jobStatus.status] || 1) : (step === 'submitting' ? 1 : 0);
  $: isSuccess = jobStatus?.status === 'completed';
  $: isFailed = ['failed', 'timeout', 'result_fetch_failed'].includes(jobStatus?.status);
</script>

<div class="submit-page">
  <!-- Header -->
  <div class="page-header">
    <div class="header-badge">WORLD FIRST</div>
    <h1 class="page-title">⚡ Job Submission</h1>
    <p class="page-subtitle">Send AI jobs directly to Republic miners — browser native</p>
  </div>

  {#if step === 'input'}
    <div class="submit-layout">

      <!-- LEFT: Prompt Input -->
      <div class="card prompt-card">
        <div class="card-label">YOUR PROMPT</div>
        <textarea
          class="prompt-input"
          bind:value={prompt}
          placeholder="Ask anything... e.g. 'Explain quantum computing in simple terms'"
          rows="6"
          maxlength="2000"
        ></textarea>
        <div class="char-count">{prompt.length}/2000</div>

        <div class="job-meta">
          <div class="meta-item">
            <span class="meta-label">Model</span>
            <span class="meta-value">republic-llm-inference:latest</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Chain</span>
            <span class="meta-value">raitestnet_77701-1</span>
          </div>
        </div>
      </div>

      <!-- RIGHT: Miner Selection -->
      <div class="card miner-card">
        <div class="card-label">SELECT MINER</div>

        {#if miners.length === 0}
          <div class="loading-miners">Loading miners...</div>
        {:else}
          <div class="miner-list">
            {#each miners.slice(0, 10) as miner}
              <button
                class="miner-row"
                class:selected={selectedMiner?.address === miner.address}
                on:click={() => selectMiner(miner)}
              >
                <div class="miner-rank">#{miner.rank}</div>
                <div class="miner-info">
                  <div class="miner-name">
                    {miner.moniker || shortAddr(miner.address)}
                  </div>
                  <div class="miner-addr">{shortAddr(miner.address)}</div>
                </div>
                <div class="miner-stats">
                  <span class="stat-jobs">{miner.submit_job_result.toLocaleString()} jobs</span>
                  {#if miner.uptime !== null}
                    <span class="stat-uptime">{miner.uptime === 100 ? '✓ 100%' : `~ ${miner.uptime}%`}</span>
                  {/if}
                </div>
                {#if selectedMiner?.address === miner.address}
                  <div class="selected-tick">✓</div>
                {/if}
              </button>
            {/each}
          </div>
        {/if}

        {#if selectedMiner}
          <div class="selected-preview">
            <span class="selected-label">Selected:</span>
            <span class="selected-name">{selectedMiner.moniker || shortAddr(selectedMiner.address)}</span>
          </div>
        {/if}
        {#if selectedMiner}
  {@const minerJobs = jobHistory.filter(j => j.miner_address === selectedMiner.address)}
  {#if minerJobs.length > 0}
    <div class="miner-history">
      <div class="card-label">JOBS SENT TO THIS MINER</div>
      {#each minerJobs.slice(0, 5) as job}
        <div class="history-row">
          <span class="history-id">Job #{job.chain_job_id || job.id}</span>
{#if job.result_txhash}
  <a href="https://explorer.vinjan-inc.com/republic-testnet/tx/{job.result_txhash}" 
     target="_blank" class="explorer-link">🔍</a>
{:else if job.txhash}
  <a href="https://explorer.vinjan-inc.com/republic-testnet/tx/{job.txhash}" 
     target="_blank" class="explorer-link">🔍</a>
{/if}
<span class="history-status 
            {job.chainStatus === 'completed' ? 'done' : 
 job.chainStatus === 'pending_validation' ? 'done' :
 job.chainStatus === 'waiting_result' ? 'mining' : 'pending'}">
            {job.chainStatus === 'pending_validation' ? '✅ PendingValidation' :
job.chainStatus === 'completed' ? '✅ Complete' :
             job.chainStatus === 'waiting_result' ? '⚙️ Mining' :
             job.chainStatus === 'submitting' ? '📡 Submitting' :
             '⏳ Pending'}
          </span>
          <span class="history-time">
            {job.submitted_at ? new Date(job.submitted_at).toLocaleTimeString() : ''}
          </span>
        </div>
      {/each}
      <div class="history-total">Total: {minerJobs.length} jobs sent</div>
    </div>
  {/if}
{/if}
      </div>
    </div>

    <!-- Submit Button -->
    <div class="submit-row">
      <button
        class="submit-btn"
        class:ready={prompt.trim() && selectedMiner}
        disabled={!prompt.trim() || !selectedMiner}
        on:click={submitJob}
      >
        {#if !selectedMiner}
          Select a miner first
        {:else if !prompt.trim()}
          Write a prompt first
        {:else}
          ⚡ Submit Job to {selectedMiner.moniker || shortAddr(selectedMiner.address)}
        {/if}
      </button>
    </div>

  {:else}
    <!-- STATUS / RESULT VIEW -->
    <div class="status-view">

      <!-- Progress Steps -->
      <div class="progress-track">
        {#each [
          { n: 1, label: 'Submit' },
          { n: 2, label: 'Broadcast' },
          { n: 3, label: 'Mining' },
          { n: 4, label: 'Fetching' },
          { n: 5, label: 'Done' }
        ] as s}
          <div class="progress-step"
            class:active={progressStep === s.n}
            class:done={progressStep > s.n}
            class:error-step={isFailed && s.n === 5}
          >
            <div class="step-dot">
              {#if progressStep > s.n}✓
              {:else if isFailed && s.n === 5}✗
              {:else}{s.n}{/if}
            </div>
            <div class="step-label">{s.label}</div>
          </div>
          {#if s.n < 5}
            <div class="step-line" class:filled={progressStep > s.n}></div>
          {/if}
        {/each}
      </div>

      <!-- Status Card -->
      <div class="card status-card" class:success={isSuccess} class:failed={isFailed}>

        <div class="status-header">
          <div class="status-label">
            {jobStatus ? (STATUS_LABELS[jobStatus.status] || jobStatus.status) : '⏳ Initializing...'}
          </div>
          {#if !isSuccess && !isFailed}
            <div class="pulse-dot"></div>
          {/if}
        </div>

        <!-- Job details -->
        {#if trackingId}
          <div class="job-details">
            <div class="detail-row">
              <span class="detail-key">Tracking ID</span>
              <span class="detail-val mono">{trackingId}</span>
            </div>
            {#if jobStatus?.txhash}
              <div class="detail-row">
                <span class="detail-key">TX Hash</span>
                <span class="detail-val mono small">{jobStatus.txhash.slice(0, 20)}...</span>
              </div>
            {/if}
            {#if jobStatus?.chain_job_id}
              <div class="detail-row">
                <span class="detail-key">Chain Job ID</span>
                <span class="detail-val mono">{jobStatus.chain_job_id}</span>
              </div>
            {/if}
            {#if jobStatus?.result_url}
              <div class="detail-row">
                <span class="detail-key">Result URL</span>
                <span class="detail-val mono small">{jobStatus.result_url}</span>
              </div>
            {/if}
            <div class="detail-row">
              <span class="detail-key">Miner</span>
              <span class="detail-val">{selectedMiner?.moniker || shortAddr(selectedMiner?.address)}</span>
            </div>
            <div class="detail-row">
              <span class="detail-key">Prompt</span>
              <span class="detail-val">{prompt.slice(0, 60)}{prompt.length > 60 ? '...' : ''}</span>
            </div>
          </div>
        {/if}

        <!-- RESULT -->
        {#if isSuccess && jobStatus?.result}
          <div class="result-box">
           <div class="result-label">✅ JOB SUCCESSFULLY SENT!</div>
<div class="result-content">
  <p>Job <strong>{jobStatus?.chain_job_id}</strong> sent to <strong>{selectedMiner?.moniker || shortAddr(selectedMiner?.address)}</strong>!</p>
  <br/>
  <p>📋 <strong>Miner needs to run these commands:</strong></p>
  <br/>
  <p><strong>Step 1 — Pick up job:</strong></p>
  <code>echo "{jobStatus?.chain_job_id}" > /root/job_1.txt</code>
  <br/><br/>
  <p><strong>Step 2 — Submit result:</strong></p>
  <code>SHA=$(sha256sum /root/result_{jobStatus?.chain_job_id}.json | awk '&#123;print $1&#125;')<br/>
republicd tx computevalidation submit-job-result {jobStatus?.chain_job_id} http://YOUR_IP:8080/result_{jobStatus?.chain_job_id}.json example-verification:latest $SHA --from YOUR_WALLET --chain-id raitestnet_77701-1 --fees 200000000000000arai --node tcp://localhost:26657 -y</code>
  <br/><br/>
  <p><strong>Step 3 — Verify:</strong></p>
  <code>republicd query computevalidation job {jobStatus?.chain_job_id} --node tcp://localhost:26657 -o json | jq '.job.status'</code>
</div>
<button class="copy-btn" on:click={() => {
  const text = `Job ID: ${jobStatus?.chain_job_id}\necho "${jobStatus?.chain_job_id}" > /root/job_1.txt`;
  navigator.clipboard.writeText(text);
}}>📋 Copy Commands</button>
          </div>
        {/if}

        <!-- ERROR -->
        {#if isFailed && jobStatus?.error}
          <div class="error-box">
            <div class="error-label">Error Details</div>
            <div class="error-content">{jobStatus.error}</div>
          </div>
        {/if}

      </div>

      <!-- Actions -->
      {#if step === 'done'}
        <div class="done-actions">
          <button class="action-btn primary" on:click={reset}>⚡ Submit Another Job</button>
          {#if isSuccess}
            <button class="action-btn secondary" on:click={() => {
              const text = `Just sent an AI job to a Republic miner via @republicstats browser-native job submitter! 🚀\n\nWorld's first browser-native AI job submission on Republic testnet.\n\ntry it: republicstats.xyz/submit`;
              window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`);
            }}>🐦 Share on X</button>
          {/if}
        </div>
      {/if}

    </div>
  {/if}

  <!-- Info footer -->
  <div class="info-bar">
    <span>⚡ Jobs submitted via Republic AI testnet</span>
    <span>•</span>
    <span>Chain: raitestnet_77701-1</span>
    <span>•</span>
    <span>Pool: 1.6M pts/week</span>
  </div>
</div>

<style>
  .submit-page {
    max-width: 1100px;
    margin: 0 auto;
    padding: 2rem 1.5rem 4rem;
    font-family: var(--font-mono, 'JetBrains Mono', monospace);
  }

  /* ── Header ── */
  .page-header {
    text-align: center;
    margin-bottom: 2.5rem;
  }
  .header-badge {
    display: inline-block;
    background: var(--accent, #f97316);
    color: #000;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    padding: 0.25rem 0.75rem;
    border-radius: 2px;
    margin-bottom: 0.75rem;
  }
  .page-title {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text, #e2e8f0);
    margin: 0 0 0.5rem;
  }
  .page-subtitle {
    color: var(--text-muted, #94a3b8);
    font-size: 0.9rem;
    margin: 0;
  }

  /* ── Cards ── */
  .card {
    background: var(--card-bg, #0f172a);
    border: 1px solid var(--border, #1e293b);
    border-radius: 8px;
    padding: 1.5rem;
  }
  .card-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    color: var(--accent, #f97316);
    margin-bottom: 1rem;
  }

  /* ── Layout ── */
  .submit-layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }
  @media (max-width: 768px) {
    .submit-layout { grid-template-columns: 1fr; }
  }

  /* ── Prompt ── */
  .prompt-input {
    width: 100%;
    background: var(--input-bg, #020617);
    border: 1px solid var(--border, #1e293b);
    border-radius: 6px;
    color: var(--text, #e2e8f0);
    font-family: inherit;
    font-size: 0.9rem;
    padding: 0.875rem;
    resize: vertical;
    outline: none;
    box-sizing: border-box;
    transition: border-color 0.2s;
  }
  .prompt-input:focus {
    border-color: var(--accent, #f97316);
  }
  .char-count {
    text-align: right;
    font-size: 0.7rem;
    color: var(--text-muted, #94a3b8);
    margin-top: 0.4rem;
    margin-bottom: 1rem;
  }
  .job-meta {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    border-top: 1px solid var(--border, #1e293b);
    padding-top: 1rem;
  }
  .meta-item {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
  }
  .meta-label { color: var(--text-muted, #94a3b8); }
  .meta-value { color: var(--text, #e2e8f0); }

  /* ── Miner List ── */
  .miner-list {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    max-height: 320px;
    overflow-y: auto;
    margin-bottom: 1rem;
  }
  .miner-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: var(--input-bg, #020617);
    border: 1px solid var(--border, #1e293b);
    border-radius: 6px;
    padding: 0.625rem 0.875rem;
    cursor: pointer;
    transition: all 0.15s;
    text-align: left;
    width: 100%;
    color: var(--text, #e2e8f0);
  }
  .miner-row:hover {
    border-color: var(--accent, #f97316);
    background: rgba(249, 115, 22, 0.05);
  }
  .miner-row.selected {
    border-color: var(--accent, #f97316);
    background: rgba(249, 115, 22, 0.1);
  }
  .miner-rank {
    font-size: 0.7rem;
    color: var(--text-muted, #94a3b8);
    min-width: 24px;
  }
  .miner-info { flex: 1; min-width: 0; }
  .miner-name {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text, #e2e8f0);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .miner-addr {
    font-size: 0.7rem;
    color: var(--text-muted, #94a3b8);
  }
  .miner-stats {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.2rem;
  }
  .stat-jobs {
    font-size: 0.7rem;
    color: var(--accent, #f97316);
  }
  .stat-uptime {
    font-size: 0.65rem;
    color: #22c55e;
  }
  .selected-tick {
    color: var(--accent, #f97316);
    font-weight: 700;
    font-size: 0.9rem;
  }
  .selected-preview {
    background: rgba(249, 115, 22, 0.08);
    border: 1px solid rgba(249, 115, 22, 0.3);
    border-radius: 4px;
    padding: 0.5rem 0.75rem;
    font-size: 0.8rem;
  }
  .selected-label { color: var(--text-muted, #94a3b8); margin-right: 0.5rem; }
  .selected-name  { color: var(--accent, #f97316); font-weight: 600; }
  .loading-miners { color: var(--text-muted, #94a3b8); font-size: 0.85rem; padding: 1rem 0; }

  /* ── Submit Button ── */
  .submit-row { display: flex; justify-content: center; }
  .submit-btn {
    background: var(--border, #1e293b);
    border: 1px solid var(--border, #1e293b);
    border-radius: 6px;
    color: var(--text-muted, #94a3b8);
    font-family: inherit;
    font-size: 0.95rem;
    font-weight: 600;
    padding: 0.875rem 2.5rem;
    cursor: not-allowed;
    transition: all 0.2s;
    letter-spacing: 0.02em;
  }
  .submit-btn.ready {
    background: var(--accent, #f97316);
    border-color: var(--accent, #f97316);
    color: #000;
    cursor: pointer;
  }
  .submit-btn.ready:hover {
    background: #ea6c0a;
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(249, 115, 22, 0.4);
  }

  /* ── Status View ── */
  .status-view { max-width: 680px; margin: 0 auto; }

  /* Progress Track */
  .progress-track {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 2rem;
    gap: 0;
  }
  .progress-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.4rem;
  }
  .step-dot {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: 2px solid var(--border, #1e293b);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    color: var(--text-muted, #94a3b8);
    transition: all 0.3s;
  }
  .progress-step.done .step-dot {
    background: #22c55e;
    border-color: #22c55e;
    color: #000;
  }
  .progress-step.active .step-dot {
    background: var(--accent, #f97316);
    border-color: var(--accent, #f97316);
    color: #000;
    animation: pulse-dot 1s ease-in-out infinite;
  }
  .progress-step.error-step .step-dot {
    background: #ef4444;
    border-color: #ef4444;
    color: #fff;
  }
  .step-label {
    font-size: 0.65rem;
    color: var(--text-muted, #94a3b8);
    letter-spacing: 0.05em;
  }
  .step-line {
    height: 2px;
    width: 48px;
    background: var(--border, #1e293b);
    margin-bottom: 1.2rem;
    transition: background 0.3s;
  }
  .step-line.filled { background: #22c55e; }

  @keyframes pulse-dot {
    0%, 100% { box-shadow: 0 0 0 0 rgba(249,115,22,0.4); }
    50%       { box-shadow: 0 0 0 6px rgba(249,115,22,0); }
  }

  /* Status Card */
  .status-card { transition: border-color 0.3s; }
  .status-card.success { border-color: #22c55e; }
  .status-card.failed  { border-color: #ef4444; }

  .status-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.25rem;
  }
  .status-label {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text, #e2e8f0);
  }
  .pulse-dot {
    width: 10px;
    height: 10px;
    background: var(--accent, #f97316);
    border-radius: 50%;
    animation: pulse-dot 1s ease-in-out infinite;
  }

  /* Job Details */
  .job-details {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1.25rem;
    padding-bottom: 1.25rem;
    border-bottom: 1px solid var(--border, #1e293b);
  }
  .detail-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.78rem;
    gap: 1rem;
  }
  .detail-key { color: var(--text-muted, #94a3b8); }
  .detail-val { color: var(--text, #e2e8f0); text-align: right; }
  .detail-val.mono { font-family: inherit; }
  .detail-val.small { font-size: 0.7rem; }

  /* Result Box */
  .result-box {
    background: rgba(34, 197, 94, 0.05);
    border: 1px solid rgba(34, 197, 94, 0.2);
    border-radius: 6px;
    padding: 1rem;
    margin-top: 1rem;
  }
  .result-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #22c55e;
    margin-bottom: 0.75rem;
  }
  .result-content {
    font-size: 0.875rem;
    color: var(--text, #e2e8f0);
    line-height: 1.6;
    white-space: pre-wrap;
    max-height: 300px;
    overflow-y: auto;
  }
  .copy-btn {
    margin-top: 0.75rem;
    background: transparent;
    border: 1px solid rgba(34, 197, 94, 0.3);
    border-radius: 4px;
    color: #22c55e;
    font-family: inherit;
    font-size: 0.75rem;
    padding: 0.35rem 0.75rem;
    cursor: pointer;
    transition: all 0.15s;
  }
  .copy-btn:hover {
    background: rgba(34, 197, 94, 0.1);
  }

  /* Error Box */
  .error-box {
    background: rgba(239, 68, 68, 0.05);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: 6px;
    padding: 1rem;
    margin-top: 1rem;
  }
  .error-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #ef4444;
    margin-bottom: 0.5rem;
  }
  .error-content {
    font-size: 0.8rem;
    color: #fca5a5;
    white-space: pre-wrap;
  }

  /* Done Actions */
  .done-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-top: 1.5rem;
  }
  .action-btn {
    font-family: inherit;
    font-size: 0.875rem;
    font-weight: 600;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .action-btn.primary {
    background: var(--accent, #f97316);
    border: none;
    color: #000;
  }
  .action-btn.primary:hover {
    background: #ea6c0a;
    transform: translateY(-1px);
  }
  .action-btn.secondary {
    background: transparent;
    border: 1px solid var(--border, #1e293b);
    color: var(--text, #e2e8f0);
  }
  .action-btn.secondary:hover {
    border-color: var(--text-muted, #94a3b8);
  }

  /* Info Bar */
  .info-bar {
    display: flex;
    gap: 0.75rem;
    justify-content: center;
    align-items: center;
    margin-top: 3rem;
    font-size: 0.72rem;
    color: var(--text-muted, #94a3b8);
    flex-wrap: wrap;
  }
  .miner-history {
  margin-top: 1rem;
  border-top: 1px solid var(--border, #1e293b);
  padding-top: 1rem;
}
.history-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.4rem 0;
  font-size: 0.78rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.history-id {
  color: var(--accent, #f97316);
  font-weight: 600;
}
.history-status {
  font-size: 0.72rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}
.history-status.done { 
  background: rgba(34,197,94,0.1); 
  color: #22c55e; 
}
.history-status.mining { 
  background: rgba(249,115,22,0.1); 
  color: #f97316; 
}
.history-status.pending { 
  background: rgba(148,163,184,0.1); 
  color: #94a3b8; 
}
.history-time {
  color: var(--text-muted, #94a3b8);
  font-size: 0.7rem;
}
.history-total {
  font-size: 0.72rem;
  color: var(--text-muted, #94a3b8);
  margin-top: 0.5rem;
  text-align: right;
}
.explorer-link {
  color: var(--accent, #f97316);
  font-size: 0.7rem;
  text-decoration: none;
}
.explorer-link:hover { text-decoration: underline; }
</style>

