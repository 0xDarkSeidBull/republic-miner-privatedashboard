<script>
  import { toastMsg } from '$lib/stores/app.js';
</script>

<div id="toast" class={$toastMsg ? 'show' : ''}>{$toastMsg}</div>
