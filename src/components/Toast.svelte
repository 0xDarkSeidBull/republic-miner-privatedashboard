<script>
  import { toastMsg } from '../stores/app.js';
</script>

<div id="toast" class={$toastMsg ? 'show' : ''}>{$toastMsg}</div>
