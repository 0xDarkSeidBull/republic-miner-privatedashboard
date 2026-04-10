// src/lib/utils/chainConfig.js

export const CHAIN_ID = 'raitestnet_77701-1';
// Official OneNov Endpoints
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
  
  // ✅ IMPORTANT: Ye features missing the, inke bina pubKey mismatch aayega
  features: [
    'eth-address-gen', 
    'eth-key-sign', 
    'eth-secp256k1-cosmos', 
    'stargate', 
    'no-legacy-stdTx'
  ],

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
    // OneNov optimized gas price
    gasPriceStep: { 
        low: 10000000000, 
        average: 25000000000, 
        high: 40000000000 
    },
  }],
  stakeCurrency: {
    coinDenom: 'RAI',
    coinMinimalDenom: 'arai',
    coinDecimals: 18,
  },
};

/**
 * Converts RAI to arai (BigInt string)
 * Use BigInt to avoid precision loss with 18 decimals
 */
export function raiToArai(amountInRAI) {
  if (!amountInRAI) return "0";
  try {
    const raiStr = amountInRAI.toString();
    const [integer, fraction = ""] = raiStr.split(".");
    const paddedFraction = fraction.padEnd(18, "0").slice(0, 18);
    return (BigInt(integer) * BigInt(10) ** BigInt(18) + BigInt(paddedFraction)).toString();
  } catch (e) {
    console.error("Conversion error:", e);
    return "0";
  }
}

/**
 * Converts arai to RAI (String)
 */
export function araiToRai(amountInArai) {
  if (!amountInArai || amountInArai === "0") return "0.0000";
  try {
    const araiBI = BigInt(amountInArai);
    const divisor = BigInt(10) ** BigInt(18);
    const integerPart = araiBI / divisor;
    const fractionalPart = araiBI % divisor;
    return `${integerPart}.${fractionalPart.toString().padStart(18, '0').slice(0, 4)}`;
  } catch (e) {
    return "0.0000";
  }
}