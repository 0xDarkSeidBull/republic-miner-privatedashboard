<script>
  import { onMount } from 'svelte';
  import { API, fmt, shortAddr } from '../../stores/app.js';
  import { marked } from 'marked';

  // ---------------- STATE ----------------
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

  // ---------------- KEPLR ----------------
  let keplrConnected = false;
  let userAddress = "";

  const CHAIN_ID = "raitestnet_77701-1";
  const TREASURY = "rai1alt2884lvwzlzg6l03eaplry7a0ytx0wf3k889";
  const AMOUNT = "10000000000000000000"; // 10 RAI

  // ---------------- COMPUTED ----------------
  $: filteredModels = models.filter(m =>
    m.id.toLowerCase().includes(modelSearch.toLowerCase()) ||
    m.name.toLowerCase().includes(modelSearch.toLowerCase())
  );

  $: selectedModelInfo = models.find(m => m.id === selectedModel);

  // ---------------- KEPLR ----------------
  async function connectKeplr() {
    if (!window.keplr) {
      alert("Install Keplr");
      return;
    }

    await window.keplr.enable(CHAIN_ID);

    const signer = window.keplr.getOfflineSignerOnlyAmino(CHAIN_ID);
    const accounts = await signer.getAccounts();

    userAddress = accounts[0].address;
    keplrConnected = true;
  }

  // ---------------- PAYMENT + SUBMIT ----------------
  async function payAndSubmit() {
    if (!prompt.trim()) return;

    loading = true;
    error = '';

    try {
      if (!keplrConnected) {
        await connectKeplr();
      }

      await window.keplr.enable(CHAIN_ID);

      const signer = window.keplr.getOfflineSignerOnlyAmino(CHAIN_ID);
      const accounts = await signer.getAccounts();

      // fetch account info
      const accRes = await fetch(`${API}/api/hyperscale/account/${userAddress}`);
      const accData = await accRes.json();

      const signDoc = {
        chain_id: CHAIN_ID,
        account_number: String(accData.account_number || "0"),
        sequence: String(accData.sequence || "0"),
        fee: {
          amount: [{ denom: "arai", amount: "200000000000000" }],
          gas: "200000",
        },
        msgs: [
          {
            type: "cosmos-sdk/MsgSend",
            value: {
              from_address: userAddress,
              to_address: TREASURY,
              amount: [{ denom: "arai", amount: AMOUNT }],
            },
          },
        ],
        memo: "Hyperscale fee",
      };

      const { signed, signature } = await window.keplr.signAmino(
        CHAIN_ID,
        userAddress,
        signDoc
      );

      // broadcast (safe way)
      const broadcastRes = await fetch(
        "https://api-test.republic.vinjan-inc.com/cosmos/tx/v1beta1/txs",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            tx: {
              msg: signed.msgs,
              fee: signed.fee,
              signatures: [signature.signature],
              memo: signed.memo,
            },
            mode: "BROADCAST_MODE_SYNC",
          }),
        }
      );

      const txResult = await broadcastRes.json();

      if (txResult.code) {
        throw new Error(txResult.raw_log || "TX Failed");
      }

      console.log("TX SUCCESS");

      // 👉 payment success → inference
      await submitJob();

    } catch (e) {
      error = e.message;
      loading = false;
    }
  }

  // ---------------- LOAD ----------------
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
    } catch(e) {
      // fallback so UI never breaks
      models = [{
        id: "fallback",
        name: "Fallback Model",
        context_length: 4096,
        pricing: { prompt: "0" }
      }];
    }
    modelsLoading = false;
  }

  // ---------------- SUBMIT ----------------
  async function submitJob() {
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
    }
  }

  // ---------------- POLL ----------------
  async function pollStatus() {
    if (!trackingId) return;

    try {
      const r = await fetch(`${API}/api/hyperscale/status/${trackingId}`);
      const d = await r.json();

      if (d.status === 'completed' || d.status === 'failed' || d.status === 'inferred_only') {
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

  onMount(() => {
    loadMiners();
    loadModels();
  });
</script>