<script>
  import { onMount, onDestroy } from 'svelte';
  import { API, fmt, shortAddr } from '../../stores/app.js';
  import { marked } from 'marked';
  import { SigningStargateClient } from '@cosmjs/stargate';

  // ---------------- CONFIG ----------------
  const RPC = 'https://rpc-republic.onenov.xyz';
  const REST = 'https://api-republic.onenov.xyz';
  const TREASURY = 'rai1alt2884lvwzlzg6l03eaplry7a0ytx0wf3k889';
  const FEE_RAI = 5;
  const FEE_ARAI = '5000000000000000000';

  // ---------------- STATE ----------------
  let prompt = '';
  let loading = false;
  let result = null;
  let error = '';
  let trackingId = null;
  let pollInterval = null;

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

  let step = 1;

  $: filteredModels = models.filter(m =>
    (m.id || '').toLowerCase().includes(modelSearch.toLowerCase()) ||
    (m.name || '').toLowerCase().includes(modelSearch.toLowerCase())
  );

  $: selectedModelInfo = models.find(m => m.id === selectedModel);

  // ---------------- CHAIN CONFIG (WORKING) ----------------
  const CHAIN_CONFIG = {
    chainId: 'raitestnet_77701-1',
    chainName: 'Republic Testnet',
    rpc: RPC,
    rest: REST,
    bip44: { coinType: 60 },
    bech32Config: {
      bech32PrefixAccAddr: 'rai',
      bech32PrefixAccPub: 'raipub',
      bech32PrefixValAddr: 'raivaloper',
      bech32PrefixValPub: 'raivaloperpub',
      bech32PrefixConsAddr: 'raivalcons',
      bech32PrefixConsPub: 'raivalconspub',
    },
    currencies: [{
      coinDenom: 'RAI',
      coinMinimalDenom: 'arai',
      coinDecimals: 18,
    }],
    feeCurrencies: [{
      coinDenom: 'RAI',
      coinMinimalDenom: 'arai',
      coinDecimals: 18,
      gasPriceStep: { low: 10000000000, average: 25000000000, high: 40000000000 },
    }],
    stakeCurrency: {
      coinDenom: 'RAI',
      coinMinimalDenom: 'arai',
      coinDecimals: 18,
    },
  };

  // ---------------- HELPERS ----------------
  function clearPoller() {
    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }
  }

  // ---------------- WALLET CONNECTION ----------------
  async function connectWallet() {
    payError = '';
    try {
      if (!window.keplr) {
        throw new Error('Keplr wallet not installed. Please install Keplr extension.');
      }

      // Remove existing chain config to avoid conflicts
      try {
        await window.keplr.removeChain('raitestnet_77701-1');
      } catch(e) {
        console.log('Chain not found, adding fresh');
      }

      await new Promise(r => setTimeout(r, 500));

      // Suggest chain
      await window.keplr.experimentalSuggestChain(CHAIN_CONFIG);
      
      // Enable chain
      await window.keplr.enable('raitestnet_77701-1');
      
      // Get signer and accounts
      const offlineSigner = window.keplr.getOfflineSigner('raitestnet_77701-1');
      const accounts = await offlineSigner.getAccounts();
      
      walletAddress = accounts[0].address;
      walletConnected = true;
      step = 2;
      
      // Fetch balance
      await fetchBalance();
      
      console.log('✅ Connected:', walletAddress);
      
    } catch (e) {
      payError = 'Failed to connect: ' + (e?.message || e);
      console.error('connectWallet error:', e);
    }
  }

  async function fetchBalance() {
    if (!walletAddress) {
      walletBalance = '0 RAI';
      return;
    }

    try {
      const r = await fetch(`${REST}/cosmos/bank/v1beta1/balances/${walletAddress}`);
      const d = await r.json();
      const arai = d?.balances?.find(b => b.denom === 'arai');

      if (arai?.amount) {
        const balanceNum = parseInt(arai.amount) / 1e18;
        walletBalance = `${balanceNum.toFixed(4)} RAI`;
      } else {
        walletBalance = '0 RAI';
      }
    } catch (e) {
      walletBalance = '—';
      console.warn('fetchBalance failed:', e);
    }
  }

  // ---------------- PAYMENT + SUBMIT ----------------
  async function payAndSubmit() {
    if (!prompt.trim()) {
      payError = 'Please enter a prompt first';
      return;
    }

    payLoading = true;
    payError = '';
    payTxHash = '';

    try {
      if (!window.keplr) throw new Error('Keplr not found');

      // Ensure chain is enabled
      await window.keplr.enable('raitestnet_77701-1');
      
      const offlineSigner = window.keplr.getOfflineSigner('raitestnet_77701-1');
      const accounts = await offlineSigner.getAccounts();
      const signerAddress = accounts[0].address;
      
      walletAddress = signerAddress;
      walletConnected = true;

      // Create client
      const client = await SigningStargateClient.connectWithSigner(RPC, offlineSigner);

      const amount = [{ denom: 'arai', amount: FEE_ARAI }];
      const fee = { amount: [{ denom: 'arai', amount: '10000000000' }], gas: '200000' };
      const memo = `RepublicStats Hyperscale Job | ${prompt.slice(0, 40)}`;

      const tx = await client.sendTokens(
        signerAddress,
        TREASURY,
        amount,
        fee,
        memo
      );

      if (tx.code !== 0) {
        throw new Error(`TX failed (${tx.code}): ${tx.rawLog || 'Unknown error'}`);
      }

      payTxHash = tx.transactionHash;
      step = 3;
      await fetchBalance();

      // Submit inference job
      loading = true;
      const r = await fetch(`${API}/api/hyperscale/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: prompt.trim(),
          miner_address: selectedMiner?.address || '',
          model: selectedModel,
          payment_txhash: payTxHash,
          payer_address: signerAddress,
        })
      });

      const d = await r.json();
      if (!d.success) throw new Error(d.error || 'Failed to submit job');

      trackingId = d.tracking_id;
      clearPoller();
      pollInterval = setInterval(pollStatus, 3000);
      
    } catch (e) {
      payError = 'Error: ' + (e?.message || e);
      loading = false;
      console.error('payAndSubmit error:', e);
    } finally {
      payLoading = false;
    }
  }

  async function pollStatus() {
    if (!trackingId) return;
    try {
      const r = await fetch(`${API}/api/hyperscale/status/${trackingId}`);
      const d = await r.json();

      if (d.status === 'completed' || d.status === 'inferred_only' || d.status === 'failed') {
        clearPoller();
        result = d;
        loading = false;
        step = 4;
      }
    } catch (e) {
      console.warn('pollStatus failed:', e);
    }
  }

  // ---------------- DATA LOADING ----------------
  async function loadMiners() {
    try {
      const r = await fetch(`${API}/api/leaderboard?limit=200`);
      const d = await r.json();
      miners = (d.data || []).filter(m => m.submit_job_result > 0);
    } catch (e) {
      console.warn('loadMiners failed:', e);
    }
  }

  async function loadModels() {
    modelsLoading = true;
    try {
      const r = await fetch(`${API}/api/hyperscale/models`);
      models = await r.json();
    } catch (e) {
      console.warn('loadModels failed:', e);
    }
    modelsLoading = false;
  }

  // ---------------- UI ACTIONS ----------------
  function reset() {
    clearPoller();
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
    clearPoller();
    walletAddress = '';
    walletConnected = false;
    walletBalance = '';
    step = 1;
    reset();
  }

  // ---------------- LIFECYCLE ----------------
  onMount(() => {
    loadMiners();
    loadModels();
  });

  onDestroy(() => {
    clearPoller();
  });
</script>

<!-- HTML TEMPLATE -->
<div class="hero">
  <div class="hero-bg"></div>
  <div style="position:relative;z-index:1">
    <div class="hero-eyebrow"><span class="hero-eyebrow-dot"></span>Republic AI · Hyperscale Jobs</div>
    <h1><span class="line1">HYPERSCALE</span><span class="line2">JOBS</span></h1>
    <p class="hero-sub">Submit AI inference jobs powered by Hyperscale SDK — recorded on Republic AI chain</p>
  </div>
</div>

<div style="max-width:800px;margin:0 auto;padding:0 28px 60px">

  {#if step === 1 || step === 2}
    <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:24px">
      
      {#if step === 1}
        <!-- CONNECT WALLET STEP -->
        <div style="text-align:center;padding:20px">
          <div style="font-size:48px;margin-bottom:16px">🔗</div>
          <h3 style="margin-bottom:8px">Connect Keplr Wallet</h3>
          <p style="color:var(--muted);margin-bottom:24px">Connect your Keplr wallet to pay {FEE_RAI} RAI per inference job</p>
          
          {#if payError}
            <div class="error-msg" style="margin-bottom:16px">{payError}</div>
          {/if}
          
          <button on:click={connectWallet}
            style="background:var(--accent);color:#000;border:none;padding:12px 32px;font-family:var(--font-mono);font-size:14px;font-weight:700;border-radius:8px;cursor:pointer">
            🔗 Connect Keplr
          </button>
        </div>
        
      {:else if step === 2}
        <!-- CONFIGURE JOB STEP -->
        <div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
            <div>
              <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted)">WALLET</div>
              <div style="font-family:monospace;font-size:12px;color:#4ADE80">✅ {walletAddress.slice(0,16)}...{walletAddress.slice(-6)}</div>
              <div style="font-size:11px;color:var(--muted)">Balance: {walletBalance}</div>
            </div>
            <button on:click={disconnectWallet}
              style="background:transparent;border:1px solid var(--border);color:var(--muted);padding:6px 12px;border-radius:6px;cursor:pointer;font-size:11px">
              Disconnect
            </button>
          </div>

          <!-- MODEL SELECT -->
          <div style="margin-bottom:20px">
            <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-bottom:8px">SELECT MODEL</div>
            {#if modelsLoading}
              <div>Loading models...</div>
            {:else}
              <input bind:value={modelSearch} placeholder="Search models..." style="width:100%;background:var(--bg1);border:1px solid var(--border);border-radius:8px 8px 0 0;padding:8px 14px;font-size:11px"/>
              <select bind:value={selectedModel} size="4" style="width:100%;background:var(--bg1);border:1px solid var(--border);border-top:none;border-radius:0 0 8px 8px;padding:4px;font-size:11px">
                {#each filteredModels as model}
                  <option value={model.id}>{model.name || model.id}</option>
                {/each}
              </select>
            {/if}
          </div>

          <!-- MINER SELECT -->
          <div style="margin-bottom:20px">
            <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-bottom:8px">SELECT MINER (optional)</div>
            <select bind:value={selectedMiner} style="width:100%;background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:8px 14px;font-size:11px">
              <option value={null}>— Auto (any available miner) —</option>
              {#each miners as miner}
                <option value={miner}>{miner.moniker || shortAddr(miner.address)}</option>
              {/each}
            </select>
          </div>

          <!-- PROMPT -->
          <div style="margin-bottom:20px">
            <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-bottom:8px">ENTER YOUR PROMPT</div>
            <textarea bind:value={prompt} placeholder="Ask anything..." rows="4" style="width:100%;background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:12px;font-size:13px;resize:vertical"></textarea>
          </div>

          {#if payError}
            <div class="error-msg" style="margin-bottom:16px">{payError}</div>
          {/if}

          <button on:click={payAndSubmit} disabled={!prompt.trim() || payLoading}
            style="background:var(--accent);color:#000;border:none;padding:14px 32px;font-size:16px;font-weight:700;border-radius:8px;cursor:pointer;width:100%;opacity:{!prompt.trim() || payLoading ? 0.5 : 1}">
            {payLoading ? '⏳ Processing...' : `⚡ PAY ${FEE_RAI} RAI & SUBMIT`}
          </button>
          <div style="text-align:center;font-size:11px;color:var(--muted);margin-top:12px">
            {FEE_RAI} RAI will be sent to treasury · Inference recorded on-chain
          </div>
        </div>
      {/if}
    </div>
  {/if}

  {#if step === 3 || step === 4}
    <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;overflow:hidden">
      <div style="padding:14px 20px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center">
        <div>
          <span style="font-family:monospace;font-size:12px;color:#4ADE80">
            {step === 3 ? '⏳ Processing...' : '✅ Completed'}
          </span>
          {#if payTxHash}
            <div style="font-size:10px;color:var(--muted);margin-top:4px">TX: {payTxHash.slice(0,20)}...</div>
          {/if}
        </div>
        <button on:click={reset} style="background:transparent;border:1px solid var(--border);padding:6px 12px;border-radius:6px;cursor:pointer;font-size:11px">↩ New Job</button>
      </div>

      {#if result}
        <div style="padding:16px 20px;border-bottom:1px solid var(--border)">
          <div style="font-size:11px;color:var(--accent)">PROMPT</div>
          <div style="font-size:14px;color:var(--muted)">{result.prompt}</div>
        </div>
        <div style="padding:20px">
          <div style="font-size:11px;color:var(--accent);margin-bottom:8px">AI RESPONSE</div>
          <div class="markdown-body">{@html marked(result.result?.content || result.error || '')}</div>
        </div>
      {:else if step === 3}
        <div style="padding:40px;text-align:center">
          <div>⏳ Waiting for AI response...</div>
          <div style="font-size:12px;color:var(--muted);margin-top:12px">This may take 10-30 seconds</div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .error-msg {
    background:rgba(239,68,68,0.1);
    border:1px solid rgba(239,68,68,0.3);
    color:#EF4444;
    padding:10px 14px;
    border-radius:8px;
    font-size:12px;
  }
</style>