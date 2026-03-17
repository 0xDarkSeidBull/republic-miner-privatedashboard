<script>
  import { API } from '../../stores/app.js';

  let name = '', desc = '', cat = '', url = '', github = '', icon = '';
  let msg = '';
  let msgType = '';

  async function submit() {
    if (!name || !desc || !cat) { msg = 'Please fill all required fields (*)'; msgType = 'error'; return; }
    msg = 'Submitting...'; msgType = 'loading';
    try {
      const r = await fetch(API + '/api/ecosystem/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description: desc, category: cat, url, github, icon })
      });
      if (r.ok) {
        msg = '✓ Project submitted! It will appear after review.';
        msgType = 'success';
        name = desc = cat = url = github = icon = '';
      } else throw new Error();
    } catch {
      msg = 'Submission failed. Try again or DM on Telegram.';
      msgType = 'error';
    }
  }
</script>

<div class="submit-wrap">
  <div class="page-title">SUBMIT<br/>PROJECT</div>
  <div class="page-sub">Add your project to the Republic AI ecosystem directory</div>

  <div class="form-group"><label class="form-label">Project Name *</label><input class="form-input" placeholder="My Republic Project" bind:value={name}/></div>
  <div class="form-group"><label class="form-label">Description *</label><textarea class="form-textarea" placeholder="What does your project do?" bind:value={desc}></textarea></div>
  <div class="form-group">
    <label class="form-label">Category *</label>
    <select class="form-select" bind:value={cat}>
      <option value="">Select category...</option>
      {#each ['AI','Tool','Infrastructure','Explorer','DeFi','Other'] as c}<option>{c}</option>{/each}
    </select>
  </div>
  <div class="form-group"><label class="form-label">Website URL</label><input class="form-input" placeholder="https://yourproject.xyz" bind:value={url}/></div>
  <div class="form-group"><label class="form-label">GitHub</label><input class="form-input" placeholder="https://github.com/..." bind:value={github}/></div>
  <div class="form-group"><label class="form-label">Icon Emoji</label><input class="form-input" placeholder="🚀" maxlength="4" style="max-width:100px" bind:value={icon}/></div>
  <button class="btn-primary" on:click={submit}>SUBMIT FOR REVIEW</button>

  {#if msg}
    <div style="margin-top:14px" class={msgType === 'error' ? 'error-msg' : msgType === 'success' ? '' : 'loading'}
         style:color={msgType === 'success' ? 'var(--green)' : ''}
         style:background={msgType === 'success' ? 'rgba(0,255,136,.05)' : ''}
         style:border={msgType === 'success' ? '1px solid rgba(0,255,136,.2)' : ''}
         style:padding={msgType === 'success' ? '12px' : ''}
         style:font-family={msgType === 'success' ? 'var(--font-mono)' : ''}
         style:font-size={msgType === 'success' ? '11px' : ''}>
      {msg}
    </div>
  {/if}
</div>
