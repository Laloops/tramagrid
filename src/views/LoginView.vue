<script setup>
  import { ref } from 'vue'
  import { supabase } from '../supabase'
  import { useRouter } from 'vue-router'
  import { showToast } from '../toast.js' // <--- Importando Toast
  
  const email = ref('')
  const loading = ref(false)
  const router = useRouter()
  
  async function handleLogin() {
    loading.value = true
    
    const { data, error } = await supabase.auth.signInWithOtp({
      email: email.value,
      options: { emailRedirectTo: window.location.origin }
    })
    
    if (error) {
        console.error("🔴 Erro Login:", error)
        showToast("Erro: " + error.message, "error") // <--- Toast Erro
    } else {
        console.log("🟢 Link enviado:", data)
        showToast("✨ Link enviado! Verifique seu e-mail.", "success") // <--- Toast Sucesso
        email.value = "" // Limpa o campo
    }
    loading.value = false
  }
  
  async function handleSocialLogin(provider) {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: provider,
      options: { emailRedirectTo: window.location.origin }
    })
    
    if (error) {
        console.error("🔴 Erro Social:", error)
        showToast("Erro no login social: " + error.message, "error") // <--- Toast Erro
    }
  }
</script>
  
<template>
<div class="login-container">
  <div class="login-box">
    <h1 class="logo">Trama<span class="highlight">Grid</span></h1>
    <p class="subtitle">Entre para salvar seus projetos.</p>

    <div class="social-buttons">
      <button class="btn-social google" @click="handleSocialLogin('google')">
        <span class="icon">G</span> Entrar com Google
      </button>
      </div>

    <div class="divider">ou use seu e-mail</div>

    <div class="form-group">
      <input 
        v-model="email" 
        type="email" 
        placeholder="seu@email.com" 
        @keyup.enter="handleLogin" 
      />
      <button 
        @click="handleLogin" 
        :disabled="loading || !email" 
        class="btn-email"
      >
        <span v-if="loading" class="spinner-small"></span>
        <span v-else>Enviar Link Mágico</span>
      </button>
    </div>

    <button @click="router.push('/')" class="btn-back">Voltar</button>
  </div>
</div>
</template>

<style scoped>
.login-container { height: 100vh; display: flex; align-items: center; justify-content: center; background: #121212; background-image: radial-gradient(circle at top, #1e1e1e 0%, #121212 70%); }
.login-box { background: #252526; padding: 40px; border-radius: 16px; border: 1px solid #333; width: 100%; max-width: 400px; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
.logo { margin: 0 0 10px 0; color: white; font-size: 2rem; }
.highlight { color: #e67e22; }
.subtitle { color: #aaa; margin-bottom: 20px; font-size: 0.9rem; }
.social-buttons { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.btn-social { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 12px; border-radius: 8px; border: 1px solid #444; background: white; color: #333; font-weight: bold; cursor: pointer; transition: 0.2s; }
.btn-social:hover { background: #f1f1f1; transform: translateY(-2px); }
.btn-social.google { color: #444; }
.divider { font-size: 0.8rem; color: #666; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; }
.form-group { display: flex; flex-direction: column; gap: 10px; }
input { padding: 12px; border-radius: 8px; border: 1px solid #444; background: #1a1a1a; color: white; font-size: 1rem; outline: none; transition: border-color 0.2s; }
input:focus { border-color: #e67e22; }
.btn-email { padding: 12px; border-radius: 8px; border: none; background: #e67e22; color: white; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s; }
.btn-email:hover:not(:disabled) { background: #d35400; transform: translateY(-1px); }
.btn-email:disabled { opacity: 0.7; cursor: wait; }
.btn-back { background: transparent; border: none; margin-top: 20px; color: #888; cursor: pointer; transition: color 0.2s; }
.btn-back:hover { color: white; text-decoration: underline; }

.spinner-small { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 1s infinite linear; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>