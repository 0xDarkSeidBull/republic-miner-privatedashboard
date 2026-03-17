<script>
  import { API, showToast } from '../../stores/app.js';

  let username = '', discord = '', moniker = '', wallet = '', raivaloper = '';
  let jobEntries = [{ id: Date.now(), jobId: '', txHash: '' }];
  let hwFile = null;
  let hwPreview = null;
  let submitting = false;
  let success = false;
  let successMsg = '';
  let errorMsg = '';

  function addJob() {
    jobEntries = [...jobEntries, { id: Date.now(), jobId: '', txHash: '' }];
  }

  function removeJob(id) {
    if (jobEntries.length <= 1) { showToast('Minimum 1 job required'); return; }
    jobEntries = jobEntries.filter(j => j.id !== id);
  }

  function handleHwUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) { showToast('File too large! Max 10MB'); return; }
    hwFile = file;
    const reader = new FileReader();
    reader.onload = ev => hwPreview = ev.target.result;
    reader.readAsDataURL(file);
  }

  function removeHw() { hwFile = null; hwPreview = null; }

  async function submit() {
    errorMsg = '';
    if (!username || !discord || !moniker || !wallet || !raivaloper) {
      errorMsg = '⚠ Please fill all required fields.'; return;
    }
    for (const j of jobEntries) {
      if (!j.jobId.trim() || !j.txHash.trim()) {
        errorMsg = '⚠ Please fill Job ID and TX Hash for all jobs.'; return;
      }
    }
    if (!hwFile) { errorMsg = '⚠ Please upload nvidia-smi hardware proof.'; return; }
    submitting = true;
    try {
      const fd = new FormData();
      fd.append('username', username); fd.append('discord', discord);
      fd.append('moniker', moniker); fd.append('wallet', wallet);
      fd.append('raivaloper', raivaloper);
      fd.append('jobs', JSON.stringify(jobEntries.map(j => ({ jobId: j.jobId, txHash: j.txHash }))));
      fd.append('hw_proof', hwFile, hwFile.name);
      const r = await fetch(API + '/api/points/submit', { method: 'POST', body: fd, signal: AbortSignal.timeout(30000) });
      if (r.ok) {
        success = true;
        successMsg = `Successfully submitted ${jobEntries.length} job${jobEntries.length > 1 ? 's' : ''} for ${username}.`;
      } else {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || 'Submission failed');
      }
    } catch(e) {
      errorMsg = `❌ ${e.message || 'Submission failed. Try again.'}`;
    }
    submitting = false;
  }

  function reset() {
    username = discord = moniker = wallet = raivaloper = '';
    jobEntries = [{ id: Date.now(), jobId: '', txHash: '' }];
    hwFile = null; hwPreview = null;
    success = false; successMsg = ''; errorMsg = '';
  }
</script>

<div class="points-wrap">
  <div class="page-title">POINTS<br/><span style="background:linear-gradient(135deg,var(--accent),var(--accent3));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">SUBMISSION</span></div>
  <div class="page-sub">Submit your completed GPU mining jobs to claim Republic AI testnet points.</div>

  {#if success}
    <div class="points-success">
      <div class="points-success-icon">✅</div>
      <h3>SUBMISSION COMPLETE!</h3>
      <p>{successMsg}</p>
      <button class="btn-primary" on:click={reset} style="margin-top:8px;padding:12px 28px;font-size:18px;width:auto">SUBMIT MORE JOBS</button>
    </div>
  {:else}
    <div class="points-note">ℹ️ Fill your details once, then add as many Job ID + TX Hash pairs as you completed.</div>

    <div class="points-card">
      <div class="points-card-title">👤 Your Details</div>
      <div class="points-row">
        <div class="form-group" style="margin-bottom:0"><label class="form-label">Web App Username *</label><input id="pf-username" class="form-input" placeholder="your username" bind:value={username}/></div>
        <div class="form-group" style="margin-bottom:0"><label class="form-label">Discord Username *</label><input class="form-input" placeholder="username#0000" bind:value={discord}/></div>
      </div>
      <div class="points-row" style="margin-top:10px">
        <div class="form-group" style="margin-bottom:0"><label class="form-label">Validator Moniker *</label><input id="pf-moniker" class="form-input" placeholder="MyValidator" bind:value={moniker}/></div>
        <div class="form-group" style="margin-bottom:0"><label class="form-label">Operator Wallet *</label><input id="pf-wallet" class="form-input" placeholder="rai1..." bind:value={wallet}/></div>
      </div>
      <div class="points-row single" style="margin-top:10px">
        <div class="form-group" style="margin-bottom:0"><label class="form-label">Raivaloper Address *</label><input class="form-input" placeholder="raivaloper1..." bind:value={raivaloper}/></div>
      </div>
    </div>

    <div class="points-card">
      <div class="points-card-title">⛏️ Completed Jobs <span style="color:var(--muted);font-size:13px;font-weight:400">({jobEntries.length} job{jobEntries.length > 1 ? 's' : ''})</span></div>
      {#each jobEntries as job, i}
        <div class="job-entry">
          <div class="job-entry-header">
            <span class="job-entry-num">JOB #{i+1}</span>
            {#if jobEntries.length > 1}
              <button class="job-remove" on:click={() => removeJob(job.id)}>✕</button>
            {/if}
          </div>
          <div class="job-grid">
            <div><label class="form-label">Job ID *</label><input class="form-input" placeholder="job_12345..." bind:value={job.jobId}/></div>
            <div><label class="form-label">TX Hash *</label><input class="form-input" placeholder="0xABCD..." bind:value={job.txHash}/></div>
          </div>
        </div>
      {/each}
      <button class="add-job-btn" on:click={addJob}>+ Add Another Job</button>
    </div>

    <div class="points-card">
      <div class="points-card-title">🖥️ Hardware Proof</div>
      <label class="form-label">nvidia-smi Screenshot *</label>
      {#if !hwPreview}
        <label style="display:flex;align-items:center;gap:12px;padding:16px;border:1px dashed var(--border2);cursor:pointer;background:var(--bg3)">
          <input type="file" accept="image/*" style="display:none" on:change={handleHwUpload}/>
          <span style="font-size:22px">📸</span>
          <span style="font-family:var(--font-mono);font-size:11px;color:var(--muted);letter-spacing:.08em">CLICK TO UPLOAD · MAX 10MB · JPG/PNG</span>
        </label>
      {:else}
        <div style="position:relative;display:inline-block;margin-top:8px">
          <img src={hwPreview} alt="hw proof" style="max-width:100%;max-height:200px;border:1px solid var(--border2)"/>
          <button on:click={removeHw} style="position:absolute;top:6px;right:6px;background:rgba(0,0,0,.8);border:none;color:#fff;width:22px;height:22px;cursor:pointer;font-size:12px">✕</button>
        </div>
      {/if}
    </div>

    {#if errorMsg}<div class="error-msg">{errorMsg}</div>{/if}
    <button class="submit-big-btn" disabled={submitting} on:click={submit}>
      {submitting ? '⏳ Submitting...' : '🚀 SUBMIT ALL JOBS'}
    </button>
  {/if}
</div>
