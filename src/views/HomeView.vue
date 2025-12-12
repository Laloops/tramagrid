<script setup>
  import { ref, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  import { supabase } from '../supabase' 
  import { createSession, uploadImage, eventBus } from '../api.js'
  import { showToast } from '../toast.js' 
  
  const router = useRouter()
  const fileInput = ref(null)
  const isLoading = ref(false)
  const showFreeBadge = ref(false) 
  
  const LOCAL_STORAGE_KEY = 'tramagrid_anon_used'

  // --- Função auxiliar para garantir que o perfil existe ---
  async function getOrCreateProfile(user) {
      let { data: profile } = await supabase
          .from('profiles')
          .select('credits, free_generation_used')
          .eq('id', user.id)
          .maybeSingle()
      
      if (!profile) {
          const { data: newProfile } = await supabase
              .from('profiles')
              .insert([{ id: user.id, email: user.email, credits: 0, free_generation_used: false }])
              .select()
              .single()
          return newProfile
      }
      return profile
  }

  // --- 1. VERIFICAÇÃO VISUAL AO CARREGAR ---
  onMounted(async () => {
    const { data: { user } } = await supabase.auth.getUser()
    if (user) {
        const profile = await getOrCreateProfile(user)
        if (profile && !profile.free_generation_used) showFreeBadge.value = true
    } else {
        const jaUsouAnonimo = localStorage.getItem(LOCAL_STORAGE_KEY)
        if (!jaUsouAnonimo) showFreeBadge.value = true
    }
  })
  
  // --- 2. UPLOAD COM VALIDAÇÃO ROBUSTA ---
  async function handleStartUpload(e) {
    const file = e.target.files[0]
    if (!file) return
  
    isLoading.value = true
    
    try {
      const { data: { user } } = await supabase.auth.getUser()
      
      // A. USUÁRIO LOGADO: Pede ao backend para cobrar
      if (user) {
          const apiBase = import.meta.env.VITE_API_URL || ''
          
          // Chama a rota de consumo de crédito
          const res = await fetch(`${apiBase}/api/consume-credit`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ user_id: user.id })
          })

          if (!res.ok) {
              // Tenta ler o erro específico (ex: "Saldo insuficiente")
              const errorData = await res.json().catch(() => ({}))
              const errorMessage = errorData.detail || "Erro desconhecido"

              console.warn("⚠️ Resposta do Backend:", res.status, errorMessage)

              // TRATAMENTO DE ERROS ESPECÍFICOS
              if (res.status === 402) {
                  showToast("Seus créditos acabaram! Redirecionando...", "warning")
                  setTimeout(() => router.push('/buy-credits'), 1500)
              } else {
                  // Outros erros (500, etc)
                  showToast(`Erro: ${errorMessage}`, "error")
              }
              
              // Reseta o input para permitir tentar de novo depois
              if (fileInput.value) fileInput.value.value = ''
              return // Para a execução aqui se deu erro
          }
          
          // Se passou, atualiza a UI
          eventBus.dispatchEvent(new Event('credits-updated'))

      } else {
          // B. USUÁRIO ANÔNIMO: Verifica localmente
          const jaUsou = localStorage.getItem(LOCAL_STORAGE_KEY)
          if (jaUsou) {
              showToast("Cota de visitante esgotada. Entre para continuar!", "info")
              setTimeout(() => router.push('/login'), 1500)
              
              if (fileInput.value) fileInput.value.value = ''
              return
          }
          localStorage.setItem(LOCAL_STORAGE_KEY, 'true')
      }

      // C. GERAÇÃO (Só acontece se não caiu nos returns acima)
      await createSession()
      await uploadImage(file)
      
      showToast("Gráfico gerado com sucesso!", "success")
      router.push('/editor')

    } catch (err) {
      console.error(err)
      showToast("Erro de conexão ou processamento.", "error")
    } finally {
      isLoading.value = false
    }
  }
</script>

<template>
  <div class="home-container">
    
    <div class="bg-overlay"></div>

    <div class="content-wrapper">
      <div class="hero-box glass">
        <h1 class="title">Trama<span class="highlight">Grid</span></h1>
        <p class="subtitle">Faça upload e veja seu gráfico pronto em segundos.</p>
        
        <div class="upload-area">
          <div v-if="showFreeBadge" class="free-badge">🎁 1ª Geração Grátis</div>

          <input 
            type="file" 
            ref="fileInput" 
            @change="handleStartUpload" 
            hidden 
            accept="image/*" 
          />
          
          <button 
            @click="fileInput.click()" 
            class="btn-big-upload" 
            :disabled="isLoading"
          >
            <span v-if="isLoading" class="spinner-small"></span>
            <span v-else>📂 Carregar Imagem</span>
          </button>
          
          <p class="hint">Suporta JPG e PNG. Processamento inteligente.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-container {
  min-height: calc(100vh - 60px);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: radial-gradient(circle at center, #2c3e50 0%, #000000 100%);
}

.bg-video {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; z-index: 0;
}
.bg-overlay {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1;
}

.content-wrapper {
  position: relative; z-index: 2; width: 100%; max-width: 700px; padding: 20px; text-align: center;
}

/* Glassmorphism */
.hero-box.glass {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 50px 40px;
  box-shadow: 0 25px 50px rgba(0,0,0,0.5);
  transition: transform 0.3s;
}
.hero-box:hover { transform: translateY(-5px); border-color: rgba(255, 255, 255, 0.2); }

.title { font-size: 4rem; margin-bottom: 15px; color: white; font-weight: 800; letter-spacing: -2px; text-shadow: 0 4px 20px rgba(0,0,0,0.5); }
.highlight { color: #e67e22; }
.subtitle { color: #ddd; font-size: 1.2rem; margin-bottom: 40px; line-height: 1.6; font-weight: 300; }

.btn-big-upload {
  background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
  color: white; border: none; padding: 18px 50px; font-size: 1.3rem; font-weight: bold; border-radius: 50px; cursor: pointer; transition: all 0.3s; box-shadow: 0 10px 30px rgba(230, 126, 34, 0.4); display: inline-flex; align-items: center; gap: 12px; justify-content: center;
}
.btn-big-upload:hover:not(:disabled) { transform: scale(1.05); box-shadow: 0 15px 40px rgba(230, 126, 34, 0.6); filter: brightness(1.1); }
.btn-big-upload:disabled { opacity: 0.7; cursor: wait; filter: grayscale(0.5); }

.free-badge {
  background: #27ae60; color: white; font-weight: bold; padding: 6px 16px; border-radius: 20px; display: inline-block; margin-bottom: 20px; font-size: 0.9rem; box-shadow: 0 0 15px rgba(39, 174, 96, 0.6); animation: float 3s ease-in-out infinite;
}

.hint { margin-top: 20px; font-size: 0.9rem; color: #aaa; }
.spinner-small { width: 24px; height: 24px; border: 3px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 1s infinite linear; }

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }

@media (max-width: 600px) {
  .title { font-size: 3rem; }
  .hero-box.glass { padding: 30px 20px; }
  .btn-big-upload { width: 100%; }
}
</style>