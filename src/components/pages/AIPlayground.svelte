<script>
  import { onMount } from 'svelte';
  import { API, fmt, shortAddr } from '../../stores/app.js';
  import { marked } from 'marked';

  const CHAIN_ID = 'raitestnet_77701-1';
  const RPC = 'https://rpc-test.republic.vinjan-inc.com';
  const REST = 'https://api-test.republic.vinjan-inc.com';
  const TREASURY = 'rai1alt2884lvwzlzg6l03eaplry7a0ytx0wf3k889';
  const FEE_RAI = 5;
  const FEE_ARAI = '5000000000000000000';

  let prompt = '';
  let loading = false;
  let result = null;
  let error = '';
  let trackingId = null;
  let pollInterval;
  let miners = [];
  let selectedMiner = null;
  let models = [];
  let selectedModel = 'nex-agi/deepseek-v3.1-nex-n1';
  let modelsLoading = true;
  let modelSearch = '';
  let walletAddress = '';
  let walletConnected = false;
  let walletBalance = '';
  let payLoading = false;
  let payError = '';
  let payTxHash = '';
  let step = 1; // 1=connect, 2=configure, 3=pay, 4=result

  $: filteredModels = models.filter(m =>
    m.id.toLowerCase().includes(modelSearch.toLowerCase()) ||
    m.name.toLowerCase().includes(modelSearch.toLowerCase())
  );

  async function loadMiners() {
    try {
      const r = await fetch(`${API}/api/leaderboard?limit=200`);
      const d = await r.json();
      miners = (d.data || []).filter(m => m.submit_job_result > 0);
    } catch(e) {}
  }

  async function loadModels() {
    modelsLoading = true;
    try {
      const r = await fetch(`${API}/api/hyperscale/models`);
      models = await r.json();
    } catch(e) {}
    modelsLoading = false;
  }

  async function connectWallet() {
    payError = '';
    try {
      if (!window.keplr) {
        payError = 'Keplr wallet not found! Please install Keplr extension.';
        return;
      }
      await window.keplr.enable(CHAIN_ID);
      const key = await window.keplr.getKey(CHAIN_ID);
      walletAddress = key.bech32Address;
      walletConnected = true;
      step = 2;
      await fetchBalance();
    } catch(e) {
      payError = 'Failed to connect: ' + e.message;
    }
  }

  async function fetchBalance() {
    try {
      const r = await fetch(`${REST}/cosmos/bank/v1beta1/balances/${walletAddress}`);
      const d = await r.json();
      const arai = d.balances?.find(b => b.denom === 'arai');
      if (arai) {
        const rai = (BigInt(arai.amount) / BigInt('1000000000000000000')).toString();
        const decimal = (BigInt(arai.amount) % BigInt('1000000000000000000')).toString().padStart(18, '0').slice(0, 4);
        walletBalance = `${rai}.${decimal} RAI`;
      } else {
        walletBalance = '0 RAI';
      }
    } catch(e) {
      walletBalance = '—';
    }
  }

  async function payAndSubmit() {
    if (!prompt.trim()) { payError = 'Please enter a prompt first'; return; }
    payLoading = true;
    payError = '';
    payTxHash = '';

    try {
      if (!window.keplr) throw new Error('Keplr not found');
      await window.keplr.enable(CHAIN_ID);

      // Load cosmjs from CDN
      const cosmjs = await import('https://cdn.jsdelivr.net/npm/@cosmjs/stargate@0.29.5/+esm');
const SigningStargateClient = cosmjs.SigningStargateClient;
const GasPrice = cosmjs.GasPrice;

      const offlineSigner = window.keplr.getOfflineSigner(CHAIN_ID);

      const client = await SigningStargateClient.connectWithSigner(
        RPC,
        offlineSigner,
        { gasPrice: GasPrice.fromString('25000000000arai') }
      );

      const memo = `RepublicStats Hyperscale Job | ${prompt.slice(0, 40)}`;

      const result = await client.sendTokens(
        walletAddress,
        TREASURY,
        [{ denom: 'arai', amount: FEE_ARAI }],
        { amount: [{ denom: 'arai', amount: '8000000000000000' }], gas: '200000' },
        memo
      );

      if (result.code !== 0) throw new Error('TX failed: ' + result.rawLog);

      payTxHash = result.transactionHash;
      step = 3;
      await fetchBalance();

      // Now submit inference job
      loading = true;
      const r = await fetch(`${API}/api/hyperscale/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: prompt.trim(),
          miner_address: selectedMiner?.address || '',
          model: selectedModel,
          payment_txhash: payTxHash,
          payer_address: walletAddress
        })
      });
      const d = await r.json();
      if (!d.success) throw new Error(d.error || 'Failed');
      trackingId = d.tracking_id;
      pollInterval = setInterval(pollStatus, 3000);

    } catch(e) {
      payError = 'Error: ' + e.message;
      payLoading = false;
      loading = false;
    }
    payLoading = false;
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
        step = 4;
      }
    } catch(e) {}
  }

  function reset() {
    result = null;
    error = '';
    payError = '';
    payTxHash = '';
    trackingId = null;
    prompt = '';
    loading = false;
    selectedMiner = null;
    selectedModel = 'nex-agi/deepseek-v3.1-nex-n1';
    step = walletConnected ? 2 : 1;
  }

  function disconnectWallet() {
    walletAddress = '';
    walletConnected = false;
    walletBalance = '';
    step = 1;
    reset();
  }

  $: selectedModelInfo = models.find(m => m.id === selectedModel);

  onMount(() => { loadMiners(); loadModels(); });
</script>

<div class="hero">
  <div class="hero-bg"></div>
  <div style="position:relative;z-index:1">
    <div class="hero-eyebrow"><span class="hero-eyebrow-dot"></span>Republic AI · Hyperscale Jobs</div>
    <h1><span class="line1">HYPERSCALE</span><span class="line2">JOBS</span></h1>
    <p class="hero-sub">Submit AI inference jobs powered by Hyperscale SDK — pay 5 RAI per job, recorded on-chain</p>
  </div>
</div>

<div style="max-width:800px;margin:0 auto;padding:0 28px 60px">

  <!-- HOW IT WORKS -->
  <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin-bottom:28px">
    <div style="font-family:var(--font-mono);font-size:11px;color:var(--accent);letter-spacing:2px;margin-bottom:12px">HOW IT WORKS</div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;text-align:center">
      <div style="opacity:{step >= 1 ? 1 : 0.4}">
        <div style="font-size:20px;margin-bottom:6px">🔗</div>
        <div style="font-size:12px;font-weight:600;margin-bottom:3px;color:{step === 1 ? 'var(--accent)' : 'var(--text)'}">1. Connect</div>
        <div style="font-size:10px;color:var(--muted)">Keplr wallet</div>
      </div>
      <div style="opacity:{step >= 2 ? 1 : 0.4}">
        <div style="font-size:20px;margin-bottom:6px">⚙️</div>
        <div style="font-size:12px;font-weight:600;margin-bottom:3px;color:{step === 2 ? 'var(--accent)' : 'var(--text)'}">2. Configure</div>
        <div style="font-size:10px;color:var(--muted)">Model + prompt</div>
      </div>
      <div style="opacity:{step >= 3 ? 1 : 0.4}">
        <div style="font-size:20px;margin-bottom:6px">💸</div>
        <div style="font-size:12px;font-weight:600;margin-bottom:3px;color:{step === 3 ? 'var(--accent)' : 'var(--text)'}">3. Pay 5 RAI</div>
        <div style="font-size:10px;color:var(--muted)">On-chain payment</div>
      </div>
      <div style="opacity:{step >= 4 ? 1 : 0.4}">
        <div style="font-size:20px;margin-bottom:6px">🤖</div>
        <div style="font-size:12px;font-weight:600;margin-bottom:3px;color:{step === 4 ? 'var(--accent)' : 'var(--text)'}">4. Get Result</div>
        <div style="font-size:10px;color:var(--muted)">AI response</div>
      </div>
    </div>
  </div>

  <!-- STEP 1: CONNECT WALLET -->
  {#if step === 1}
    <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:40px 24px;text-align:center">
      <div style="font-size:48px;margin-bottom:16px">🔗</div>
      <h2 style="font-family:var(--font-display);font-size:28px;letter-spacing:2px;color:var(--accent);margin-bottom:8px">CONNECT WALLET</h2>
      <p style="color:var(--muted);font-size:13px;margin-bottom:28px">Connect your Keplr wallet to pay 5 RAI per inference job</p>
      {#if payError}
        <div class="error-msg" style="margin-bottom:16px">{payError}</div>
      {/if}
      <button on:click={connectWallet}
        style="background:var(--accent);color:#000;border:none;padding:14px 40px;font-family:var(--font-display);font-size:20px;letter-spacing:1px;border-radius:8px;cursor:pointer">
        ⚡ CONNECT KEPLR
      </button>
    </div>

  <!-- STEP 2: CONFIGURE -->
  {:else if step === 2}
    <!-- Wallet Info Bar -->
    <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:14px 20px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
      <div>
        <div style="font-family:var(--font-mono);font-size:10px;color:var(--muted);margin-bottom:2px">CONNECTED</div>
        <div style="font-family:var(--font-mono);font-size:11px;color:var(--accent)">{walletAddress}</div>
      </div>
      <div style="display:flex;align-items:center;gap:16px">
        <div>
          <div style="font-family:var(--font-mono);font-size:10px;color:var(--muted)">BALANCE</div>
          <div style="font-family:var(--font-mono);font-size:13px;color:var(--accent3)">{walletBalance}</div>
        </div>
        <button on:click={disconnectWallet}
          style="background:transparent;border:1px solid var(--border);color:var(--muted);padding:5px 12px;font-family:var(--font-mono);font-size:10px;cursor:pointer;border-radius:4px">
          Disconnect
        </button>
      </div>
    </div>

    <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:24px">

      <!-- MODEL SELECT -->
      <div style="margin-bottom:20px">
        <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-bottom:8px;letter-spacing:1px">
          SELECT MODEL <span style="color:var(--accent)">({models.length} available)</span>
        </div>
        {#if modelsLoading}
          <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted)">Loading models...</div>
        {:else}
          <input bind:value={modelSearch} placeholder="Search models... e.g. gpt, claude, llama"
            style="width:100%;background:var(--bg1);border:1px solid var(--border);border-radius:8px 8px 0 0;padding:8px 14px;color:var(--text);font-family:var(--font-mono);font-size:11px;outline:none;box-sizing:border-box"/>
          <select bind:value={selectedModel} size="4"
            style="width:100%;background:var(--bg1);border:1px solid var(--border);border-top:none;border-radius:0 0 8px 8px;padding:4px;color:var(--text);font-family:var(--font-mono);font-size:11px;outline:none;cursor:pointer">
            {#each filteredModels as model}
              <option value={model.id} style="background:#0D0D1A;color:#E8E8F0;padding:6px">
                {model.name} — {model.id}
              </option>
            {/each}
          </select>
          {#if selectedModelInfo}
            <div style="margin-top:8px;background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:10px 14px;display:flex;gap:16px;flex-wrap:wrap">
              <div><span style="font-size:10px;color:var(--muted)">MODEL: </span><span style="font-family:var(--font-mono);font-size:10px;color:var(--accent)">{selectedModel}</span></div>
              <div><span style="font-size:10px;color:var(--muted)">CONTEXT: </span><span style="font-family:var(--font-mono);font-size:10px;color:var(--accent3)">{selectedModelInfo.context_length?.toLocaleString() || '—'} tokens</span></div>
              <div><span style="font-size:10px;color:var(--muted)">PRICE: </span><span style="font-family:var(--font-mono);font-size:10px;color:var(--accent3)">{selectedModelInfo.pricing?.prompt === '0' ? '🆓 Free' : `$${parseFloat(selectedModelInfo.pricing?.prompt || 0) * 1000000}/M tokens`}</span></div>
            </div>
          {/if}
        {/if}
      </div>

      <!-- MINER SELECT -->
      <div style="margin-bottom:20px">
        <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-bottom:8px;letter-spacing:1px">SELECT MINER</div>
        <select bind:value={selectedMiner}
          style="width:100%;background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:10px 14px;color:var(--text);font-family:var(--font-mono);font-size:11px;outline:none;cursor:pointer">
          <option value={null} style="background:#0D0D1A;color:#E8E8F0">— Auto (any available miner)</option>
          {#each miners as miner}
            <option value={miner} style="background:#0D0D1A;color:#E8E8F0">
              {miner.moniker || shortAddr(miner.address)} · {fmt(miner.submit_job_result)} results
            </option>
          {/each}
        </select>
      </div>

      <!-- PROMPT -->
      <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-bottom:8px;letter-spacing:1px">ENTER YOUR PROMPT</div>
      <textarea bind:value={prompt} placeholder="Ask anything..." disabled={loading}
        style="width:100%;background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:14px;color:var(--text);font-family:var(--font-mono);font-size:13px;resize:vertical;min-height:120px;outline:none;line-height:1.6;box-sizing:border-box"></textarea>

      {#if payError}
        <div class="error-msg" style="margin-top:12px">{payError}</div>
      {/if}

      <!-- PAY BUTTON -->
      <div style="margin-top:20px;background:rgba(255,107,0,0.06);border:1px solid rgba(255,107,0,0.2);border-radius:10px;padding:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
        <div>
          <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-bottom:4px">PAYMENT REQUIRED</div>
          <div style="font-family:var(--font-display);font-size:22px;color:var(--accent);letter-spacing:1px">5 RAI</div>
          <div style="font-family:var(--font-mono);font-size:10px;color:var(--muted);margin-top:2px">Per inference job · On-chain proof</div>
        </div>
        <button on:click={payAndSubmit} disabled={payLoading || loading || !prompt.trim()}
          style="background:var(--accent);color:#000;border:none;padding:14px 32px;font-family:var(--font-display);font-size:20px;letter-spacing:1px;border-radius:8px;cursor:pointer;opacity:{(payLoading || loading || !prompt.trim()) ? 0.6 : 1}">
          {payLoading ? '⏳ APPROVING...' : loading ? '🤖 PROCESSING...' : '⚡ PAY & SUBMIT'}
        </button>
      </div>

      {#if loading}
        <div style="margin-top:16px;text-align:center">
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
          {#if payTxHash}
            <div style="margin-top:10px;font-family:var(--font-mono);font-size:10px;color:var(--muted)">
              Payment TX: <span style="color:var(--accent3)">{payTxHash.slice(0,16)}...</span>
            </div>
          {/if}
        </div>
      {/if}
    </div>

  <!-- STEP 4: RESULT -->
  {:else if step === 4 && result}
    <!-- Wallet bar -->
    <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:12px 20px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
      <div style="font-family:var(--font-mono);font-size:11px;color:var(--accent)">{walletAddress}</div>
      <div style="font-family:var(--font-mono);font-size:11px;color:var(--accent3)">{walletBalance}</div>
    </div>

    <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;overflow:hidden">
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

      <div style="padding:16px 20px;border-bottom:1px solid var(--border);background:rgba(255,107,0,0.03)">
        <div style="font-family:var(--font-mono);font-size:10px;color:var(--accent);margin-bottom:6px;letter-spacing:1px">PROMPT</div>
        <div style="font-size:14px;color:var(--muted)">{result.prompt}</div>
      </div>

      <div style="padding:20px">
        <div style="font-family:var(--font-mono);font-size:10px;color:var(--accent);margin-bottom:10px;letter-spacing:1px">AI RESPONSE</div>
        <div class="markdown-body">
          {@html marked(result.result?.content || result.error || '')}
        </div>
      </div>

      <div style="padding:16px 20px;border-top:1px solid var(--border);background:rgba(0,0,0,0.2)">
        <div style="font-family:var(--font-mono);font-size:10px;color:var(--accent);margin-bottom:8px;letter-spacing:1px">TRANSACTION PROOF</div>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:12px">
          <div>
            <div style="font-size:10px;color:var(--muted);margin-bottom:4px">PAYMENT TX</div>
            <div style="font-family:var(--font-mono);font-size:10px;color:var(--accent3);word-break:break-all">{payTxHash}</div>
          </div>
          <div>
            <div style="font-size:10px;color:var(--muted);margin-bottom:4px">INFERENCE TX</div>
            <div style="font-family:var(--font-mono);font-size:10px;color:var(--accent3);word-break:break-all">{result.txhash || '—'}</div>
          </div>
        </div>
        <div style="display:flex;gap:16px;flex-wrap:wrap">
          <div>
            <span style="font-size:10px;color:var(--muted)">COST: </span>
            <span style="font-family:var(--font-mono);font-size:11px;color:var(--accent)">{result.result?.cost?.toFixed(6)} RAI</span>
          </div>
          <div>
            <span style="font-size:10px;color:var(--muted)">HYPERSCALE ID: </span>
            <span style="font-family:var(--font-mono);font-size:10px;color:var(--accent3)">{result.result?.hyperscale_job_id || '—'}</span>
          </div>
        </div>
        {#if result.txhash}
          <a href="https://explorer.vinjan-inc.com/republic-testnet/tx/{result.txhash}" target="_blank" rel="noopener"
            style="display:inline-block;margin-top:12px;color:var(--blue);font-family:var(--font-mono);font-size:11px">
            View Inference TX on Explorer ↗
          </a>
        {/if}
        <a href="https://explorer.vinjan-inc.com/republic-testnet/tx/{payTxHash}" target="_blank" rel="noopener"
          style="display:inline-block;margin-top:8px;margin-left:16px;color:var(--blue);font-family:var(--font-mono);font-size:11px">
          View Payment TX on Explorer ↗
        </a>
      </div>
    </div>
  {/if}

</div>

<style>
  .markdown-body { font-size: 14px; line-height: 1.8; color: var(--text); }
  .markdown-body :global(h1), .markdown-body :global(h2), .markdown-body :global(h3), .markdown-body :global(h4) {
    color: var(--accent); font-family: var(--font-display); letter-spacing: 1px; margin: 20px 0 10px; line-height: 1.2;
  }
  .markdown-body :global(h1) { font-size: 24px; }
  .markdown-body :global(h2) { font-size: 20px; }
  .markdown-body :global(h3) { font-size: 17px; }
  .markdown-body :global(p) { margin-bottom: 12px; color: var(--text); }
  .markdown-body :global(ul), .markdown-body :global(ol) { padding-left: 20px; margin-bottom: 12px; }
  .markdown-body :global(li) { margin-bottom: 6px; color: var(--text); }
  .markdown-body :global(code) {
    background: rgba(255,107,0,0.1); border: 1px solid rgba(255,107,0,0.2);
    padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono); font-size: 12px; color: var(--accent);
  }
  .markdown-body :global(pre) {
    background: var(--bg1); border: 1px solid var(--border); padding: 16px;
    border-radius: 8px; overflow-x: auto; margin-bottom: 16px;
  }
  .markdown-body :global(pre code) { background: none; border: none; padding: 0; color: var(--text); font-size: 13px; }
  .markdown-body :global(strong) { color: var(--text); font-weight: 700; }
  .markdown-body :global(em) { color: var(--muted); font-style: italic; }
  .markdown-body :global(hr) { border: none; border-top: 1px solid var(--border); margin: 20px 0; }
  .markdown-body :global(a) { color: var(--blue); text-decoration: none; }
  .markdown-body :global(a:hover) { text-decoration: underline; }
  .markdown-body :global(blockquote) {
    border-left: 3px solid var(--accent); padding-left: 16px; margin: 12px 0; color: var(--muted); font-style: italic;
  }
  .markdown-body :global(table) { width: 100%; border-collapse: collapse; margin-bottom: 16px; font-size: 13px; }
  .markdown-body :global(th) {
    background: rgba(255,107,0,0.1); border: 1px solid var(--border); padding: 8px 12px;
    text-align: left; color: var(--accent); font-family: var(--font-mono); font-size: 11px; letter-spacing: 1px;
  }
  .markdown-body :global(td) { border: 1px solid var(--border); padding: 8px 12px; color: var(--text); }
  .markdown-body :global(tr:hover td) { background: rgba(255,107,0,0.03); }
</style>