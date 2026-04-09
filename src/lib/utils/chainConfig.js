// src/lib/utils/chainConfig.js
export const CHAIN_ID = 'raitestnet_77701-1';
// OneNov ke official RPC & REST endpoints jo tumne verify kiye
export const RPC_URL = 'https://rpc-republic.onenov.xyz';
export const REST_URL = 'https://api-republic.onenov.xyz';
export const TREASURY_ADDRESS = 'rai1alt2884lvwzlzg6l03eaplry7a0ytx0wf3k889';
export const RAI_FEE = 10;

export const REPUBLIC_CHAIN_CONFIG = {
  chainId: CHAIN_ID,
  chainName: 'Republic Testnet',
  rpc: RPC_URL,
  rest: REST_URL,
  // ✅ CRITICAL: coinType 60 for Ethermint chains
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
  // Updated gas price from node_info
  gasPriceStep: { low: 10000000000, average: 25000000000, high: 40000000000 },
  stakeCurrency: {
    coinDenom: 'RAI',
    coinMinimalDenom: 'arai',
    coinDecimals: 18,
  },
};

export function raiToArai(amountInRAI) {
  return Math.floor(amountInRAI * 1e18).toString();
}

export function araiToRai(amountInArai) {
  return (parseInt(amountInArai) / 1e18).toString();
}