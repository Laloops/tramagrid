<script setup>
  import { ref, computed, onMounted, onUnmounted } from 'vue'
  import { useRouter } from 'vue-router'
  import { supabase } from '../supabase'
  import { eventBus } from '../api.js'
  
  const router = useRouter()
  
  const user = ref(null)
  const userProfile = ref(null)
  const isMenuOpen = ref(false)
  
  const isLoggedIn = computed(() => !!user.value)
  const userAvatar = computed(() => user.value?.user_metadata?.avatar_url || '')
  const userInitial = computed(() => user.value?.email ? user.value.email[0].toUpperCase() : 'U')
  const userName = computed(() => user.value?.user_metadata?.full_name || 'Usuário')
  const userEmail = computed(() => user.value?.email || '')
  
  const credits = computed(() => userProfile.value?.credits || 0)
  const isFree = computed(() => userProfile.value && !userProfile.value.free_generation_used)

  async function fetchUser() {
    const { data } = await supabase.auth.getUser()
    user.value = data.user
    
    if (user.value) {
      let { data: profile } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', user.value.id)
        .maybeSingle()
      
      if (!profile) {
          const { data: newProfile, error } = await supabase
            .from('profiles')
            .insert([{ id: user.value.id, email: user.value.email, credits: 0, free_generation_used: false }])
            .select()
            .single()
          if (!error) profile = newProfile
      }
      if (profile) userProfile.value = profile
    } else {
      userProfile.value = null
    }
  }

  async function handleLogout() {
    await supabase.auth.signOut()
    user.value = null
    userProfile.value = null
    isMenuOpen.value = false
    router.push('/login')
  }

  function toggleMenu() { isMenuOpen.value = !isMenuOpen.value }
  function closeMenu() { isMenuOpen.value = false }

  onMounted(() => {
    fetchUser()
    supabase.auth.onAuthStateChange((event, session) => {
      if (session?.user) { user.value = session.user; fetchUser(); } 
      else { user.value = null; userProfile.value = null; }
    })
    eventBus.addEventListener('credits-updated', fetchUser)
  })

  onUnmounted(() => eventBus.removeEventListener('credits-updated', fetchUser))
</script>
    
<template>
  <header class="header">
    <div class="brand">
      <router-link to="/" class="logo-link">
        <h1 class="logo-text">Trama<span class="highlight">Grid</span></h1>
      </router-link>
    </div>
    
    <div class="user-area">
      <template v-if="isLoggedIn">
        <router-link to="/buy-credits" class="credits-pill" :class="{ 'free-tier': isFree }">
          <span v-if="isFree">🎁 1 Grátis</span>
          <span v-else>💎 {{ credits }}</span>
        </router-link>
        <div class="avatar-container" @click="toggleMenu">
            <img v-if="userAvatar" :src="userAvatar" class="avatar-img" alt="User" />
            <div v-else class="avatar-placeholder">{{ userInitial }}</div>
        </div>
        <div v-if="isMenuOpen" class="menu-backdrop" @click="closeMenu"></div>
        <transition name="fade">
            <div v-if="isMenuOpen" class="user-menu">
                <div class="menu-header">
                    <p class="name">{{ userName }}</p>
                    <p class="email">{{ userEmail }}</p>
                </div>
                <div class="menu-divider"></div>
                <router-link to="/dashboard" class="menu-item" @click="closeMenu">📊 Meus Arquivos</router-link>
                <router-link to="/buy-credits" class="menu-item" @click="closeMenu">💳 Comprar Créditos</router-link>
                <div class="menu-divider"></div>
                <button @click="handleLogout" class="menu-item danger">🚪 Sair</button>
            </div>
        </transition>
      </template>
      <template v-else>
        <router-link to="/login" class="btn-login">Entrar</router-link>
      </template>
    </div>
  </header>
</template>
    
<style scoped>
.header { 
  background: #181818; 
  height: 60px; 
  flex-shrink: 0; 
  display: flex; 
  align-items: center; 
  justify-content: space-between; 
  padding: 0 25px; 
  border-bottom: 1px solid #333; 
  z-index: 200; 
  position: relative; 
}

.logo-link { text-decoration: none; }
.logo-text { margin: 0; font-size: 1.4rem; font-weight: 700; color: #eee; letter-spacing: -0.5px; }
.highlight { color: #e67e22; }
.user-area { display: flex; align-items: center; gap: 15px; position: relative; }

/* --- AQUI ESTÁ A MUDANÇA PARA ALINHAR --- */
.credits-pill { 
  background: rgba(241, 196, 15, 0.1); 
  height: 40px; /* Altura fixa igual ao avatar */
  padding: 0 20px; /* Padding apenas lateral */
  display: flex; /* Flex para centralizar o texto verticalmente */
  align-items: center;
  justify-content: center;
  border-radius: 20px; 
  font-size: 0.9rem; 
  font-weight: 600; 
  color: #f1c40f; 
  border: 1px solid rgba(241, 196, 15, 0.3); 
  white-space: nowrap; 
  user-select: none; 
  text-decoration: none; 
  transition: 0.2s;
  box-sizing: border-box; /* Garante que a borda não aumente o tamanho */
}
.credits-pill:hover { background: rgba(241, 196, 15, 0.2); }
.credits-pill.free-tier { background: rgba(46, 204, 113, 0.15); color: #2ecc71; border-color: #2ecc71; }

.avatar-container { cursor: pointer; transition: transform 0.2s; position: relative; z-index: 202; }
.avatar-container:hover { transform: scale(1.05); }

/* Avatar com box-sizing para manter 40px exatos com a borda */
.avatar-img { 
  width: 40px; 
  height: 40px; 
  border-radius: 50%; 
  border: 2px solid #444; 
  object-fit: cover; 
  display: block; 
  box-sizing: border-box; 
}
.avatar-placeholder { 
  width: 40px; 
  height: 40px; 
  border-radius: 50%; 
  background: #333; 
  border: 2px solid #444; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  color: #ddd; 
  font-weight: bold; 
  font-size: 1.1rem; 
  box-sizing: border-box;
}

.user-menu { position: absolute; top: 55px; right: 0; width: 220px; background: #252526; border: 1px solid #444; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.5); overflow: hidden; z-index: 202; padding: 5px 0; }
.menu-header { padding: 15px 20px; background: #2c2c2c; border-bottom: 1px solid #333; }
.name { margin: 0; font-weight: bold; color: white; font-size: 0.95rem; }
.email { margin: 2px 0 0 0; color: #888; font-size: 0.75rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.menu-item { display: block; padding: 10px 20px; color: #ccc; text-decoration: none; font-size: 0.9rem; transition: background 0.2s; border: none; background: transparent; width: 100%; text-align: left; cursor: pointer; box-sizing: border-box; }
.menu-item:hover { background: #333; color: white; }
.menu-item.danger { color: #e74c3c; }
.menu-item.danger:hover { background: rgba(231, 76, 60, 0.1); }
.menu-divider { height: 1px; background: #333; margin: 5px 0; }
.menu-backdrop { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 201; cursor: default; }
.btn-login { background: #e67e22; color: white; text-decoration: none; padding: 8px 20px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; transition: 0.2s; }
.btn-login:hover { background: #d35400; transform: translateY(-1px); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s, transform 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-10px); }
</style>