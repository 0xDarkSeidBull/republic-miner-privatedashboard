export const CHAIN_ID = 'raitestnet_77701-1';
export const RPC_URL = 'https://rpc-republic.onenov.xyz';
export const REST_URL = 'https://api-republic.onenov.xyz';
export const TREASURY_ADDRESS = 'rai1alt2884lvwzlzg6l03eaplry7a0ytx0wf3k889';
export const RAI_FEE = 10;

export const REPUBLIC_CHAIN_CONFIG = {
  chainId: CHAIN_ID,
  chainName: "Republic AI Testnet",
  rpc: RPC_URL,
  rest: REST_URL,
  bip44: {
    coinType: 60
  },
  bech32Config: {
    bech32PrefixAccAddr: "rai",
    bech32PrefixAccPub: "raipub",
    bech32PrefixValAddr: "raivaloper",
    bech32PrefixValPub: "raivaloperpub",
    bech32PrefixConsAddr: "raivalcons",
    bech32PrefixConsPub: "raivalconspub"
  },
  currencies: [
    {
      coinDenom: "RAI",
      coinMinimalDenom: "arai",
      coinDecimals: 18
    }
  ],
  feeCurrencies: [
    {
      coinDenom: "RAI",
      coinMinimalDenom: "arai",
      coinDecimals: 18,
      gasPriceStep: {
        low: 20000000000,
        average: 25000000000,
        high: 30000000000
      }
    }
  ],
  stakeCurrency: {
    coinDenom: "RAI",
    coinMinimalDenom: "arai",
    coinDecimals: 18
  },
  // ✅ EXACT ONE NOV FEATURES
  features: ["eth-address-gen", "eth-key-sign", "eth-secp256k1-cosmos"],
  beta: true
};

export function raiToArai(amountInRAI) {
  if (!amountInRAI) return "0";
  return (BigInt(Math.floor(amountInRAI * 1e9)) * BigInt(1e9)).toString();
}

export function araiToRai(amountInArai) {
  if (!amountInArai) return "0.0000";
  return (Number(BigInt(amountInArai) / BigInt(1e14)) / 10000).toFixed(4);
}