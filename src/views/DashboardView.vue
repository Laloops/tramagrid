<script setup>
    import { ref, onMounted, computed } from 'vue'
    import { useRouter } from 'vue-router'
    import { supabase } from '../supabase'
    import { loadProjectFromSupabase } from '../api.js'
    import { showToast, showConfirm } from '../toast.js' // <--- Importando nosso Toast
    
    const router = useRouter()
    const projects = ref([])
    const loading = ref(true)
    const userProfile = ref(null)
    
    const firstName = computed(() => {
      const email = userProfile.value?.email || ''
      return email.split('@')[0] || 'Artista'
    })
    
    onMounted(async () => {
      await fetchUserData()
      await fetchProjects()
    })
    
    async function fetchUserData() {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        router.push('/login')
        return
      }
      userProfile.value = user
    }
    
    async function fetchProjects() {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return
    
      const { data, error } = await supabase
        .from('projects')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })
    
      if (error) console.error("Erro:", error)
      else projects.value = data
      loading.value = false
    }
    
    async function openProject(project) {
      // SUBSTITUÍDO: confirm() por showConfirm()
      const confirmed = await showConfirm(`Abrir "${project.name}"?\nIsso vai substituir o trabalho atual.`)
      if (!confirmed) return
    
      loading.value = true
      try {
        const projectAdapter = {
            ...project,
            image_path: project.image_url || project.image_path 
        }
        await loadProjectFromSupabase(projectAdapter)
        router.push('/editor')
      } catch (e) {
        showToast("Erro ao abrir projeto: " + e.message, "error") // <--- Toast Erro
        loading.value = false
      }
    }
    
    async function deleteProject(id) {
      // SUBSTITUÍDO: confirm() por showConfirm()
      const confirmed = await showConfirm("Tem certeza que quer apagar este projeto?")
      if(!confirmed) return
      
      const previousList = [...projects.value]
      projects.value = projects.value.filter(p => p.id !== id)
      
      const { error } = await supabase.from('projects').delete().eq('id', id)
      
      if (error) {
        showToast("Erro ao apagar projeto.", "error") // <--- Toast Erro
        projects.value = previousList
      } else {
        showToast("Projeto apagado com sucesso.", "success") // <--- Toast Sucesso
      }
    }
    </script>
    
    <template>
      <div class="dashboard-page">
        <header class="dash-header">
          <div class="header-inner">
            <h1>Olá, <span class="gradient-text">{{ firstName }}</span></h1>
            <p class="subtitle">Sua coleção ({{ projects.length }})</p>
          </div>
        </header>
    
        <main class="content-scroll-area">
          <div class="content-inner">
            
            <div v-if="loading" class="loading-state">
              <div class="spinner"></div>
            </div>
    
            <div v-else class="projects-grid">
              <div class="card create-card" @click="router.push('/')">
                <div class="icon-circle"><span class="plus">+</span></div>
                <span class="create-label">Novo</span>
              </div>
    
              <div v-for="p in projects" :key="p.id" class="card project-card" @click="openProject(p)">
                <div class="card-thumb" :style="{ backgroundImage: `url(${p.image_url})` }">
                  <div class="overlay"><span>✏️</span></div>
                </div>
                <div class="card-info">
                  <h3>{{ p.name }}</h3>
                  <button @click.stop="deleteProject(p.id)" class="btn-icon">🗑️</button>
                </div>
              </div>
            </div>
    
          </div>
        </main>
      </div>
    </template>
    
    <style scoped>
    /* Layout Principal - Ocupa exatamente o espaço que sobra */
    .dashboard-page {
      flex: 1; /* Ocupa o restante do App (que tem 100vh) */
      display: flex;
      flex-direction: column;
      background-color: #121212;
      color: #ecf0f1;
      overflow: hidden; /* Evita scroll na página inteira */
    }
    
    /* Header Compacto */
    .dash-header { 
      background: #181818; 
      border-bottom: 1px solid #333; 
      padding: 15px 30px;
      flex-shrink: 0;
    }
    .header-inner { max-width: 1400px; margin: 0 auto; display: flex; align-items: baseline; gap: 15px; }
    .dash-header h1 { font-size: 1.5rem; margin: 0; font-weight: 700; }
    .subtitle { color: #666; font-size: 0.9rem; margin: 0; }
    .gradient-text { background: linear-gradient(to right, #e67e22, #f1c40f); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    
    /* Área de Conteúdo */
    .content-scroll-area {
      flex: 1; 
      overflow-y: auto; /* Scroll apenas aqui se necessário */
      padding: 20px 30px;
    }
    
    .content-inner { max-width: 1400px; margin: 0 auto; }
    
    /* Grid Responsivo e Compacto */
    .projects-grid { 
      display: grid; 
      /* Cards menores para caberem mais na tela */
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); 
      gap: 15px; 
    }
    
    /* Estilo dos Cards */
    .card { 
      background: #1e1e1e; 
      border-radius: 12px; 
      overflow: hidden; 
      cursor: pointer; 
      transition: all 0.2s; 
      border: 1px solid #333; 
      position: relative;
      display: flex;
      flex-direction: column;
    }
    .card:hover { transform: translateY(-3px); border-color: #555; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
    
    /* Card Novo */
    .create-card { 
      background: rgba(255,255,255,0.03); border: 2px dashed #444; 
      align-items: center; justify-content: center; 
      min-height: 180px; /* Altura fixa para alinhar */
    }
    .create-card:hover { border-color: #e67e22; background: rgba(230, 126, 34, 0.05); }
    .icon-circle { width: 40px; height: 40px; border-radius: 50%; background: #252526; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; border: 1px solid #444; }
    .plus { font-size: 1.5rem; color: #aaa; margin-top: -3px; }
    .create-label { font-weight: bold; color: #888; font-size: 0.85rem; }
    
    /* Card Projeto */
    .project-card { min-height: 180px; }
    .card-thumb { 
      flex: 1; /* Ocupa todo o espaço disponível menos o rodapé */
      background-size: cover; background-position: center; background-color: #000; 
      position: relative;
    }
    .overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; opacity: 0; transition: 0.2s; }
    .card:hover .overlay { opacity: 1; }
    
    .card-info { 
      padding: 10px; background: #252526; border-top: 1px solid #333; 
      display: flex; justify-content: space-between; align-items: center; 
      height: 40px; box-sizing: border-box;
    }
    .card-info h3 { margin: 0; font-size: 0.85rem; color: #ddd; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100px; }
    .btn-icon { background: transparent; border: none; color: #666; cursor: pointer; font-size: 1.1rem; padding: 0 5px; }
    .btn-icon:hover { color: #e74c3c; }
    
    /* Loading */
    .loading-state { text-align: center; margin-top: 50px; }
    .spinner { width: 30px; height: 30px; border: 3px solid rgba(255,255,255,0.1); border-top-color: #e67e22; border-radius: 50%; animation: spin 1s infinite linear; margin: 0 auto; }
    @keyframes spin { to { transform: rotate(360deg); } }
    
    /* Scrollbar Discreta */
    .content-scroll-area::-webkit-scrollbar { width: 6px; }
    .content-scroll-area::-webkit-scrollbar-track { background: transparent; }
    .content-scroll-area::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
    .content-scroll-area::-webkit-scrollbar-thumb:hover { background: #444; }
    
    /* Ajuste Mobile */
    @media (max-width: 600px) {
      .projects-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }
      .content-scroll-area { padding: 15px; }
    }
    </style>