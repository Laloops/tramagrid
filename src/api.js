// src/api.js
import { ref } from 'vue'

const API_BASE = '' // O proxy do Vite trata do redirecionamento

// 1. Estado Partilhado: O ID da sessão é agora reativo
export const sessionId = ref('')

// 2. Bus de Eventos: Para avisar os componentes (ex: atualizar a paleta após gerar a grade)
export const eventBus = new EventTarget()

export async function createSession() {
  const res = await fetch(`${API_BASE}/api/session`, { method: 'POST' })
  const data = await res.json()
  sessionId.value = data.session_id // Atualiza o valor reativo
}

export async function uploadImage(file) {
  const form = new FormData()
  form.append('file', file)
  await fetch(`${API_BASE}/api/upload/${sessionId.value}`, { method: 'POST', body: form })
}

export async function generateGrid() {
  await fetch(`${API_BASE}/api/generate/${sessionId.value}`, { method: 'POST' })
  // Avisa a aplicação que a grade mudou (para atualizar a paleta, etc.)
  eventBus.dispatchEvent(new Event('refresh'))
}

export async function getPalette() {
  if (!sessionId.value) return []
  const res = await fetch(`${API_BASE}/api/palette/${sessionId.value}`)
  return await res.json()
}

export async function getGridImage() {
  if (!sessionId.value) return ""
  const res = await fetch(`${API_BASE}/api/grid/${sessionId.value}`)
  const data = await res.json()
  // Lógica para tratar os diferentes formatos de retorno do backend
  if (!data) return ""
  if (typeof data === "string") return data
  if (data.image_base64) {
      return data.image_base64.startsWith("data:") 
        ? data.image_base64 
        : `data:image/png;base64,${data.image_base64}`
  }
  return ""
}

export async function updateParams(params) {
  await fetch(`${API_BASE}/api/params/${sessionId.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  })
}

export async function replaceColor(index, new_hex) {
  await fetch(`${API_BASE}/api/color/replace/${sessionId.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ index, new_hex })
  })
  eventBus.dispatchEvent(new Event('refresh'))
}

export async function deleteColor(index) {
  await fetch(`${API_BASE}/api/color/delete/${sessionId.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ index })
  })
  eventBus.dispatchEvent(new Event('refresh'))
}

export async function simplifyPalette(intensity) {
  await fetch(`${API_BASE}/api/simplify/${sessionId.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ intensity })
  })
  eventBus.dispatchEvent(new Event('refresh'))
}

export async function simplifyBW() {
  await fetch(`${API_BASE}/api/simplify-bw/${sessionId.value}`, { method: 'POST' })
  eventBus.dispatchEvent(new Event('refresh'))
}