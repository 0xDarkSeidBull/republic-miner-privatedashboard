import { writable } from 'svelte/store';
import { SigningStargateClient } from '@cosmjs/stargate';
import { CHAIN_ID, RPC_URL, REST_URL, REPUBLIC_CHAIN_CONFIG, raiToArai, araiToRai } from '../utils/chainConfig.js';

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
        } catch (e) { return '0.0000'; }
    }

    async function connectWallet() {
    if (!window.keplr) {
        error.set('Please install Keplr wallet extension');
        return null;
    }
    try {
        // ✅ STEP 1: Pehle chain details suggest karo (Details must be full)
        await window.keplr.experimentalSuggestChain(REPUBLIC_CHAIN_CONFIG);
        
        // ✅ STEP 2: Phir enable karo
        await window.keplr.enable(CHAIN_ID);
        
        const key = await window.keplr.getKey(CHAIN_ID);
        // Is point par check karo console mein ki algo badla ya nahi
        console.log("Connected Algo:", key.algo); 

        const userAddress = key.bech32Address;
        address.set(userAddress);
        const bal = await fetchBalance(userAddress);
        balance.set(bal);
        
        return { address: userAddress };
    } catch (e) {
        console.error("Connection Error:", e);
        error.set(e.message);
        return null;
    }
}

    async function transfer(recipientAddress, amountInRAI) {
    loading.set(true);
    error.set('');
    
    try {
        const keplr = window.keplr;
        if (!keplr) throw new Error("Keplr not found");

        await keplr.enable(CHAIN_ID);
        const key = await keplr.getKey(CHAIN_ID);
        const offlineSigner = keplr.getOfflineSigner(CHAIN_ID);

        // ✅ YE HAI ASLI FIX: Fixed Signer Wrapper
        // Isse CosmJS ko force kiya jata hai ki wo Ethereum-style key use kare
        const fixedSigner = {
            getAccounts: async () => [{
                address: key.bech32Address,
                algo: "ethsecp256k1", // Force Ethermint algorithm
                pubkey: key.pubKey,
            }],
            signDirect: async (signerAddress, signDoc) => {
                return offlineSigner.signDirect(signerAddress, signDoc);
            }
        };

        const client = await SigningStargateClient.connectWithSigner(RPC_URL, fixedSigner);

        const araiAmount = raiToArai(amountInRAI);
        
        const msgSend = {
            typeUrl: "/cosmos.bank.v1beta1.MsgSend",
            value: {
                fromAddress: key.bech32Address,
                toAddress: recipientAddress,
                amount: [{ denom: 'arai', amount: araiAmount }]
            }
        };

        const fee = {
            amount: [{ denom: 'arai', amount: "10000000000000000" }], // 0.01 RAI
            gas: "250000"
        };

        // signAndBroadcast use karo jaise OneNov kar raha hai
        const result = await client.signAndBroadcast(
            key.bech32Address,
            [msgSend],
            fee,
            'Hyperscale Job Fee'
        );

        if (result.code !== 0) throw new Error(result.rawLog);

        return result;
    } catch (e) {
        console.error("Transfer Error:", e);
        error.set(e.message);
        throw e;
    } finally {
        loading.set(false);
    }
}

            const client = await SigningStargateClient.connectWithSigner(RPC_URL, fixedSigner);

            const araiAmount = raiToArai(amountInRAI);
            
            const msgSend = {
                typeUrl: "/cosmos.bank.v1beta1.MsgSend",
                value: {
                    fromAddress: key.bech32Address,
                    toAddress: recipientAddress,
                    amount: [{ denom: 'arai', amount: araiAmount }]
                }
            };

            const fee = {
                amount: [{ denom: 'arai', amount: "10000000000000000" }], // 0.01 RAI
                gas: "200000"
            };

            // ✅ Use signAndBroadcast like OneNov
            const result = await client.signAndBroadcast(
                key.bech32Address,
                [msgSend],
                fee,
                'Hyperscale Job Fee - republicstats.xyz'
            );

            if (result.code !== 0) throw new Error(result.rawLog);

            const newBalance = await fetchBalance(key.bech32Address);
            balance.set(newBalance);
            
            return result;
        } catch (e) {
            error.set(e.message);
            throw e;
        } finally {
            loading.set(false);
        }
    }

    return { loading, address, balance, error, connectWallet, transfer };
}