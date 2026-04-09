// src/lib/hooks/useKeplrTransfer.js
import { writable } from 'svelte/store';
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

  async function fetchAccountInfo(addr) {
    const res = await fetch(`${REST_URL}/cosmos/auth/v1beta1/accounts/${addr}`);
    const data = await res.json();
    const acc = data.account?.base_account || data.account;
    return {
      accountNumber: acc.account_number || '0',
      sequence: acc.sequence || '0',
    };
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
      
      const key = await window.keplr.getKey(CHAIN_ID);
      const userAddress = key.bech32Address;
      
      address.set(userAddress);
      
      const bal = await fetchBalance(userAddress);
      balance.set(bal);
      
      loading.set(false);
      return { address: userAddress };
      
    } catch (e) {
      console.error('Connection error:', e);
      error.set(e.message);
      loading.set(false);
      return null;
    }
  }

  async function transfer(recipientAddress, amountInRAI, API_BASE) {
    loading.set(true);
    error.set('');
    
    try {
      const connection = await connectWallet();
      if (!connection) throw new Error('Wallet not connected');
      
      const fromAddress = connection.address;
      
      // Get account info
      const { accountNumber, sequence } = await fetchAccountInfo(fromAddress);
      
      // Prepare amount
      const araiAmount = raiToArai(amountInRAI);
      
      // Create signDoc (Amino format - works with Ethermint)
      const signDoc = {
        chain_id: CHAIN_ID,
        account_number: accountNumber,
        sequence: sequence,
        fee: {
          amount: [{ denom: 'arai', amount: '4000000000000000' }],
          gas: '250000',
        },
        msgs: [{
          type: 'cosmos-sdk/MsgSend',
          value: {
            from_address: fromAddress,
            to_address: recipientAddress,
            amount: [{ denom: 'arai', amount: araiAmount }],
          },
        }],
        memo: 'Hyperscale inference fee — republicstats.xyz',
      };

      // Sign with Keplr (Amino)
      const signed = await window.keplr.signAmino(
        CHAIN_ID, 
        fromAddress, 
        signDoc,
        { preferNoSetFee: true }
      );

      // Broadcast via backend (CRITICAL for Ethermint)
      const broadcastRes = await fetch(`/api/hyperscale/broadcast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          signed_doc: signed.signed,
          signature: signed.signature,
          user_address: fromAddress,
        }),
      });
      
      const broadcastData = await broadcastRes.json();
      
      if (!broadcastData.success) {
        throw new Error(broadcastData.error || 'Broadcast failed');
      }
      
      // Update balance
      const newBalance = await fetchBalance(fromAddress);
      balance.set(newBalance);
      
      loading.set(false);
      return { 
        code: 0, 
        transactionHash: broadcastData.txhash 
      };
      
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