// src/lib/utils/chainConfig.js

export const CHAIN_ID = 'raitestnet_77701-1';
export const RPC_URL = 'https://rpc-test.republic.vinjan-inc.com';
export const REST_URL = 'https://api-test.republic.vinjan-inc.com';
export const TREASURY_ADDRESS = 'rai1alt2884lvwzlzg6l03eaplry7a0ytx0wf3k889';
export const RAI_FEE = 10;

export const REPUBLIC_CHAIN_CONFIG = {
  chainId: CHAIN_ID,
  chainName: 'Republic AI Testnet',
  rpc: RPC_URL,
  rest: REST_URL,
  
  // ✅ CRITICAL: Ethermint configuration
  bip44: {
    coinType: 60  // Ethereum-style
  },
  
  // ✅ TELL KEPLR THIS IS ETHERMINT
  features: ['ethsecp256k1'],
  
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
    coinGeckoId: '',
  }],
  
  feeCurrencies: [{
    coinDenom: 'RAI',
    coinMinimalDenom: 'arai',
    coinDecimals: 18,
    coinGeckoId: '',
    gasPriceStep: {
      low: 10000000000,
      average: 25000000000,
      high: 40000000000,
    },
  }],
  
  stakeCurrency: {
    coinDenom: 'RAI',
    coinMinimalDenom: 'arai',
    coinDecimals: 18,
  },
};

// Helper: Convert RAI to arai (smallest unit)
export function raiToArai(amountInRAI) {
  const parts = amountInRAI.toString().split('.');
  const whole = parts[0] || '0';
  let decimal = parts[1] || '';
  decimal = decimal.padEnd(18, '0').slice(0, 18);
  return (BigInt(whole) * BigInt(10n ** 18n) + BigInt(decimal)).toString();
}

// Helper: Convert arai to RAI
export function araiToRai(amountInArai) {
  const num = Number(BigInt(amountInArai) / BigInt(10n ** 14n)) / 10000;
  return num.toFixed(4);
}