<script>
  import { onMount } from 'svelte';
  import { API, fmt, shortAddr } from '../../stores/app.js';
  import { marked } from 'marked';

  // ── STATE ──
  let prompt = '';
  let loading = false;
  let result = null;
  let error = '';
  let trackingId = null;
  let pollInterval;

  // ── MINERS ──
  let miners = [];
  let selectedMiner = null;

  // ── MODELS ──
  let models = [];
  let selectedModel = 'nex-agi/deepseek-v3.1-nex-n1';
  let modelsLoading = true;
  let modelSearch = '';
  $: filteredModels = models.filter(m =>
    m.id.toLowerCase().includes(modelSearch.toLowerCase()) ||
    m.name.toLowerCase().includes(modelSearch.toLowerCase())
  );
  $: selectedModelInfo = models.find(m => m.id === selectedModel);

  // ── KEPLR / PAYMENT ──
  let keplrConnected = false;
  let userAddress = '';
  let keplrError = '';
  let paymentStep = 'idle'; // idle | connecting | paying | verifying | ready
  let paymentTxHash = '';
  let paymentError = '';

  const TREASURY = 'rai1alt2884lvwzlzg6l03eaplry7a0ytx0wf3k889';
  const RAI_FEE = 10;
  const ARAI_FEE = (BigInt(RAI_FEE) * BigInt(10 ** 18)).toString();

  const REPUBLIC_CHAIN = {
    chainId: 'raitestnet_77701-1',
    chainName: 'Republic AI Testnet',
    rpc: 'https://rpc-test.republic.vinjan-inc.com',
    rest: 'https://api-test.republic.vinjan-inc.com',
    bip44: { coinType: 60 },
    bech32Config: {
      bech32PrefixAccAddr: 'rai1',
      bech32PrefixAccPub: 'rai1pub',
      bech32PrefixValAddr: 'raivaloper1',
      bech32PrefixValPub: 'raivaloper1pub',
      bech32PrefixConsAddr: 'raivalcons1',
      bech32PrefixConsPub: 'raivalcons1pub',
    },
    currencies: [{ coinDenom: 'RAI', coinMinimalDenom: 'arai', coinDecimals: 18 }],
    feeCurrencies: [{ coinDenom: 'RAI', coinMinimalDenom: 'arai', coinDecimals: 18, gasPriceStep: { low: 0.01, average: 0.025, high: 0.04 } }],
    stakeCurrency: { coinDenom: 'RAI', coinMinimalDenom: 'arai', coinDecimals: 18 },
  };

  async function connectKeplr() {
    paymentStep = 'connecting';
    keplrError = '';
    try {
      if (!window.keplr) throw new Error('Keplr not installed! Install from keplr.app');
      await window.keplr.experimentalSuggestChain(REPUBLIC_CHAIN);
      await window.keplr.enable(REPUBLIC_CHAIN.chainId);
      const offlineSigner = window.keplr.getOfflineSigner(REPUBLIC_CHAIN.chainId);
      const accounts = await offlineSigner.getAccounts();
      userAddress = accounts[0].address;
      keplrConnected = true;
      paymentStep = 'idle';
    } catch(e) {
      keplrError = e.message;
      paymentStep = 'idle';
    }
  }

  async function payAndInfer() {
    if (!prompt.trim()) return;
    paymentStep = 'connecting';
    paymentError = '';
    loading = true;
    try {
      if (!window.keplr) throw new Error('Keplr not installed!');
      
      await window.keplr.experimentalSuggestChain(REPUBLIC_CHAIN);
      await window.keplr.enable(REPUBLIC_CHAIN.chainId);
      
      const offlineSigner = window.keplr.getOfflineSigner(REPUBLIC_CHAIN.chainId);
      const accounts = await offlineSigner.getAccounts();
      userAddress = accounts[0].address;
      keplrConnected = true;

      paymentStep = 'paying';

      // Load SigningStargateClient from CDN
      const { SigningStargateClient } = await import('https://esm.sh/@cosmjs/stargate@0.32.4');
      
      const client = await SigningStargateClient.connectWithSigner(
        'https://rpc-republic.onenov.xyz',
        offlineSigner
      );

      const amount = [{ denom: 'arai', amount: ARAI_FEE }];
      const fee = { 
        amount: [{ denom: 'arai', amount: '200000000000000' }], 
        gas: '200000' 
      };

      const result = await client.sendTokens(
        userAddress,
        TREASURY,
        amount,
        fee,
        'Hyperscale inference fee'
      );

      if (result.code !== 0) throw new Error(`TX failed: ${result.rawLog}`);
      
      paymentTxHash = result.transactionHash;
      paymentStep = 'verifying';
      await new Promise(r => setTimeout(r, 3000));
      
      paymentStep = 'ready';
      await submitJob();

    } catch(e) {
      paymentError = e.message;
      paymentStep = 'idle';
      loading = false;
    }
  }

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
          miner_address: selectedMiner?.address || '',
          model: selectedModel
        })
      });
      const d = await r.json();
      if (!d.success) throw new Error(d.error || 'Failed');
      trackingId = d.tracking_id;
      pollInterval = setInterval(pollStatus, 3000);
    } catch(e) {
      error = e.message;
      loading = false;
      paymentStep = 'idle';
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
        paymentStep = 'idle';
      }
    } catch(e) {}
  }

  function reset() {
    result = null; error = ''; trackingId = null;
    prompt = ''; loading = false; selectedMiner = null;
    selectedModel = 'nex-agi/deepseek-v3.1-nex-n1';
    paymentStep = 'idle'; paymentTxHash = ''; paymentError = '';
  }

  onMount(() => { loadMiners(); loadModels(); });
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
      <div><div style="font-size:24px;margin-bottom:8px">🔗</div><div style="font-size:13px;font-weight:600;margin-bottom:4px">1. Connect Keplr</div><div style="font-size:11px;color:var(--muted)">Connect your Republic AI wallet</div></div>
      <div><div style="font-size:24px;margin-bottom:8px">💸</div><div style="font-size:13px;font-weight:600;margin-bottom:4px">2. Pay 10 RAI</div><div style="font-size:11px;color:var(--muted)">Sign payment on Republic chain</div></div>
      <div><div style="font-size:24px;margin-bottom:8px">⛓️</div><div style="font-size:13px;font-weight:600;margin-bottom:4px">3. Get Response</div><div style="font-size:11px;color:var(--muted)">AI inference recorded on-chain</div></div>
    </div>
  </div>

  <!-- KEPLR CONNECT -->
  <div style="background:var(--bg2);border:1px solid {keplrConnected ? 'rgba(74,222,128,.3)' : 'var(--border)'};border-radius:12px;padding:16px 20px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
    <div>
      <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-bottom:4px;letter-spacing:1px">WALLET</div>
      {#if keplrConnected}
        <div style="font-family:var(--font-mono);font-size:12px;color:#4ADE80">✅ {userAddress.slice(0,16)}...{userAddress.slice(-6)}</div>
      {:else}
        <div style="font-size:13px;color:var(--muted)">Connect Keplr to pay with RAI</div>
      {/if}
      {#if keplrError}<div style="font-size:11px;color:#EF4444;margin-top:4px">{keplrError}</div>{/if}
    </div>
    {#if !keplrConnected}
      <button on:click={connectKeplr}
        style="background:var(--accent);color:#000;border:none;padding:10px 20px;font-family:var(--font-mono);font-size:12px;font-weight:700;border-radius:8px;cursor:pointer;letter-spacing:1px">
        {paymentStep === 'connecting' ? '⏳ Connecting...' : '🔗 Connect Keplr'}
      </button>
    {:else}
      <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted)">
        Fee: <span style="color:var(--accent);font-weight:700">{RAI_FEE} RAI</span> per inference
      </div>
    {/if}
  </div>

  {#if !result}
    <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:24px">

      <!-- MODEL SELECT -->
      <div style="margin-bottom:20px">
        <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-bottom:8px;letter-spacing:1px">
          SELECT MODEL <span style="color:var(--accent)">({models.length} available)</span>
        </div>
        {#if modelsLoading}
          <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted)">Loading models...</div>
        {:else}
          <input bind:value={modelSearch}
            placeholder="Search models... e.g. gpt, claude, llama, deepseek"
            style="width:100%;background:var(--bg1);border:1px solid var(--border);border-radius:8px 8px 0 0;padding:8px 14px;color:var(--text);font-family:var(--font-mono);font-size:11px;outline:none;box-sizing:border-box"/>
          <select bind:value={selectedModel} size="5"
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
        {#if miners.length === 0}
          <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted)">Loading miners...</div>
        {:else}
          <select bind:value={selectedMiner}
            style="width:100%;background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:10px 14px;color:var(--text);font-family:var(--font-mono);font-size:11px;outline:none;cursor:pointer">
            <option value={null} style="background:#0D0D1A;color:#E8E8F0">— Auto (any available miner)</option>
            {#each miners as miner}
              <option value={miner} style="background:#0D0D1A;color:#E8E8F0">{miner.moniker || shortAddr(miner.address)} · {fmt(miner.submit_job_result)} results</option>
            {/each}
          </select>
          {#if selectedMiner}
            <div style="margin-top:8px;font-family:var(--font-mono);font-size:10px;color:var(--muted)">
              Selected: <span style="color:var(--accent)">{selectedMiner.moniker || shortAddr(selectedMiner.address)}</span>
              &nbsp;·&nbsp; Uptime: {selectedMiner.uptime ? selectedMiner.uptime + '%' : '—'}
            </div>
          {/if}
        {/if}
      </div>

      <!-- PROMPT -->
      <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-bottom:12px;letter-spacing:1px">ENTER YOUR PROMPT</div>
      <textarea bind:value={prompt}
        placeholder="Ask anything... e.g. What is Republic AI? How does GPU mining work?"
        disabled={loading}
        style="width:100%;background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:14px;color:var(--text);font-family:var(--font-mono);font-size:13px;resize:vertical;min-height:120px;outline:none;line-height:1.6;box-sizing:border-box"
      ></textarea>

      {#if error}<div class="error-msg" style="margin-top:12px">{error}</div>{/if}
      {#if paymentError}<div class="error-msg" style="margin-top:12px">💸 {paymentError}</div>{/if}

      {#if loading}
        <div style="margin-top:20px;text-align:center">
          <div style="background:#0A0A12;border:1px solid #1E1E2A;color:#4ADE80;font-family:'Courier New',monospace;font-size:12px;padding:32px 16px 16px;border-radius:4px;position:relative;display:inline-block;min-width:260px">
            <div style="position:absolute;top:0;left:0;right:0;height:24px;background:#141420;border-radius:4px 4px 0 0;display:flex;align-items:center;padding:0 8px">
              <span style="font-size:9px;color:#666;letter-spacing:1px">hyperscale_sdk</span>
              <div style="margin-left:auto;display:flex;gap:4px">
                <div style="width:8px;height:8px;border-radius:50%;background:#E35353"></div>
                <div style="width:8px;height:8px;border-radius:50%;background:#E3C853"></div>
                <div style="width:8px;height:8px;border-radius:50%;background:#53E3A6"></div>
              </div>
            </div>
            <div style="font-size:12px">
              {paymentStep === 'paying' ? '💸 Sending 10 RAI...' 
              : paymentStep === 'verifying' ? '🔍 Verifying payment...'
              : 'Processing inference...'}
            </div>
          </div>
          <div style="font-size:12px;color:var(--muted);margin-top:12px">
            {paymentStep === 'paying' ? 'Sign transaction in Keplr...'
            : paymentStep === 'verifying' ? 'Confirming on-chain payment...'
            : selectedMiner ? `Sending to ${selectedMiner.moniker || shortAddr(selectedMiner.address)}...` : 'Submitting to Republic chain (~30s)'}
          </div>
        </div>
      {:else}
        <button on:click={payAndInfer}
          disabled={!prompt.trim()}
          style="margin-top:16px;background:var(--accent);color:#000;border:none;padding:13px 36px;font-family:var(--font-display);font-size:18px;letter-spacing:1px;border-radius:8px;cursor:pointer;opacity:{prompt.trim() ? 1 : 0.5};width:100%">
          {keplrConnected ? `⚡ PAY ${RAI_FEE} RAI & SUBMIT` : '🔗 Connect Keplr & Submit'}
        </button>
        <div style="text-align:center;font-size:11px;color:var(--muted);margin-top:8px">
          {RAI_FEE} RAI will be sent to treasury · Inference recorded on-chain
        </div>
      {/if}
    </div>
  {/if}

  <!-- RESULT -->
  {#if result}
    <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;overflow:hidden">
      <div style="padding:14px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between">
        <div style="display:flex;align-items:center;gap:10px">
          <div style="width:8px;height:8px;border-radius:50%;background:{result.status === 'completed' ? '#4ADE80' : result.status === 'failed' ? '#EF4444' : 'var(--accent)'}"></div>
          <span style="font-family:var(--font-mono);font-size:11px;color:var(--muted)">
            {result.status === 'completed' ? '✅ Completed & On-Chain' : result.status === 'inferred_only' ? '⚡ Inferred (Chain pending)' : '❌ Failed'}
          </span>
        </div>
        <button on:click={reset} style="background:transparent;border:1px solid var(--border);color:var(--muted);padding:5px 12px;font-family:var(--font-mono);font-size:10px;cursor:pointer;border-radius:4px">↩ New Job</button>
      </div>

      <div style="padding:16px 20px;border-bottom:1px solid var(--border);background:rgba(255,107,0,0.03)">
        <div style="font-family:var(--font-mono);font-size:10px;color:var(--accent);margin-bottom:6px;letter-spacing:1px">PROMPT</div>
        <div style="font-size:14px;color:var(--muted)">{result.prompt}</div>
      </div>

      <div style="padding:20px">
        <div style="font-family:var(--font-mono);font-size:10px;color:var(--accent);margin-bottom:10px;letter-spacing:1px">AI RESPONSE</div>
        <div class="markdown-body">{@html marked(result.result?.content || result.error || '')}</div>
      </div>

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
          <div style="margin-top:12px;display:flex;align-items:center;gap:16px;flex-wrap:wrap">
            <a href={result.explorer} target="_blank" rel="noopener" style="color:var(--blue);font-family:var(--font-mono);font-size:11px">View on Explorer ↗</a>
            {#if paymentTxHash}
              <a href="https://explorer.vinjan-inc.com/republic-testnet/tx/{paymentTxHash}" target="_blank" rel="noopener" style="color:var(--accent3);font-family:var(--font-mono);font-size:11px">Payment TX ↗</a>
            {/if}
            <span style="font-family:var(--font-mono);font-size:10px;color:var(--muted)">Verified by: Hyperscale SDK + Republic AI Chain</span>
          	