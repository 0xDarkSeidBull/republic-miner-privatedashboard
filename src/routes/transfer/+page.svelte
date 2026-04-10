<script>
  import { onMount } from 'svelte';

  let walletAddress = '';
  let walletBalance = '0';
  let loading = false;
  let txHash = '';
  let error = '';

  const CHAIN_CONFIG = {
    chainId: 'raitestnet_77701-1',
    chainName: 'Republic Testnet',
    rpc: 'https://rpc-republic.onenov.xyz',
    rest: 'https://api-republic.onenov.xyz',
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
    }],
    gasPriceStep: { low: 10000000000, average: 25000000000, high: 40000000000 },
  };

  const TREASURY = 'rai1alt2884lvwzlzg6l03eaplry7a0ytx0wf3k889';

  async function connectWallet() {
    if (!window.keplr) {
      error = 'Please install Keplr';
      return;
    }
    loading = true;
    error = '';
    try {
      await window.keplr.experimentalSuggestChain(CHAIN_CONFIG);
      await window.keplr.enable(CHAIN_CONFIG.chainId);
      // ✅ Using getOfflineSignerOnlyAmino as suggested by OneNov
      const offlineSigner = window.keplr.getOfflineSignerOnlyAmino(CHAIN_CONFIG.chainId);
      const accounts = await offlineSigner.getAccounts();
      walletAddress = accounts[0].address;
      fetchBalance();
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  async function fetchBalance() {
    try {
      const res = await fetch(`${CHAIN_CONFIG.rest}/cosmos/bank/v1beta1/balances/${walletAddress}`);
      const data = await res.json();
      const arai = data.balances?.find(b => b.denom === 'arai');
      walletBalance = arai ? (parseInt(arai.amount) / 1e18).toString() : '0';
    } catch(e) {}
  }

  async function transferRAI(amount) {
    if (!walletAddress) return;
    loading = true;
    error = '';
    txHash = '';
    try {
      const { SigningStargateClient } = await import('@cosmjs/stargate');
      const offlineSigner = window.keplr.getOfflineSignerOnlyAmino(CHAIN_CONFIG.chainId);
      const client = await SigningStargateClient.connectWithSigner(CHAIN_CONFIG.rpc, offlineSigner);

      const amountInArai = Math.floor(amount * 1e18).toString();
      const msg = {
        typeUrl: '/cosmos.bank.v1beta1.MsgSend',
        value: {
          fromAddress: walletAddress,
          toAddress: TREASURY,
          amount: [{ denom: 'arai', amount: amountInArai }],
        },
      };

      const fee = {
        amount: [{ denom: 'arai', amount: (0.01 * 1e18).toString() }],
        gas: '200000',
      };

      const result = await client.signAndBroadcast(walletAddress, [msg], fee, `Pay ${amount} RAI`);
      if (result.code !== 0) throw new Error(result.rawLog);
      txHash = result.transactionHash;
      fetchBalance();
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }
</script>

<div style="max-width: 500px; margin: 100px auto; padding: 30px; background: #0D0D1A; border: 1px solid #1E1E2A; border-radius: 12px; color: #E8E8F0; font-family: 'Courier New', monospace; text-align: center;">
  <h2 style="color: #FF6B00; letter-spacing: 2px;">⚡ REPUBLIC TRANSFER</h2>
  <p style="font-size: 11px; color: #666; margin-bottom: 20px;">Simple RAI sender powered by OneNov implementation</p>
  
  <hr style="border: 0; border-top: 1px solid #1E1E2A; margin: 20px 0;" />

  {#if !walletAddress}
    <button on:click={connectWallet} disabled={loading} style="width: 100%; padding: 14px; background: #FF6B00; color: #000; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-family: inherit;">
      {loading ? 'INITIALIZING...' : 'CONNECT KEPLR WALLET'}
    </button>
  {:else}
    <div style="text-align: left;">
      <p style="color: #666; font-size: 11px;">CONNECTED ADDRESS:</p>
      <p style="color: #4ADE80; font-size: 13px; word-break: break-all; margin-bottom: 20px;">{walletAddress}</p>
      
      <div style="background: rgba(255,107,0,0.05); padding: 15px; border-radius: 8px; border-left: 3px solid #FF6B00;">
        <p style="color: #666; font-size: 11px; margin: 0;">AVAILABLE BALANCE:</p>
        <p style="font-size: 24px; font-weight: bold; margin: 5px 0;">{parseFloat(walletBalance).toFixed(4)} RAI</p>
      </div>
      
      <button on:click={() => transferRAI(10)} disabled={loading} style="width: 100%; margin-top: 25px; padding: 14px; background: transparent; border: 1px solid #FF6B00; color: #FF6B00; border-radius: 6px; cursor: pointer; font-family: inherit; font-weight: bold;">
        {loading ? 'SENDING...' : 'SEND 10 RAI TO TREASURY'}
      </button>

      {#if txHash}
        <div style="margin-top: 20px; padding: 12px; background: rgba(74, 222, 128, 0.1); border: 1px solid #4ADE80; border-radius: 6px;">
          <p style="color: #4ADE80; margin: 0; font-size: 12px; font-weight: bold;">✅ TRANSACTION SUCCESSFUL</p>
          <a href="https://explorer.republicai.io/tx/{txHash}" target="_blank" style="color: #4ADE80; font-size: 11px; word-break: break-all; display: block; margin-top: 5px; text-decoration: none; border-bottom: 1px dashed #4ADE80; width: fit-content;">View on Explorer ↗</a>
        </div>
      {/if}
    </div>
  {/if}

  {#if error}
    <div style="margin-top: 20px; padding: 12px; background: rgba(239, 68, 68, 0.1); border: 1px solid #EF4444; border-radius: 6px; color: #EF4444; font-size: 12px; text-align: left;">
      ❌ ERROR: {error}
    </div>
  {/if}
</div>