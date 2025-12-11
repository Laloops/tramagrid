<script setup>
  import { ref, onMounted } from 'vue'
  import { supabase } from '../supabase'
  
  const credits = ref(null)
  const isFree = ref(false)
  const userAvatar = ref('👤')
  
  onMounted(async () => {
    // 1. Pega usuário atual
    const { data: { user } } = await supabase.auth.getUser()
    
    if (user) {
      userAvatar.value = user.email ? user.email[0].toUpperCase() : 'U'
      
      // 2. Busca perfil no banco
      const { data: profile, error } = await supabase
        .from('profiles')
        .select('credits, free_generation_used')
        .eq('id', user.id)
        .single()
  
      if (profile) {
        // Lógica de exibição
        if (!profile.free_generation_used) {
          isFree.value = true // Ainda tem a gratuita
          credits.value = 1
        } else {
          isFree.value = false
          credits.value = profile.credits
        }
      }
    }
  })
  </script>
    
  <template>
    <header class="header">
      <div class="brand">
        <h1 class="logo-text">Trama<span class="highlight">Grid</span></h1>
      </div>
      
      <div class="user-area">
        <div v-if="credits !== null" class="credits-pill" :class="{ 'free-tier': isFree }">
          <span v-if="isFree">🎁 1 Grátis</span>
          <span v-else>💎 {{ credits }} Créditos</span>
        </div>
        
        <div class="user-avatar">{{ userAvatar }}</div>
      </div>
    </header>
  </template>
    
  <style scoped>
  /* (Mesmo CSS de antes, adicione apenas a classe .free-tier) */
  .header { background: #181818; height: 60px; display: flex; align-items: center; justify-content: space-between; padding: 0 25px; border-bottom: 1px solid #333; z-index: 20; }
  .logo-text { margin: 0; font-size: 1.4rem; font-weight: 700; color: #eee; letter-spacing: -0.5px; user-select: none; }
  .highlight { color: #e67e22; }
  .user-area { display: flex; align-items: center; gap: 20px; }
  
  .credits-pill {
    background: rgba(241, 196, 15, 0.1); padding: 6px 14px; border-radius: 20px;
    font-size: 0.8rem; font-weight: 600; color: #f1c40f; border: 1px solid rgba(241, 196, 15, 0.3);
  }
  /* Estilo especial para quando é grátis */
  .credits-pill.free-tier {
    background: rgba(46, 204, 113, 0.15); color: #2ecc71; border-color: #2ecc71;
  }
  
  .user-avatar { background: #333; width: 38px; height: 38px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #ddd; border: 2px solid #444; font-weight: bold; }
  </style>