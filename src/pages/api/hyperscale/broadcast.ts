// Astro API Endpoint
export const prerender = false;

export async function POST({ request }) {
  try {
    const body = await request.json();
    const { signature, user_address } = body;
    
    console.log(`📡 Broadcasting tx from ${user_address}...`);
    
    // Dynamically import CosmJS (Astro SSR compatibility)
    const { StargateClient } = await import('@cosmjs/stargate');
    const { fromBase64 } = await import('@cosmjs/encoding');
    
    const client = await StargateClient.connect('https://rpc-test.republic.vinjan-inc.com');
    const txBytes = fromBase64(signature.signature);
    const result = await client.broadcastTx(txBytes);
    
    if (result.code !== 0) {
      console.error('❌ Broadcast failed:', result.rawLog);
      return new Response(JSON.stringify({ 
        success: false, 
        error: result.rawLog || 'Transaction broadcast failed' 
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    console.log('✅ TX Hash:', result.transactionHash);
    return new Response(JSON.stringify({ 
      success: true, 
      txhash: result.transactionHash 
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
    
  } catch (error) {
    console.error('Server error:', error);
    return new Response(JSON.stringify({ 
      success: false, 
      error: error.message 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}