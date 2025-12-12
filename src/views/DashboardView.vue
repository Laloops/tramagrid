<script setup>
    import { ref, onMounted, computed } from 'vue'
    import { useRouter } from 'vue-router'
    import { supabase } from '../supabase'
    import { loadProjectFromSupabase } from '../api.js'
    
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
      const confirmOpen = confirm(`Abrir "${project.name}"?\n⚠️ Substitui o projeto atual.`)
      if (!confirmOpen) return
    
      loading.value = true
      try {
        const projectAdapter = {
            ...project,
            image_path: project.image_url || project.image_path 
        }
        await loadProjectFromSupabase(projectAdapter)
        router.push('/editor')
      } catch (e) {
        alert("Erro ao abrir: " + e.message)
        loading.value = false
      }
    }
    
    async function deleteProject(id) {
      if(!confirm("Tem certeza?")) return
      const previousList = [...projects.value]
      projects.value = projects.value.filter(p => p.id !== id)
      const { error } = await supabase.from('projects').delete().eq('id', id)
      if (error) {
        alert("Erro ao apagar.")
        projects.value = previousList
      }
    }
    </script>
    
    <template>
      <div class="dashboard-page">
        <header class="dash-header">
          <div class="header-inner">
            <div class="welcome-text">
              <h1>Olá, <span class="gradient-text">{{ firstName }}</span></h1>
              <p class="subtitle">Sua coleção de gráficos.</p>
            </div>
          </div>
        </header>
    
        <main class="content-area">
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            <p>Carregando...</p>
          </div>
    
          <div v-else class="projects-grid">
            <div class="card create-card" @click="router.push('/')">
              <div class="icon-circle"><span class="plus">+</span></div>
              <span class="create-label">Novo Gráfico</span>
            </div>
    
            <div v-for="p in projects" :key="p.id" class="card project-card" @click="openProject(p)">
              <div class="card-thumb" :style="{ backgroundImage: `url(${p.image_url})` }">
                <div class="overlay"><span class="open-btn">Abrir</span></div>
              </div>
              <div class="card-info">
                <div class="info-left">
                  <h3>{{ p.name }}</h3>
                  <span class="date">{{ new Date(p.created_at).toLocaleDateString('pt-BR') }}</span>
                </div>
                <button @click.stop="deleteProject(p.id)" class="btn-icon">🗑️</button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </template>
    
    <style scoped>
    /* AQUI ESTÁ A CORREÇÃO DE LAYOUT DO DASHBOARD */
    .dashboard-page {
      /* Removemos min-height: 100vh pois o App.vue já tem altura fixa */
      flex: 1; 
      display: flex;
      flex-direction: column;
      overflow-y: auto; /* Permite rolar o dashboard sem rolar a barra */
      background-color: #121212;
      color: #ecf0f1;
    }
    
    /* Header */
    .dash-header { background: #181818; border-bottom: 1px solid #333; width: 100%; flex-shrink: 0; }
    .header-inner { max-width: 1200px; margin: 0 auto; padding: 30px 40px; }
    .welcome-text h1 { font-size: 2.2rem; margin: 0; font-weight: 800; letter-spacing: -1px; }
    .gradient-text { background: linear-gradient(to right, #e67e22, #f1c40f); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .subtitle { color: #888; margin: 8px 0 0 0; font-size: 1rem; }
    
    /* Content Area */
    .content-area { padding: 40px; max-width: 1200px; margin: 0 auto; width: 100%; box-sizing: border-box; animation: fadeIn 0.6s ease-out; }
    
    /* Grid & Cards */
    .projects-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 30px; }
    .card { background: #1e1e1e; border-radius: 16px; overflow: hidden; cursor: pointer; transition: all 0.3s; border: 1px solid #333; box-shadow: 0 4px 10px rgba(0,0,0,0.3); display: flex; flex-direction: column; }
    .card:hover { transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.5); border-color: #555; }
    
    /* Create Card */
    .create-card { background: rgba(255,255,255,0.03); border: 2px dashed #444; align-items: center; justify-content: center; min-height: 240px; }
    .create-card:hover { border-color: #e67e22; background: rgba(230, 126, 34, 0.05); }
    .icon-circle { width: 60px; height: 60px; border-radius: 50%; background: #252526; display: flex; align-items: center; justify-content: center; margin-bottom: 15px; border: 1px solid #444; transition: 0.3s; }
    .create-card:hover .icon-circle { background: #e67e22; border-color: #e67e22; transform: scale(1.1); }
    .plus { font-size: 2rem; color: #aaa; line-height: 1; }
    .create-card:hover .plus { color: white; }
    .create-label { font-weight: bold; color: #888; transition: 0.3s; }
    .create-card:hover .create-label { color: #e67e22; }
    
    /* Project Card */
    .card-thumb { height: 160px; background-size: cover; background-position: center; background-color: #000; position: relative; }
    .overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; opacity: 0; transition: 0.2s; backdrop-filter: blur(3px); }
    .card:hover .overlay { opacity: 1; }
    .open-btn { background: #e67e22; color: white; padding: 8px 20px; border-radius: 20px; font-weight: bold; font-size: 0.85rem; box-shadow: 0 4px 10px rgba(0,0,0,0.4); }
    .card-info { padding: 15px; background: #252526; border-top: 1px solid #333; display: flex; justify-content: space-between; align-items: center; flex-grow: 1; }
    .info-left h3 { margin: 0; font-size: 0.95rem; color: #fff; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 130px; }
    .date { font-size: 0.7rem; color: #777; margin-top: 4px; display: block; }
    .btn-icon { background: transparent; border: none; cursor: pointer; font-size: 1.1rem; opacity: 0.4; transition: 0.2s; padding: 6px; border-radius: 6px; }
    .btn-icon:hover { opacity: 1; background: rgba(231, 76, 60, 0.15); transform: scale(1.1); }
    
    /* Loading */
    .loading-state { text-align: center; margin-top: 80px; color: #666; }
    .spinner { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1); border-top-color: #e67e22; border-radius: 50%; animation: spin 1s infinite linear; margin: 0 auto 15px; }
    @keyframes spin { to { transform: rotate(360deg); } }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
    </style>