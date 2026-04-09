<script lang="ts">
  import HyperscalePayment from '../HyperscalePayment.svelte';
  
  let prompt = '';
  let inferenceResult = '';
  let isInferring = false;
  let statusMessage = '';
  let statusType = '';
  
  // Your treasury wallet address (jo payment receive karega)
  const TREASURY_ADDRESS = "rai1xcr42hlh85kutaqtmyxw2zu8pr3nk5rks6nlp5";
  
  const runInference = async () => {
    if (!prompt.trim()) {
      alert('Please enter a prompt');
      return;
    }
    
    isInferring = true;
    statusMessage = 'Running inference...';
    statusType = 'pending';
    
    try {
      // Call your backend API
      const response = await fetch('/api/hyperscale/inference', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        inferenceResult = data.result;
        statusMessage = '✅ Inference completed!';
        statusType = 'success';
      } else {
        throw new Error(data.error || 'Inference failed');
      }
    } catch (error) {
      console.error(error);
      statusMessage = `❌ ${error.message}`;
      statusType = 'error';
    } finally {
      isInferring = false;
      setTimeout(() => {
        if (statusType !== 'error') statusMessage = '';
      }, 3000);
    }
  };
  
  const handlePaymentSuccess = async (txHash: string) => {
    console.log('Payment successful:', txHash);
    statusMessage = `✅ Payment confirmed! Running inference...`;
    statusType = 'success';
    await runInference();
  };
  
  const handlePaymentError = (error: string) => {
    statusMessage = `❌ ${error}`;
    statusType = 'error';
    setTimeout(() => {
      statusMessage = '';
    }, 5000);
  };
</script>

<div class="hyperscale-container">
  <div class="header">
    <h1>🚀 Hyperscale AI</h1>
    <p>Pay with RAI, get instant AI inference results</p>
  </div>
  
  <div class="card">
    <div class="form-group">
      <label>📝 Enter your prompt</label>
      <textarea
        bind:value={prompt}
        placeholder="Example: Explain quantum computing in simple terms..."
        rows="5"
      ></textarea>
    </div>
    
    <div class="divider">
      <span>Payment Required</span>
    </div>
    
    <HyperscalePayment
      treasuryAddress={TREASURY_ADDRESS}
      priceInRAI={0.1}
      onPaymentSuccess={handlePaymentSuccess}
      onPaymentError={handlePaymentError}
    />
    
    {#if statusMessage}
      <div class="status {statusType}">
        {statusMessage}
      </div>
    {/if}
    
    {#if isInferring}
      <div class="loading">
        <div class="spinner"></div>
        <span>🤖 AI is thinking...</span>
      </div>
    {/if}
    
    {#if inferenceResult && !isInferring}
      <div class="result">
        <h3>✨ Result:</h3>
        <p>{inferenceResult}</p>
      </div>
    {/if}
  </div>
  
  <div class="footer">
    Powered by Republic AI Testnet | 0.1 RAI per inference
  </div>
</div>

<style>
  .hyperscale-container {
    max-width: 700px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .header {
    text-align: center;
    margin-bottom: 2rem;
  }
  
  .header h1 {
    font-size: 2.5rem;
    background: linear-gradient(135deg, #60a5fa, #34d399);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
  }
  
  .header p {
    color: #9ca3af;
    margin-top: 0.5rem;
  }
  
  .card {
    background: rgba(30, 30, 50, 0.6);
    backdrop-filter: blur(10px);
    border-radius: 24px;
    padding: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .form-group label {
    display: block;
    margin-bottom: 0.5rem;
    color: #d1d5db;
    font-weight: 500;
  }
  
  textarea {
    width: 100%;
    padding: 1rem;
    background: rgba(15, 15, 30, 0.8);
    border: 1px solid #374151;
    border-radius: 16px;
    color: white;
    font-size: 14px;
    resize: vertical;
  }
  
  textarea:focus {
    outline: none;
    border-color: #60a5fa;
  }
  
  .divider {
    position: relative;
    margin: 1.5rem 0;
    text-align: center;
  }
  
  .divider::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 0;
    right: 0;
    height: 1px;
    background: #374151;
  }
  
  .divider span {
    position: relative;
    background: rgba(30, 30, 50, 0.6);
    padding: 0 1rem;
    font-size: 12px;
    color: #6b7280;
  }
  
  .status {
    margin-top: 1rem;
    padding: 0.75rem;
    border-radius: 12px;
    font-size: 14px;
    text-align: center;
  }
  
  .status.success {
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid #10b981;
    color: #34d399;
  }
  
  .status.error {
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid #ef4444;
    color: #fca5a5;
  }
  
  .status.pending {
    background: rgba(59, 130, 246, 0.2);
    border: 1px solid #3b82f6;
    color: #60a5fa;
  }
  
  .loading {
    margin-top: 1rem;
    padding: 1rem;
    background: rgba(59, 130, 246, 0.1);
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    color: #60a5fa;
  }
  
  .spinner {
    width: 20px;
    height: 20px;
    border: 2px solid #60a5fa;
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  .result {
    margin-top: 1.5rem;
    padding: 1.5rem;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 16px;
  }
  
  .result h3 {
    color: #34d399;
    font-size: 14px;
    margin-bottom: 0.75rem;
  }
  
  .result p {
    color: white;
    line-height: 1.6;
  }
  
  .footer {
    text-align: center;
    margin-top: 2rem;
    font-size: 12px;
    color: #6b7280;
  }
</style>