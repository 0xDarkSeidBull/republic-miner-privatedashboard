<script lang="ts">
  import { onMount } from 'svelte';
  
  export let treasuryAddress: string;
  export let priceInRAI: number = 0.1;
  export let onPaymentSuccess: (txHash: string) => void;
  export let onPaymentError: (error: string) => void;
  
  let loading = false;
  let address: string | null = null;
  let balance: string = "0";
  let isPaid = false;
  let txHash: string | null = null;
  
  let keplr: any;
  let client: any;
  
  const CHAIN_CONFIG = {
    chainId: "raitestnet_77701-1",
    chainName: "Republic AI Testnet",
    rpc: "https://rpc.republicai.io",
    rest: "https://rest.republicai.io",
    bech32Prefix: "rai",
    currencies: [{
      coinDenom: "RAI",
      coinMinimalDenom: "arai",
      coinDecimals: 18,
    }],
    feeCurrencies: [{
      coinDenom: "RAI",
      coinMinimalDenom: "arai",
      coinDecimals: 18,
    }],
    gasPriceStep: { low: 1, average: 1.5, high: 2 },
  };
  
  const connectWallet = async () => {
    if (!window.keplr) {
      alert("Please install Keplr wallet extension from keplr.app");
      window.open("https://www.keplr.app/download", "_blank");
      return;
    }
    
    loading = true;
    try {
      keplr = window.keplr;
      
      // Suggest chain
      await keplr.experimentalSuggestChain({
        chainId: CHAIN_CONFIG.chainId,
        chainName: CHAIN_CONFIG.chainName,
        rpc: CHAIN_CONFIG.rpc,
        rest: CHAIN_CONFIG.rest,
        bip44: { coinType: 118 },
        bech32Config: {
          bech32PrefixAccAddr: CHAIN_CONFIG.bech32Prefix,
          bech32PrefixAccPub: `${CHAIN_CONFIG.bech32Prefix}pub`,
          bech32PrefixValAddr: `${CHAIN_CONFIG.bech32Prefix}valoper`,
          bech32PrefixValPub: `${CHAIN_CONFIG.bech32Prefix}valoperpub`,
          bech32PrefixConsAddr: `${CHAIN_CONFIG.bech32Prefix}valcons`,
          bech32PrefixConsPub: `${CHAIN_CONFIG.bech32Prefix}valconspub`,
        },
        currencies: CHAIN_CONFIG.currencies,
        feeCurrencies: CHAIN_CONFIG.feeCurrencies,
        gasPriceStep: CHAIN_CONFIG.gasPriceStep,
      });
      
      await keplr.enable(CHAIN_CONFIG.chainId);
      const offlineSigner = keplr.getOfflineSigner(CHAIN_CONFIG.chainId);
      const accounts = await offlineSigner.getAccounts();
      address = accounts[0].address;
      
      // Import SigningStargateClient dynamically
      const { SigningStargateClient } = await import('@cosmjs/stargate');
      client = await SigningStargateClient.connectWithSigner(
        CHAIN_CONFIG.rpc,
        offlineSigner
      );
      
      const balanceResponse = await client.getBalance(address, "arai");
      balance = (parseInt(balanceResponse.amount) / 1e18).toFixed(6);
      
    } catch (error) {
      console.error(error);
      alert(`Connection failed: ${error.message}`);
    } finally {
      loading = false;
    }
  };
  
  const transfer = async () => {
    if (!client || !address) {
      await connectWallet();
    }
    
    const currentBalance = parseFloat(balance);
    if (currentBalance < priceInRAI) {
      onPaymentError(`Insufficient balance! You have ${balance} RAI, need ${priceInRAI} RAI`);
      return;
    }
    
    loading = true;
    try {
      const amount = [{ 
        denom: "arai", 
        amount: Math.floor(priceInRAI * 1e18).toString() 
      }];
      
      const fee = { 
        amount: [{ denom: "arai", amount: "10000000000000000" }],
        gas: "200000" 
      };
      
      const result = await client.sendTokens(
        address,
        treasuryAddress,
        amount,
        fee,
        "Hyperscale AI Payment via Republic Stats"
      );
      
      if (result.code === 0) {
        isPaid = true;
        txHash = result.transactionHash;
        onPaymentSuccess(result.transactionHash);
      } else {
        onPaymentError(`Transfer failed: ${result.rawLog}`);
      }
    } catch (error) {
      onPaymentError(error.message);
    } finally {
      loading = false;
    }
  };
</script>

<div class="hyperscale-payment">
  {#if !address}
    <button
      on:click={connectWallet}
      disabled={loading}
      class="btn btn-primary"
    >
      {loading ? '⏳ Connecting...' : '🔌 Connect Keplr Wallet'}
    </button>
  {:else if !isPaid}
    <div class="wallet-info">
      <div class="wallet-address">
        📡 {address.slice(0, 10)}...{address.slice(-8)}
      </div>
      <div class="wallet-balance">
        💰 Balance: {parseFloat(balance).toFixed(4)} RAI
      </div>
    </div>
    <button
      on:click={transfer}
      disabled={loading}
      class="btn btn-success"
    >
      {loading ? '⏳ Processing...' : `💸 Pay ${priceInRAI} RAI & Run Inference`}
    </button>
  {:else}
    <div class="payment-success">
      ✅ Payment successful!
      <div class="tx-hash">TX: {txHash?.slice(0, 20)}...</div>
    </div>
  {/if}
</div>

<style>
  .hyperscale-payment {
    margin-top: 1rem;
  }
  
  .btn {
    width: 100%;
    padding: 12px 24px;
    border: none;
    border-radius: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-primary {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    color: white;
  }
  
  .btn-primary:hover:not(:disabled) {
    transform: translateY(-2px);
    opacity: 0.9;
  }
  
  .btn-success {
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
  }
  
  .btn-success:hover:not(:disabled) {
    transform: translateY(-2px);
    opacity: 0.9;
  }
  
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .wallet-info {
    background: rgba(15, 15, 30, 0.6);
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 12px;
  }
  
  .wallet-address {
    font-family: monospace;
    font-size: 13px;
    color: white;
  }
  
  .wallet-balance {
    font-size: 12px;
    color: #34d399;
    margin-top: 4px;
  }
  
  .payment-success {
    padding: 12px;
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid #10b981;
    border-radius: 12px;
    color: #34d399;
    text-align: center;
  }
  
  .tx-hash {
    font-size: 11px;
    color: #6b7280;
    margin-top: 4px;
  }
</style>