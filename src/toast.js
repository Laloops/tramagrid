import { ref } from 'vue'

const toasts = ref([])

// Toast normal (some sozinho)
export function showToast(message, type = 'success') {
  const id = Date.now()
  toasts.value.push({ id, message, type })
  
  // Auto-remove se não for de confirmação
  if (type !== 'confirm') {
    setTimeout(() => removeToast(id), 4000)
  }
}

// Toast de Confirmação (Espera clique)
export function showConfirm(message) {
  return new Promise((resolve) => {
    const id = Date.now()
    
    toasts.value.push({
      id,
      message,
      type: 'confirm', // Tipo especial
      // Funções que o botão vai chamar
      onConfirm: () => { removeToast(id); resolve(true) },
      onCancel: () => { removeToast(id); resolve(false) }
    })
  })
}

export function removeToast(id) {
  toasts.value = toasts.value.filter(t => t.id !== id)
}

export function useToast() {
  return { toasts, removeToast }
}