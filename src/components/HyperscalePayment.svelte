<script>
  export let treasuryAddress;
  export let priceInRAI = 10;
  export let onPaymentSuccess;
  export let onPaymentError;

  let loading = false;
  let address = null;
  let balance = '0';
  let isPaid = false;
  let txHash = null;

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
    currencies: [{ coinDenom: 'RAI', coinMinimalDenom: 'arai', coinDecimals: 18 }],
    feeCurrencies: [{ coinDenom: 'RAI', coinMinimalDenom: 'arai', coinDecimals: 18 }],
    gasPriceStep: { low: 10000000000, average: 25000000000, high: 40000000000 },
    stakeCurrency: { coinDenom: 'RAI', coinMinimalDenom: 'arai', coinDecimals: 18 },
  };

  let client = null;

  const connectWallet = async () => {
    if (!window.keplr) {
      alert('Please install Keplr wallet');
      return;
    }
    loading = true;
    try {
      await window.keplr.experimentalSuggestChain(CHAIN_CONFIG);
      await window.keplr.enable(CHAIN_CONFIG.chainId);

      const offlineSigner = window.keplr.getOfflineSignerOnlyAmino(CHAIN_CONFIG.chainId);
      const accounts = await offlineSigner.getAccounts();
      address = accounts[0].address;

      const { SigningStargateClient } = await import('@cosmjs/stargate');
      client = await SigningStargateClient.connectWithSigner(CHAIN_CONFIG.rpc, offlineSigner);

      const bal = await client.getBalance(address, 'arai');
      balance = (parseInt(bal.amount) / 1e18).toFixed(4);
    } catch(e) {
      alert(`Connection failed: ${e.message}`);
    } finally {
      loading = false;
    }
  };

  const transfer = async () => {
    if (!client || !address) await connectWallet();
    if (!client) return;

    if (parseFloat(balance) < priceInRAI) {
      onPaymentError(`Insufficient balance. Have ${balance} RAI, need ${priceInRAI} RAI`);
      return;
    }

    loading = true;
    try {
      const result = await client.signAndBroadcast(
        address,
        [{
          typeUrl: '/cosmos.bank.v1beta1.MsgSend',
          value: {
            fromAddress: address,
            toAddress: treasuryAddress,
            amount: [{ denom: 'arai', amount: Math.floor(priceInRAI * 1e18).toString() }]
          }
        }],
        {
          amount: [{ denom: 'arai', amount: '10000000000000000' }],
          gas: '200000'
        },
        'Hyperscale inference fee — republicstats.xyz'
      );

      if (result.code === 0) {
        isPaid = true;
        txHash = result.transactionHash;
        onPaymentSuccess(result.transactionHash);
      } else {
        onPaymentError(`Failed: ${result.rawLog}`);
      }
    } catch(e) {
      onPaymentError(e.message);
    } finally {
      loading = false;
    }
  };
</script>

{#if !address}
  <button on:click={connectWallet} disabled={loading}
    style="width:100%;background:var(--accent);color:#000;border:none;padding:13px;font-family:var(--font-mono);font-size:13px;font-weight:700;border-radius:8px;cursor:pointer">
    {loading ? '⏳ Connecting...' : '🔗 Connect Keplr'}
  </button>
{:else if !isPaid}
  <div style="background:var(--bg1);border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:12px">
    <div style="font-family:var(--font-mono);font-size:11px;color:#4ADE80">✅ {address.slice(0,14)}...{address.slice(-6)}</div>
    <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-top:4px">Balance: <span style="color:#4ADE80">{balance} RAI</span></div>
  </div>
  <button on:click={transfer} disabled={loading}
    style="width:100%;background:var(--accent);color:#000;border:none;padding:13px;font-family:var(--font-mono);font-size:13px;font-weight:700;border-radius:8px;cursor:pointer">
    {loading ? '⏳ Processing...' : `⚡ PAY ${priceInRAI} RAI & SUBMIT`}
  </button>
{:else}
  <div style="background:rgba(74,222,128,0.1);border:1px solid rgba(74,222,128,0.3);border-radius:8px;padding:12px;text-align:center">
    <div style="color:#4ADE80;font-weight:700">✅ Payment Successful!</div>
    <div style="font-family:var(--font-mono);font-size:10px;color:var(--muted);margin-top:4px">{txHash?.slice(0,30)}...</div>
  </div>
{/if}
