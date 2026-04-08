// Yeh exact copy kar apni file mein
import { SigningStargateClient } from '@cosmjs/stargate';

const TREASURY = 'rai1alt2884lvwzlzg6l03eaplry7a0ytx0wf3k889';
const RAI_FEE = 10;

const REPUBLIC_CHAIN = {
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
  feeCurrencies: [{ coinDenom: 'RAI', coinMinimalDenom: 'arai', coinDecimals: 18, gasPriceStep: { low: 10000000000, average: 25000000000, high: 40000000000 } }],
  stakeCurrency: { coinDenom: 'RAI', coinMinimalDenom: 'arai', coinDecimals: 18 },
};

async function connectKeplr() {
  if (!window.keplr) {
    keplrError = 'Please install Keplr extension';
    return;
  }
  await window.keplr.experimentalSuggestChain(REPUBLIC_CHAIN);
  await window.keplr.enable(REPUBLIC_CHAIN.chainId);
  const offlineSigner = window.keplr.getOfflineSigner(REPUBLIC_CHAIN.chainId);
  const accounts = await offlineSigner.getAccounts();
  userAddress = accounts[0].address;
  keplrConnected = true;
}

async function payAndInfer() {
  if (!prompt.trim()) return;
  
  paymentStep = 'paying';
  loading = true;
  
  try {
    if (!keplrConnected) await connectKeplr();
    
    const offlineSigner = window.keplr.getOfflineSigner(REPUBLIC_CHAIN.chainId);
    const accounts = await offlineSigner.getAccounts();
    const fromAddress = accounts[0].address;
    
    const client = await SigningStargateClient.connectWithSigner(REPUBLIC_CHAIN.rpc, offlineSigner);
    
    const amount = [{ denom: "arai", amount: Math.floor(RAI_FEE * 1e18).toString() }];
    const fee = { amount: [{ denom: "arai", amount: "10000000000" }], gas: "200000" };
    
    const result = await client.sendTokens(fromAddress, TREASURY, amount, fee, "Hyperscale inference fee");
    
    if (result.code !== 0) throw new Error(result.rawLog);
    
    paymentTxHash = result.transactionHash;
    paymentStep = 'ready';
    await submitJob();
    
  } catch (e) {
    paymentError = e.message;
    paymentStep = 'idle';
    loading = false;
  }
}