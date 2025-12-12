<script setup>
  import { ref, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  import { supabase } from '../supabase' 
  import { createSession, uploadImage, eventBus } from '../api.js'
  
  const router = useRouter()
  const fileInput = ref(null)
  const isLoading = ref(false)
  const showFreeBadge = ref(false) 
  
  const LOCAL_STORAGE_KEY = 'tramagrid_anon_used'

  // --- Função auxiliar ---
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

  // --- 1. VERIFICAÇÃO VISUAL ---
  onMounted(async () => {
    const { data: { user } } = await supabase.auth.getUser()
    if (user) {
        const profile = await getOrCreateProfile(user)
        if (profile && !profile.free_generation_used) {
            showFreeBadge.value = true
        }
    } else {
        const jaUsouAnonimo = localStorage.getItem(LOCAL_STORAGE_KEY)
        if (!jaUsouAnonimo) showFreeBadge.value = true
    }
  })
  
  // --- 2. UPLOAD COM COBRANÇA IMEDIATA ---
  async function handleStartUpload(e) {
    const file = e.target.files[0]
    if (!file) return
  
    isLoading.value = true
    
    try {
      const { data: { user } } = await supabase.auth.getUser()
      let profile = null

      // A. VERIFICAÇÃO DE SALDO (Antes de gastar processamento)
      if (user) {
          profile = await getOrCreateProfile(user)
          
          if (!profile) throw new Error("Erro ao carregar perfil.")

          const temCredito = profile.credits > 0
          const temGratis = !profile.free_generation_used

          if (!temCredito && !temGratis) {
              alert("Seus créditos acabaram! 😢\nAdquira um pacote para gerar novos gráficos.")
              router.push('/buy-credits')
              if (fileInput.value) fileInput.value.value = ''
              return 
          }
      } else {
          // Anônimo
          const jaUsou = localStorage.getItem(LOCAL_STORAGE_KEY)
          if (jaUsou) {
              if (confirm("Cota de visitante esgotada.\nEntre na sua conta para continuar!")) {
                  router.push('/login')
              }
              if (fileInput.value) fileInput.value.value = ''
              return
          }
      }

      // B. GERAÇÃO (O trabalho pesado)
      await createSession()
      await uploadImage(file)
      
      // C. COBRANÇA (Se chegou aqui, o gráfico foi gerado com sucesso)
      if (user) {
          console.log("💰 Cobrando o usuário agora...")
          let updateData = {}
          
          // Prioridade: Gasta o grátis primeiro, depois os créditos
          if (!profile.free_generation_used) {
              updateData = { free_generation_used: true }
          } else {
              updateData = { credits: Math.max(0, profile.credits - 1) }
          }

          const { error: chargeError } = await supabase
              .from('profiles')
              .update(updateData)
              .eq('id', user.id)
          
          if (chargeError) console.error("Erro ao cobrar:", chargeError)
          
          // Atualiza a UI do TopToolbar imediatamente
          eventBus.dispatchEvent(new Event('credits-updated'))
      
      } else {
          // Cobra o anônimo
          localStorage.setItem(LOCAL_STORAGE_KEY, 'true')
      }

      router.push('/editor')

    } catch (err) {
      console.error(err)
      alert("Erro: " + err.message)
    } finally {
      isLoading.value = false
    }
  }
</script>

<template>
  <div class="home-container">
    <div class="hero-box">
      <h1 class="title">Trama<span class="highlight">Grid</span></h1>
      <p class="subtitle">Faça upload e veja seu gráfico pronto em segundos.</p>
      
      <div class="upload-area">
        <div v-if="showFreeBadge" class="free-badge">🎁 1 Grátis Disponível</div>

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
          <span v-else>✨ Criar Grade Agora</span>
        </button>
        
        <p class="hint">Custará 1 crédito ou seu uso grátis.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-container { height: calc(100vh - 60px); display: flex; align-items: center; justify-content: center; background: #121212; background-image: radial-gradient(circle at center, #1e1e1e 0%, #121212 70%); }
.hero-box { text-align: center; max-width: 600px; padding: 40px; background: rgba(30,30,30,0.5); border-radius: 20px; border: 1px solid #333; backdrop-filter: blur(10px); box-shadow: 0 20px 50px rgba(0,0,0,0.5); position: relative; }
.title { font-size: 3.5rem; margin-bottom: 10px; color: white; letter-spacing: -2px; }
.highlight { color: #e67e22; }
.subtitle { color: #aaa; font-size: 1.1rem; margin-bottom: 40px; line-height: 1.5; }
.free-badge { background: #27ae60; color: white; font-weight: bold; padding: 5px 15px; border-radius: 20px; display: inline-block; margin-bottom: 15px; font-size: 0.9rem; box-shadow: 0 0 10px rgba(39, 174, 96, 0.4); animation: bounce 2s infinite; }
.btn-big-upload { background: #e67e22; color: white; border: none; padding: 15px 40px; font-size: 1.2rem; font-weight: bold; border-radius: 50px; cursor: pointer; transition: all 0.3s; box-shadow: 0 10px 20px rgba(230, 126, 34, 0.3); display: flex; align-items: center; gap: 10px; margin: 0 auto; }
.btn-big-upload:hover:not(:disabled) { transform: translateY(-3px); box-shadow: 0 15px 30px rgba(230, 126, 34, 0.4); background: #d35400; }
.btn-big-upload:disabled { opacity: 0.7; cursor: wait; }
.hint { margin-top: 15px; font-size: 0.85rem; color: #666; }
.spinner-small { width: 20px; height: 20px; border: 3px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 1s infinite linear; }
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
</style>