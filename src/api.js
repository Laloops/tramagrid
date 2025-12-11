// src/api.js
import { ref } from 'vue'

const API_BASE = '' 

// --- ESTADO GLOBAL ---
export const sessionId = ref('')
export const eventBus = new EventTarget()
export const activeColorIndex = ref(0) 

export const mergeState = ref({ sourceIndex: null })

// --- SESSÃO ---
export async function createSession() {
  const res = await fetch(`${API_BASE}/api/session`, { method: 'POST' })
  const data = await res.json()
  sessionId.value = data.session_id
}

export async function uploadImage(file) {
  const form = new FormData()
  form.append('file', file)
  await fetch(`${API_BASE}/api/upload/${sessionId.value}`, { method: 'POST', body: form })
}

export async function generateGrid() {
  await fetch(`${API_BASE}/api/generate/${sessionId.value}`, { method: 'POST' })
  eventBus.dispatchEvent(new Event('refresh'))
}

// --- FERRAMENTAS ---
export async function paintCell(x, y) {
  await fetch(`${API_BASE}/api/paint/${sessionId.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ x: x, y: y, color_index: activeColorIndex.value })
  })
}

export async function getPixelIndex(x, y) {
  const res = await fetch(`${API_BASE}/api/query-pixel/${sessionId.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ x, y })
  })
  const data = await res.json()
  return data.index
}

export async function undoLastAction() {
  await fetch(`${API_BASE}/api/undo/${sessionId.value}`, { method: 'POST' })
  eventBus.dispatchEvent(new Event('refresh'))
}

export async function mergeColors(fromIndex, toIndex) {
  await fetch(`${API_BASE}/api/merge/${sessionId.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ from_index: fromIndex, to_index: toIndex })
  })
  eventBus.dispatchEvent(new Event('refresh'))
}

// NOVO: Buscar sugestões de agrupamento
export async function getColorClusters() {
  if (!sessionId.value) return []
  const res = await fetch(`${API_BASE}/api/clusters/${sessionId.value}`)
  const data = await res.json()
  return data.clusters || []
}

// --- VISUALIZAÇÃO ---
export async function getPalette() {
  if (!sessionId.value) return []
  const res = await fetch(`${API_BASE}/api/palette/${sessionId.value}`)
  return await res.json()
}

export async function getGridImage() {
  if (!sessionId.value) return ""
  const res = await fetch(`${API_BASE}/api/grid/${sessionId.value}`)
  const data = await res.json()
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

export async function getParams() {
  if (!sessionId.value) return {}
  const res = await fetch(`${API_BASE}/api/params/${sessionId.value}`)
  return await res.json()
}

export async function replaceColorInRegion(x, y, w, h, fromIndex, toIndex) {
  if (!sessionId.value) return
  await fetch(`${API_BASE}/api/region/replace/${sessionId.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
        x: x, y: y, w: w, h: h, 
        from_index: fromIndex, 
        to_index: toIndex 
    })
  })
  eventBus.dispatchEvent(new Event('refresh'))
}