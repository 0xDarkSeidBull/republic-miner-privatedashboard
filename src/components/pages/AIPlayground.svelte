<script>
  import { SigningStargateClient } from "@cosmjs/stargate";
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
  let userAddress = '';

  const CHAIN_ID = "raitestnet_77701-1";
  const RPC = "https://rpc-test.republic.vinjan-inc.com";

  const TREASURY = "rai1alt2884lvwzlzg6l03eaplry7a0ytx0wf3k889";
  const RAI_FEE = "10000000000000000000"; // 10 RAI

  // ---------------- COMPUTED ----------------
  $: filteredModels = models.filter(m =>
    m.id.toLowerCase().includes(modelSearch.toLowerCase()) ||
    m.name.toLowerCase().includes(modelSearch.toLowerCase())
  );

  $: selectedModelInfo = models.find(m => m.id === selectedModel);

  // ---------------- KEPLR CONNECT ----------------
  async function connectKeplr() {
    try {
      if (!window.keplr) throw new Error("Install Keplr wallet");

      await window.keplr.enable(CHAIN_ID);

      const signer = window.keplr.getOfflineSigner(CHAIN_ID);
      const accounts = await signer.getAccounts();

      userAddress = accounts[0].address;
      keplrConnected = true;

    } catch (e) {
      error = e.message;
    }
  }

  // ---------------- PAYMENT + INFERENCE ----------------
  async function payAndSubmit() {
    if (!prompt.trim()) return;

    loading = true;
    error = '';

    try {
      if (!keplrConnected) {
        await connectKeplr();
      }


      const signer = window.keplr.getOfflineSigner(CHAIN_ID);

      const client = await SigningStargateClient.connectWithSigner(RPC, signer);

      // 💸 SEND 10 RAI
      const tx = await client.sendTokens(
        userAddress,
        TREASURY,
        [{ denom: "arai", amount: RAI_FEE }],
        {
          amount: [{ denom: "arai", amount: "200000000000000" }],
          gas: "200000"
        },
        "Hyperscale fee"
      );

      console.log("TX SUCCESS:", tx.transactionHash);

      // 🚀 AFTER PAYMENT → SUBMIT JOB
      await submitJob();

    } catch (e) {
      error = e.message;
      loading = false;
    }
  }

  // ---------------- LOAD DATA ----------------
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
      // fallback
      models = [{
        id: "fallback",
        name: "Fallback Model",
        context_length: 4096,
        pricing: { prompt: "0" }
      }];
    }
    modelsLoading = false;
  }

  // ---------------- SUBMIT JOB ----------------
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