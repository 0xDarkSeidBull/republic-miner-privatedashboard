import { writable } from 'svelte/store';
import { SigningStargateClient } from '@cosmjs/stargate';
import { 
  CHAIN_ID, 
  RPC_URL, 
  REST_URL, 
  REPUBLIC_CHAIN_CONFIG, 
  raiToArai, 
  araiToRai 
} from '$lib/utils/chainConfig.js';

export function useKeplrTransfer() {
  const loading = writable(false);
  const address = writable(null);
  const balance = writable('0');
  const error = writable('');

  async function fetchBalance(addr) {
    try {
      const res = await fetch(`${REST_URL}/cosmos/bank/v1beta1/balances/${addr}`);
      const data = await res.json();
      const araiBalance = data.balances?.find(b => b.denom === 'arai');
      return araiBalance ? araiToRai(araiBalance.amount) : '0.0000';
    } catch(e) {
      return '0.0000';
    }
  }

  async function connectWallet() {
    if (!window.keplr) {
      error.set('Please install Keplr wallet extension');
      return null;
    }

    loading.set(true);
    error.set('');

    try {
      await window.keplr.experimentalSuggestChain(REPUBLIC_CHAIN_CONFIG);
      await window.keplr.enable(CHAIN_ID);
      
      // ✅ OneNov exactly yahi use kar raha hai
      const offlineSigner = window.keplr.getOfflineSigner(CHAIN_ID);
      const accounts = await offlineSigner.getAccounts();
      const userAddress = accounts[0].address;
      
      address.set(userAddress);
      
      const bal = await fetchBalance(userAddress);
      balance.set(bal);
      
      loading.set(false);
      return { offlineSigner, address: userAddress };
      
    } catch (e) {
      console.error('Connection error:', e);
      error.set(e.message);
      loading.set(false);
      return null;
    }
  }

  async function transfer(recipientAddress, amountInRAI) {
    loading.set(true);
    error.set('');
    
    try {
      const connection = await connectWallet();
      if (!connection) throw new Error('Wallet not connected');
      
      const { offlineSigner, address: fromAddress } = connection;
      
      // ✅ OneNov ka exact method - signAndBroadcast
      const client = await SigningStargateClient.connectWithSigner(
        RPC_URL,
        offlineSigner
      );

      const araiAmount = raiToArai(amountInRAI);
      
      // Create message exactly like OneNov
      const sendMsg = {
        typeUrl: '/cosmos.bank.v1beta1.MsgSend',
        value: {
          fromAddress: fromAddress,
          toAddress: recipientAddress,
          amount: [{ denom: 'arai', amount: araiAmount }]
        }
      };

      // Fee structure exactly like OneNov
      const fee = {
        amount: [{ 
          denom: 'arai', 
          amount: (0.01 * 10 ** 18).toFixed(0)  // 0.01 RAI
        }],
        gas: '400000'  // OneNov uses 400000 gas
      };

      // ✅ Use signAndBroadcast - NOT sendTokens
      const result = await client.signAndBroadcast(
        fromAddress,
        [sendMsg],
        fee,
        'Hyperscale inference fee — republicstats.xyz'
      );

      if (result.code !== 0) {
        throw new Error(`Transaction failed: ${result.rawLog}`);
      }

      const newBalance = await fetchBalance(fromAddress);
      balance.set(newBalance);
      
      loading.set(false);
      return result;
      
    } catch (e) {
      console.error('Transfer error:', e);
      error.set(e.message);
      loading.set(false);
      throw e;
    }
  }

  return {
    loading,
    address,
    balance,
    error,
    connectWallet,
    transfer
  };
}