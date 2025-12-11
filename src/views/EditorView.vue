<script setup>
  import { onMounted, ref } from 'vue'
  import { useRouter } from 'vue-router'
  import ProjectControls from '../components/ProjectControls.vue' 
  import ColorPalette from '../components/ColorPalette.vue'
  import GridCanvas from '../components/GridCanvas.vue'
  import { sessionId } from '../api.js'
  import { supabase } from '../supabase'
  
  const router = useRouter()
  const isSidebarOpen = ref(true) 
  
  onMounted(() => {
    // Se tentar acessar o editor sem ter feito upload na home, manda voltar
    if (!sessionId.value) {
      router.push('/')
    }
  })

  // AÇÃO DO BOTÃO "NOVO PROJETO / SALVAR"
  async function handleFinishProject() {
    // 1. Verifica autenticação
    const { data: { user } } = await supabase.auth.getUser()

    if (!user) {
        if(confirm("Você precisa entrar para salvar seu projeto grátis.\n\nIr para login?")) {
            router.push('/login')
        }
        return
    }

    // 2. Busca saldo do usuário
    const { data: profile } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', user.id)
      .single()

    if (!profile) return alert("Erro ao carregar perfil.")

    // 3. Determina se pode salvar
    let canSave = false
    let message = ""

    if (!profile.free_generation_used) {
        message = "Usar sua Geração Gratuita de Boas-vindas?"
        canSave = true
    } else if (profile.credits > 0) {
        message = `Salvar projeto? Custo: 1 Crédito.\n(Saldo atual: ${profile.credits})`
        canSave = true
    } else {
        // SEM SALDO!
        if (confirm("Você não tem créditos suficientes.\n\nDeseja adquirir um pacote?")) {
            router.push('/buy-credits') // Vamos criar essa rota já já
        }
        return
    }

    // 4. Executa a transação
    if (canSave && confirm(message)) {
        try {
            // A. Atualiza o saldo no banco
            let updateData = {}
            if (!profile.free_generation_used) {
                updateData = { free_generation_used: true } // Queima o grátis
            } else {
                updateData = { credits: profile.credits - 1 } // Queima o crédito
            }

            const { error } = await supabase
                .from('profiles')
                .update(updateData)
                .eq('id', user.id)

            if (error) throw error

            // B. (Futuro) Aqui salvaríamos o projeto na tabela 'projects'
            
            alert("Projeto salvo com sucesso! Novo saldo atualizado.")
            router.push('/') // Volta pra home

        } catch (err) {
            alert("Erro ao processar: " + err.message)
        }
    }
}
</script>
  
<template>
  <div class="editor-layout">
      <button v-if="!isSidebarOpen" class="toggle-sidebar-floating" @click="isSidebarOpen = true">☰</button>

      <button class="fab-finish" @click="handleFinishProject" title="Salvar e Novo Projeto">
        <span class="plus-icon">+</span>
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
.editor-layout { flex: 1; display: flex; overflow: hidden; position: relative; height: calc(100vh - 60px); }

/* --- FAB (Botão Flutuante de Ação Principal) --- */
.fab-finish {
    position: absolute;
    bottom: 40px;
    right: 40px;
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: #e67e22;
    color: white;
    border: none;
    cursor: pointer;
    box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    z-index: 100;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.fab-finish:hover {
    transform: scale(1.1) rotate(90deg);
    background: #d35400;
    box-shadow: 0 10px 25px rgba(230, 126, 34, 0.5);
}
.plus-icon { font-size: 2.5rem; font-weight: 300; line-height: 1; margin-top: -4px; }

/* (CSS da Sidebar e Layout mantidos) */
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