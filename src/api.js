// src/api.js
const API_BASE = 'http://localhost:8000'   // ← ESSA É A ÚNICA COISA QUE MUDOU

let sessionId = ''

export async function createSession() {
  const res = await fetch(`${API_BASE}/api/session`, { method: 'POST' })
  const data = await res.json()
  sessionId = data.session_id
}

export async function uploadImage(file) {
  const form = new FormData()
  form.append('file', file)
  await fetch(`${API_BASE}/api/upload/${sessionId}`, { method: 'POST', body: form })
}

export async function generateGrid() {
  await fetch(`${API_BASE}/api/generate/${sessionId}`, { method: 'POST' })
}

export async function getPalette() {
  const res = await fetch(`${API_BASE}/api/palette/${sessionId}`)
  return await res.json()
}

export async function getGridImage() {
  const res = await fetch(`${API_BASE}/api/grid/${sessionId}`)
  const data = await res.json()
  return `data:image/png;base64,${data.image_base64}`
}

export async function updateParams(params) {
  await fetch(`${API_BASE}/api/params/${sessionId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  })
}

export async function replaceColor(index, new_hex) {
  await fetch(`${API_BASE}/api/color/replace/${sessionId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ index, new_hex })
  })
}

export async function deleteColor(index) {
  await fetch(`${API_BASE}/api/color/delete/${sessionId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ index })
  })
}

export async function simplifyPalette(intensity) {
  await fetch(`${API_BASE}/api/simplify/${sessionId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ intensity })
  })
}

export async function simplifyBW() {
  await fetch(`${API_BASE}/api/simplify-bw/${sessionId}`, { method: 'POST' })
}