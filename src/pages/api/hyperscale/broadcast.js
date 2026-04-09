export const prerender = false;

export async function POST({ request }) {
  try {
    const { signature, user_address } = await request.json();
    
    console.log(`📡 Broadcasting from ${user_address}...`);
    
    const { StargateClient } = await import('@cosmjs/stargate');
    const { fromBase64 } = await import('@cosmjs/encoding');
    
    const client = await StargateClient.connect('https://rpc-test.republic.vinjan-inc.com');
    const txBytes = fromBase64(signature.signature);
    const result = await client.broadcastTx(txBytes);
    
    if (result.code !== 0) {
      return new Response(JSON.stringify({ 
        success: false, 
        error: result.rawLog 
      }), { headers: { 'Content-Type': 'application/json' } });
    }
    
    console.log('✅ TX:', result.transactionHash);
    return new Response(JSON.stringify({ 
      success: true, 
      txhash: result.transactionHash 
    }), { headers: { 'Content-Type': 'application/json' } });
    
  } catch (error) {
    console.error('❌ Error:', error);
    return new Response(JSON.stringify({ 
      success: false, 
      error: error.message 
    }), { status: 500, headers: { 'Content-Type': 'application/json' } });
  }
}