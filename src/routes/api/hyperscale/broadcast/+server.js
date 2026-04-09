// src/routes/api/hyperscale/broadcast/+server.js
import { json } from '@sveltejs/kit';
import { StargateClient } from '@cosmjs/stargate';
import { fromBase64 } from '@cosmjs/encoding';

export async function POST({ request }) {
  try {
    const { signature, user_address } = await request.json();
    
    console.log(`📡 Broadcasting tx from ${user_address}...`);
    
    const client = await StargateClient.connect('https://rpc-test.republic.vinjan-inc.com');
    const txBytes = fromBase64(signature.signature);
    const result = await client.broadcastTx(txBytes);
    
    if (result.code !== 0) {
      console.error('❌ Broadcast failed:', result.rawLog);
      return json({ 
        success: false, 
        error: result.rawLog || 'Transaction broadcast failed' 
      });
    }
    
    console.log('✅ TX Hash:', result.transactionHash);
    return json({ 
      success: true, 
      txhash: result.transactionHash 
    });
    
  } catch (error) {
    console.error('Server error:', error);
    return json({ 
      success: false, 
      error: error.message 
    }, { status: 500 });
  }
}