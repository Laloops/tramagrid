<script setup>
  import { useToast } from '../toast.js'
  
  const { toasts, removeToast } = useToast()
  
  const icons = {
    success: '✅',
    error: '❌',
    info: 'ℹ️',
    warning: '⚠️',
    confirm: '🤔' // Ícone de dúvida
  }
  </script>
  
  <template>
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div 
          v-for="toast in toasts" 
          :key="toast.id" 
          class="toast-card" 
          :class="toast.type"
        >
          <div class="toast-content">
            <span class="icon">{{ icons[toast.type] || '🔔' }}</span>
            <span class="message">{{ toast.message }}</span>
          </div>
  
          <div v-if="toast.type === 'confirm'" class="toast-actions">
            <button @click="toast.onCancel" class="btn-cancel">Cancelar</button>
            <button @click="toast.onConfirm" class="btn-confirm">Confirmar</button>
          </div>
          
          <button v-else class="close-x" @click="removeToast(toast.id)">×</button>
        </div>
      </TransitionGroup>
    </div>
  </template>
  
  <style scoped>
  .toast-container {
    position: fixed; top: 80px; right: 20px; z-index: 9999;
    display: flex; flex-direction: column; gap: 10px; pointer-events: none;
  }
  
  .toast-card {
    pointer-events: auto; min-width: 300px; max-width: 400px;
    background: rgba(30, 30, 30, 0.95); backdrop-filter: blur(10px);
    color: white; padding: 15px 20px; border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    border-left: 4px solid #555;
    display: flex; flex-direction: column; gap: 10px; /* Layout vertical para caber botões */
    transition: all 0.3s;
  }
  
  .toast-content { display: flex; align-items: center; gap: 12px; }
  
  /* Tipos */
  .toast-card.success { border-left-color: #27ae60; }
  .toast-card.error { border-left-color: #e74c3c; }
  .toast-card.info { border-left-color: #3498db; }
  .toast-card.warning { border-left-color: #f1c40f; }
  .toast-card.confirm { border-left-color: #9b59b6; background: rgba(40, 40, 40, 0.98); }
  
  .icon { font-size: 1.2rem; }
  .message { font-size: 0.95rem; font-weight: 500; line-height: 1.4; }
  
  /* Botões do Confirm */
  .toast-actions {
    display: flex; gap: 10px; justify-content: flex-end; margin-top: 5px;
  }
  .btn-confirm, .btn-cancel {
    border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 0.85rem;
  }
  .btn-confirm { background: #27ae60; color: white; }
  .btn-confirm:hover { background: #2ecc71; }
  .btn-cancel { background: transparent; border: 1px solid #555; color: #ccc; }
  .btn-cancel:hover { border-color: #888; color: white; }
  
  .close-x {
    position: absolute; top: 5px; right: 5px; background: transparent;
    border: none; color: #666; font-size: 1.2rem; cursor: pointer;
  }
  .close-x:hover { color: white; }
  
  /* Animações */
  .toast-enter-from { opacity: 0; transform: translateX(50px); }
  .toast-enter-active, .toast-leave-active { transition: all 0.4s ease; }
  .toast-leave-to { opacity: 0; transform: translateX(50px); }
  </style>