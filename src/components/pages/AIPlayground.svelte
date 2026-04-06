<script>
  import { onMount } from 'svelte';
  import { API, fmt, shortAddr } from '../../stores/app.js';

  let prompt = '';
  let loading = false;
  let result = null;
  let error = '';
  let trackingId = null;
  let pollInterval;
  let miners = [];
  let selectedMiner = null;

  async function loadMiners() {
    try {
      const r = await fetch(`${API}/api/leaderboard?limit=200`);
      const d = await r.json();
      miners = (d.data || []).filter(m => m.submit_job_result > 0);
    } catch(e) {}
  }

  async function submitJob() {
    if (!prompt.trim()) return;
    loading = true;
    error = '';
    result = null;

    try {
      const r = await fetch(`${API}/api/hyperscale/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: prompt.trim(),
          miner_address: selectedMiner?.address || ''
        })
      });
      const d = await r.json();
      if (!d.success) throw new Error(d.error || 'Failed');
      trackingId = d.tracking_id;
      pollInterval = setInterval(pollStatus, 3000);
    } catch(e) {
      error = e.message;
      loading = false;
    }
  }

  async function pollStatus() {
    if (!trackingId) return;
    try {
      const r = await fetch(`${API}/api/hyperscale/status/${trackingId}`);
      const d = await r.json();
      if (d.status === 'completed' || d.status === 'inferred_only' || d.status === 'failed') {
        clearInterval(pollInterval);
        result = d;
        loading = false;
      }
    } catch(e) {}
  }

  function reset() {
    result = null;
    error = '';
    trackingId = null;
    prompt = '';
    loading = false;
    selectedMiner = null;
  }

  onMount(() => { loadMiners(); });
</script>

<div class="hero">
  <div class="hero-bg"></div>
  <div style="position:relative;z-index:1">
    <div class="hero-eyebrow"><span class="hero-eyebrow-dot"></span>Republic AI · Hyperscale Jobs</div>
    <h1><span class="line1">HYPERSCALE</span><span class="line2">JOBS</span></h1>
    <p class="hero-sub">Submit AI inference jobs powered by Hyperscale SDK — recorded on Republic AI chain</p>
  </div>
</div>

<div style="max-width:800px;margin:0 auto;padding:0 28px 60px">

  <!-- HOW IT WORKS -->
  <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin-bottom:28px">
    <div style="font-family:var(--font-mono);font-size:11px;color:var(--accent);letter-spacing:2px;margin-bottom:12px">HOW IT WORKS</div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;text-align:center">
      <div>
        <div style="font-size:24px;margin-bottom:8px">⚡</div>
        <div style="font-size:13px;font-weight:600;margin-bottom:4px">1. Submit Prompt</div>
        <div style="font-size:11px;color:var(--muted)">Your query sent to Hyperscale SDK</div>
      </div>
      <div>
        <div style="font-size:24px;margin-bottom:8px">🤖</div>
        <div style="font-size:13px;font-weight:600;margin-bottom:4px">2. AI Inference</div>
        <div style="font-size:11px;color:var(--muted)">DeepSeek processes via Hyperscale SDK</div>
      </div>
      <div>
        <div style="font-size:24px;margin-bottom:8px">⛓️</div>
        <div style="font-size:13px;font-weight:600;margin-bottom:4px">3. On-Chain Record</div>
        <div style="font-size:11px;color:var(--muted)">Result submitted to Republic chain</div>
      </div>
    </div>
  </div>

  <!-- INPUT -->
  {#if !result}
    <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:24px">

      <!-- MINER SELECT -->
      <div style="margin-bottom:20px">
        <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-bottom:8px;letter-spacing:1px">SELECT MINER</div>
        {#if miners.length === 0}
          <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted)">Loading miners...</div>
        {:else}
          <select
            bind:value={selectedMiner}
            style="width:100%;background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:10px 14px;color:var(--text);font-family:var(--font-mono);font-size:11px;outline:none;cursor:pointer">
            <option value={null} style="background:#0D0D1A;color:#E8E8F0">— Auto (any available miner)</option>
            {#each miners as miner}
              <option value={miner} style="background:#0D0D1A;color:#E8E8F0">
                {miner.moniker || shortAddr(miner.address)} · {fmt(miner.submit_job_result)} results
              </option>
            {/each}
          </select>
          {#if selectedMiner}
            <div style="margin-top:8px;font-family:var(--font-mono);font-size:10px;color:var(--muted)">
              Selected: <span style="color:var(--accent)">{selectedMiner.moniker || shortAddr(selectedMiner.address)}</span>
              &nbsp;·&nbsp; {fmt(selectedMiner.submit_job_result)} results
              &nbsp;·&nbsp; Uptime: {selectedMiner.uptime ? selectedMiner.uptime + '%' : '—'}
            </div>
          {/if}
        {/if}
      </div>

      <!-- PROMPT -->
      <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-bottom:12px;letter-spacing:1px">ENTER YOUR PROMPT</div>
      <textarea
        bind:value={prompt}
        placeholder="Ask anything... e.g. What is Republic AI? How does GPU mining work?"
        disabled={loading}
        style="width:100%;background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:14px;color:var(--text);font-family:var(--font-mono);font-size:13px;resize:vertical;min-height:120px;outline:none;line-height:1.6"
      ></textarea>

      {#if error}
        <div class="error-msg" style="margin-top:12px">{error}</div>
      {/if}

      {#if loading}
        <div style="margin-top:20px;text-align:center">
          <div style="background:#0A0A12;border:1px solid #1E1E2A;color:#4ADE80;font-family:'Courier New',monospace;font-size:12px;padding:32px 16px 16px;border-radius:4px;position:relative;display:inline-block;min-width:220px">
            <div style="position:absolute;top:0;left:0;right:0;height:24px;background:#141420;border-radius:4px 4px 0 0;display:flex;align-items:center;padding:0 8px">
              <span style="font-size:9px;color:#666;letter-spacing:1px">hyperscale_sdk</span>
              <div style="margin-left:auto;display:flex;gap:4px">
                <div style="width:8px;height:8px;border-radius:50%;background:#E35353"></div>
                <div style="width:8px;height:8px;border-radius:50%;background:#E3C853"></div>
                <div style="width:8px;height:8px;border-radius:50%;background:#53E3A6"></div>
              </div>
            </div>
            <div style="font-size:12px">Processing inference...</div>
          </div>
          <div style="font-size:12px;color:var(--muted);margin-top:12px">
            {selectedMiner ? `Sending to ${selectedMiner.moniker || shortAddr(selectedMiner.address)}...` : 'Submitting to Republic chain after inference (~30s)'}
          </div>
        </div>
      {:else}
        <button
          on:click={submitJob}
          disabled={!prompt.trim()}
          style="margin-top:16px;background:var(--accent);color:#000;border:none;padding:13px 36px;font-family:var(--font-display);font-size:20px;letter-spacing:1px;border-radius:8px;cursor:pointer;opacity:{prompt.trim() ? 1 : 0.5}">
          ⚡ SUBMIT JOB
        </button>
      {/if}
    </div>
  {/if}

  <!-- RESULT -->
  {#if result}
    <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;overflow:hidden">
      <!-- Status bar -->
      <div style="padding:14px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between">
        <div style="display:flex;align-items:center;gap:10px">
          <div style="width:8px;height:8px;border-radius:50%;background:{result.status === 'completed' ? '#4ADE80' : result.status === 'failed' ? '#EF4444' : 'var(--accent)'}"></div>
          <span style="font-family:var(--font-mono);font-size:11px;color:var(--muted)">
            {result.status === 'completed' ? '✅ Completed & On-Chain' : result.status === 'inferred_only' ? '⚡ Inferred (Chain pending)' : '❌ Failed'}
          </span>
        </div>
        <button on:click={reset} style="background:transparent;border:1px solid var(--border);color:var(--muted);padding:5px 12px;font-family:var(--font-mono);font-size:10px;cursor:pointer;border-radius:4px">
          ↩ New Job
        </button>
      </div>

      <!-- Prompt -->
      <div style="padding:16px 20px;border-bottom:1px solid var(--border);background:rgba(255,107,0,0.03)">
        <div style="font-family:var(--font-mono);font-size:10px;color:var(--accent);margin-bottom:6px;letter-spacing:1px">PROMPT</div>
        <div style="font-size:14px;color:var(--muted)">{result.prompt}</div>
      </div>

      <!-- AI Response -->
      <div style="padding:20px">
        <div style="font-family:var(--font-mono);font-size:10px;color:var(--accent);margin-bottom:10px;letter-spacing:1px">AI RESPONSE</div>
        <div style="font-size:14px;line-height:1.8;color:var(--text);white-space:pre-wrap">{result.result?.content || result.error}</div>
      </div>

      <!-- Chain Info -->
      {#if result.txhash}
        <div style="padding:16px 20px;border-top:1px solid var(--border);background:rgba(0,0,0,0.2)">
          <div style="font-family:var(--font-mono);font-size:10px;color:var(--accent);margin-bottom:8px;letter-spacing:1px">ON-CHAIN PROOF</div>
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px">
            <div>
              <div style="font-size:10px;color:var(--muted);margin-bottom:4px">TX HASH</div>
              <div style="font-family:var(--font-mono);font-size:10px;color:var(--accent3);word-break:break-all">{result.txhash}</div>
            </div>
            <div>
              <div style="font-size:10px;color:var(--muted);margin-bottom:4px">HYPERSCALE JOB ID</div>
              <div style="font-family:var(--font-mono);font-size:10px;color:var(--accent3);word-break:break-all">{result.result?.hyperscale_job_id || '—'}</div>
            </div>
            <div>
              <div style="font-size:10px;color:var(--muted);margin-bottom:4px">COST</div>
              <div style="font-family:var(--font-mono);font-size:12px;color:var(--accent)">{result.result?.cost?.toFixed(6)} RAI</div>
            </div>
          </div>
          <div style="margin-top:12px;display:flex;align-items:center;gap:16px">
            <a href={result.explorer} target="_blank" rel="noopener"
              style="color:var(--blue);font-family:var(--font-mono);font-size:11px">
              View on Explorer ↗
            </a>
            <span style="font-family:var(--font-mono);font-size:10px;color:var(--muted)">
              Verified by: {result.result?.verified_by || 'Hyperscale SDK + Republic AI Chain'}
            </span>
          </div>
        </div>
      {/if}
    </div>
  {/if}

</div>