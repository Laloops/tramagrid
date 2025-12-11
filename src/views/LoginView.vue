<script setup>
    import { ref } from 'vue'
    import { supabase } from '../supabase'
    import { useRouter } from 'vue-router'
    
    const email = ref('')
    const loading = ref(false)
    const message = ref('')
    const router = useRouter()
    
    async function handleLogin() {
      loading.value = true
      message.value = ''
      const { error } = await supabase.auth.signInWithOtp({
        email: email.value,
        options: { emailRedirectTo: window.location.origin + '/editor' }
      })
      if (error) message.value = 'Erro: ' + error.message
      else message.value = '✨ Link enviado para seu e-mail!'
      loading.value = false
    }
    
    // NOVA FUNÇÃO: Login Social
    async function handleSocialLogin(provider) {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: provider,
        options: { redirectTo: window.location.origin + '/editor' }
      })
      if (error) alert("Erro no login social: " + error.message)
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
            <input v-model="email" type="email" placeholder="seu@email.com" @keyup.enter="handleLogin" />
            <button @click="handleLogin" :disabled="loading || !email" class="btn-email">
              {{ loading ? 'Enviando...' : 'Enviar Link Mágico' }}
            </button>
          </div>
    
          <p v-if="message" class="status-msg">{{ message }}</p>
          <button @click="router.push('/')" class="btn-back">Voltar</button>
        </div>
      </div>
    </template>
    
    <style scoped>
    /* (Mantenha o CSS anterior e adicione estes novos) */
    .login-container { height: 100vh; display: flex; align-items: center; justify-content: center; background: #121212; background-image: radial-gradient(circle at top, #1e1e1e 0%, #121212 70%); }
    .login-box { background: #252526; padding: 40px; border-radius: 16px; border: 1px solid #333; width: 100%; max-width: 400px; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
    .logo { margin: 0 0 10px 0; color: white; font-size: 2rem; }
    .highlight { color: #e67e22; }
    .subtitle { color: #aaa; margin-bottom: 20px; font-size: 0.9rem; }
    
    /* Botões Sociais */
    .social-buttons { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
    .btn-social { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 12px; border-radius: 8px; border: 1px solid #444; background: white; color: #333; font-weight: bold; cursor: pointer; transition: 0.2s; }
    .btn-social:hover { background: #f1f1f1; transform: translateY(-2px); }
    .btn-social.google { color: #444; }
    
    .divider { font-size: 0.8rem; color: #666; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; }
    
    .form-group { display: flex; flex-direction: column; gap: 10px; }
    input { padding: 12px; border-radius: 8px; border: 1px solid #444; background: #1a1a1a; color: white; font-size: 1rem; outline: none; }
    .btn-email { padding: 12px; border-radius: 8px; border: none; background: #e67e22; color: white; font-weight: bold; cursor: pointer; }
    .btn-email:hover { background: #d35400; }
    .status-msg { margin-top: 20px; color: #2ecc71; background: rgba(46, 204, 113, 0.1); padding: 10px; border-radius: 6px; }
    .btn-back { background: transparent; border: none; margin-top: 20px; color: #888; cursor: pointer; }
    </style>