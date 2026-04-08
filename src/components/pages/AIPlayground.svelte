<script>
  import { onMount } from 'svelte';
  import { API, fmt, shortAddr } from '../../stores/app.js';
  import { marked } from 'marked';
  import { Buffer } from 'buffer'; 

  // ── STATE ──
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

  $: filteredModels = models.filter(m =>
    m.id.toLowerCase().includes(modelSearch.toLowerCase()) ||
    m.name.toLowerCase().includes(modelSearch.toLowerCase())
  );
  $: selectedModelInfo = models.find(m => m.id === selectedModel);

  // ── KEPLR / PAYMENT ──
  let keplrConnected = false;
  let userAddress = '';
  let keplrError = '';
  let paymentStep = 'idle'; 
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
      if (!window.keplr) throw new Error('Keplr not installed!');
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

  // 🔥 YAHAN FIX KIYA HAI LOGIC 🔥
  async function payAndInfer() {
    if (!keplrConnected) { await connectKeplr(); return; }
    if (!prompt.trim()) return;
    paymentStep = 'paying';
    paymentError = '';
    loading = true;
    try {
      await window.keplr.enable(REPUBLIC_CHAIN.chainId);
      const accRes = await fetch(`${API}/api/hyperscale/account/${userAddress}`);
      const accData = await accRes.json();
      
      const signDoc = {
        chain_id: REPUBLIC_CHAIN.chainId,
        account_number: String(accData.account_number || '0'),
        sequence: String(accData.sequence || '0'),
        fee: {
          amount: [{ denom: 'arai', amount: '200000000000000' }],
          gas: '200000'
        },
        msgs: [{
          type: 'cosmos-sdk/MsgSend',
          value: {
            from_address: userAddress,
            to_address: TREASURY,
            amount: [{ denom: 'arai', amount: ARAI_FEE }]
          }
        }],
        memo: 'Hyperscale inference fee'
      };

      const { signed, signature } = await window.keplr.signAmino(REPUBLIC_CHAIN.chainId, userAddress, signDoc);

      // FIX: Handling ESM import wrap for '@keplr-wallet/cosmos'
      const rawModule = await import('https://esm.sh/@keplr-wallet/cosmos@0.12.80');
      const cosmos = rawModule.cosmos || rawModule.default.cosmos;

      if (!cosmos) throw new Error("Cosmos SDK not found in module");

      const signedTxBytes = cosmos.tx.v1beta1.TxRaw.encode({
        bodyBytes: cosmos.tx.v1beta1.TxBody.encode({
          messages: [{
            typeUrl: '/cosmos.bank.v1beta1.MsgSend',
            value: cosmos.bank.v1beta1.MsgSend.encode({
              fromAddress: userAddress,
              toAddress: TREASURY,
              amount: [{ denom: 'arai', amount: ARAI_FEE }]
            }).finish()
          }],
          memo: signed.memo
        }).finish(),
        authInfoBytes: cosmos.tx.v1beta1.AuthInfo.encode({
          signerInfos: [{
            publicKey: {
              typeUrl: '/ethermint.crypto.v1.ethsecp256k1.PubKey',
              value: cosmos.crypto.ed25519.PubKey.encode({
                key: Buffer.from(signature.pub_key.value, 'base64')
              }).finish()
            },
            modeInfo: { single: { mode: 1 } },
            sequence: BigInt(signed.sequence)
          }],
          fee: {
            amount: signed.fee.amount,
            gasLimit: BigInt(signed.fee.gas)
          }
        }).finish(),
        signatures: [Buffer.from(signature.signature, 'base64')]
      }).finish();

      const txHashBytes = await window.keplr.sendTx(REPUBLIC_CHAIN.chainId, signedTxBytes, 'sync');
      paymentTxHash = Buffer.from(txHashBytes).toString('hex').toUpperCase();
      paymentStep = 'verifying';
      await new Promise(r => setTimeout(r, 6000));
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
    loading = true; error = ''; result = null;
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
      if (['completed', 'inferred_only', 'failed'].includes(d.status)) {
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
  <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin-bottom:28px">
    <div style="font-family:var(--font-mono);font-size:11px;color:var(--accent);letter-spacing:2px;margin-bottom:12px">HOW IT WORKS</div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;text-align:center">
      <div><div style="font-size:24px;margin-bottom:8px">🔗</div><div style="font-size:13px;font-weight:600;margin-bottom:4px">1. Connect Keplr</div><div style="font-size:11px;color:var(--muted)">Connect your Republic AI wallet</div></div>
      <div><div style="font-size:24px;margin-bottom:8px">💸</div><div style="font-size:13px;font-weight:600;margin-bottom:4px">2. Pay 10 RAI</div><div style="font-size:11px;color:var(--muted)">Sign payment on Republic chain</div></div>
      <div><div style="font-size:24px;margin-bottom:8px">⛓️</div><div style="font-size:13px;font-weight:600;margin-bottom:4px">3. Get Response</div><div style="font-size:11px;color:var(--muted)">AI inference recorded on-chain</div></div>
    </div>
  </div>

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
      <button on:click={connectKeplr} style="background:var(--accent);color:#000;border:none;padding:10px 20px;font-family:var(--font-mono);font-size:12px;font-weight:700;border-radius:8px;cursor:pointer;letter-spacing:1px">
        {paymentStep === 'connecting' ? '⏳ Connecting...' : '🔗 Connect Keplr'}
      </button>
    {:else}
      <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted)">Fee: <span style="color:var(--accent);font-weight:700">{RAI_FEE} RAI</span></div>
    {/if}
  </div>

  {#if !result}
    <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:24px">
      <div style="margin-bottom:20px">
        <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-bottom:8px;letter-spacing:1px">SELECT MODEL</div>
        <select bind:value={selectedModel} style="width:100%;background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:10px;color:var(--text);font-family:var(--font-mono);font-size:11px;">
          {#each filteredModels as model}
            <option value={model.id}>{model.name}</option>
          {/each}
        </select>
      </div>

      <textarea bind:value={prompt} placeholder="Ask anything..." disabled={loading} style="width:100%;background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:14px;color:var(--text);min-height:120px;box-sizing:border-box"></textarea>

      {#if paymentError}<div style="color:#EF4444;font-size:12px;margin-top:10px">💸 {paymentError}</div>{/if}
      
      <button on:click={payAndInfer} disabled={!prompt.trim() || loading} style="margin-top:16px;background:var(--accent);color:#000;border:none;padding:13px;width:100%;border-radius:8px;font-weight:bold;cursor:pointer;opacity:{!prompt.trim() || loading ? 0.5 : 1}">
        {loading ? 'Processing...' : keplrConnected ? `⚡ PAY ${RAI_FEE} RAI & SUBMIT` : '🔗 Connect & Submit'}
      </button>
    </div>
  {:else}
    <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:20px">
      <div style="display:flex;justify-content:space-between;margin-bottom:15px">
        <span style="color:var(--accent);font-family:var(--font-mono)">RESULT</span>
        <button on:click={reset} style="background:none;border:1px solid var(--border);color:var(--muted);cursor:pointer;padding:4px 8px;border-radius:4px">New Job</button>
      </div>
      <div class="markdown-body">{@html marked(result.result?.content || result.error || '')}</div>
    </div>
  {/if}
</div>

<style>
  /* Your original CSS styles here */
  .markdown-body { font-size:14px; line-height:1.8; color:var(--text); }
  /* ... rest of your styles */
</style>