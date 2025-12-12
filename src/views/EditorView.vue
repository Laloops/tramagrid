<script setup>
  import { onMounted, ref } from 'vue'
  import { useRouter } from 'vue-router'
  import ProjectControls from '../components/ProjectControls.vue' 
  import ColorPalette from '../components/ColorPalette.vue'
  import GridCanvas from '../components/GridCanvas.vue'
  import { sessionId, getParams } from '../api.js' 
  import { supabase } from '../supabase'
  import { showToast, showConfirm } from '../toast.js' // <--- Importando Toast
  
  const router = useRouter()
  const isSidebarOpen = ref(true) 
  const isSaving = ref(false)
  
  onMounted(() => {
    if (!sessionId.value) router.push('/')
  })

  function base64ToBlob(base64, mimeType = 'image/png') {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  }

  async function handleFinishProject() {
    console.log("💾 Iniciando Salvamento (Grade Editada)...")
    
    // 1. Auth
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) {
        // SUBSTITUÍDO: Confirm nativo por showConfirm
        const irLogin = await showConfirm("Você precisa estar logado para salvar.\nIr para login?")
        if(irLogin) router.push('/login')
        return
    }

    const { data: profile } = await supabase.from('profiles').select('*').eq('id', user.id).single()
    if (!profile) {
        showToast("Erro: Perfil de usuário não encontrado.", "error")
        return
    }

    // Nota: O prompt continua nativo pois nosso Toast não tem input de texto ainda
    const nomeProjeto = prompt("Nome do projeto:", "Meu TramaGrid")
    if (!nomeProjeto) return

    isSaving.value = true
    try {
        console.log(`📡 Buscando GRADE EDITADA para sessão: ${sessionId.value}`);
        
        // A. Pega a GRADE EDITADA (Visual Final)
        const imgRes = await fetch(`/api/grid/${sessionId.value}`)
        
        if (!imgRes.ok) {
            const txt = await imgRes.text()
            throw new Error(`Erro ${imgRes.status} do backend: ${txt}`)
        }
        
        const imgData = await imgRes.json()
        if (!imgData.image_base64) throw new Error("Imagem vazia.")
        
        // B. Upload
        const imageBlob = base64ToBlob(imgData.image_base64)
        const fileName = `${user.id}/${Date.now()}_grid.png` 
        
        const { error: uploadError } = await supabase.storage
            .from('images')
            .upload(fileName, imageBlob, { contentType: 'image/png', upsert: true })

        if (uploadError) throw uploadError

        const { data: { publicUrl } } = supabase.storage.from('images').getPublicUrl(fileName)

        // C. Salva no Banco com Configurações
        const currentParams = await getParams()
        
        const { error: projectError } = await supabase
            .from('projects')
            .insert({
                user_id: user.id,
                name: nomeProjeto,
                image_url: publicUrl, 
                settings: currentParams 
            })

        if (projectError) throw projectError

        showToast("Projeto salvo na galeria com sucesso!", "success") // <--- Toast Sucesso
        router.push('/dashboard') 

    } catch (err) {
        console.error("❌ ERRO AO SALVAR:", err)
        showToast("Erro ao salvar: " + err.message, "error") // <--- Toast Erro
    } finally {
        isSaving.value = false
    }
  }
</script>
  
<template>
  <div class="editor-layout">
      <button v-if="!isSidebarOpen" class="toggle-sidebar-floating" @click="isSidebarOpen = true">☰</button>
      <button class="fab-finish" @click="handleFinishProject" :disabled="isSaving" title="Salvar Projeto">
        <span v-if="isSaving" class="spinner-small"></span>
        <span v-else class="plus-icon">💾</span>
      </button>
      <aside class="sidebar" :class="{ closed: !isSidebarOpen }">
        <div class="sidebar-header">
            <h2 class="sidebar-title">Ferramentas</h2>
            <button @click="isSidebarOpen = false" class="close-btn">✕</button>
        </div>
        <div class="sidebar-content custom-scroll">
            <ProjectControls />
            <ColorPalette />
        </div>
      </aside>
      <main class="canvas-area">
        <GridCanvas />
      </main>
  </div>
</template>
  
<style scoped>
/* (Mantendo o estilo inalterado) */
.editor-layout { flex: 1; display: flex; overflow: hidden; position: relative; height: calc(100vh - 60px); }
.fab-finish { position: absolute; bottom: 40px; right: 40px; width: 64px; height: 64px; border-radius: 50%; background: #27ae60; color: white; border: none; cursor: pointer; box-shadow: 0 6px 20px rgba(0,0,0,0.4); z-index: 100; display: flex; align-items: center; justify-content: center; transition: all 0.3s; }
.fab-finish:hover:not(:disabled) { transform: scale(1.1); background: #2ecc71; }
.fab-finish:disabled { opacity: 0.7; cursor: wait; }
.plus-icon { font-size: 2rem; margin-top: -2px; }
.spinner-small { width: 24px; height: 24px; border: 3px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 1s infinite linear; }
@keyframes spin { to { transform: rotate(360deg); } }
.sidebar { width: 340px; background: #252526; border-right: 1px solid #333; transition: width 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); display: flex; flex-direction: column; overflow: hidden; }
.sidebar.closed { width: 0; border: none; }
.sidebar-header { flex-shrink: 0; height: 55px; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; border-bottom: 1px solid #333; background-color: #252526; }
.sidebar-title { margin: 0; font-size: 0.95rem; color: #ddd; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
.close-btn { background: transparent; border: none; color: #aaa; cursor: pointer; font-size: 1.1rem; width: 32px; height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: center; }
.close-btn:hover { background: rgba(255,255,255,0.1); color: white; }
.sidebar-content { flex: 1; overflow-y: auto; padding: 20px; padding-bottom: 40px; }
.toggle-sidebar-floating { position: absolute; left: 20px; top: 20px; z-index: 50; background: #252526; color: #fff; border: 1px solid #444; width: 44px; height: 44px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(0,0,0,0.4); }
.toggle-sidebar-floating:hover { background: #333; transform: translateY(-2px); border-color: #e67e22; color: #e67e22; }
.canvas-area { flex: 1; background: #0f0f0f; overflow: hidden; position: relative; }
.custom-scroll::-webkit-scrollbar { width: 6px; }
.custom-scroll::-webkit-scrollbar-track { background: transparent; }
.custom-scroll::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }
</style>