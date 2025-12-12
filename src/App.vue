<script setup>
  import { onMounted } from 'vue'
  import { supabase } from './supabase'
  import { useRouter } from 'vue-router'
  import TopToolbar from './components/TopToolbar.vue'
  
  const router = useRouter()

  onMounted(() => {
    // Escuta mudanças de auth globais (incluindo o retorno do Link Mágico)
    supabase.auth.onAuthStateChange((event, session) => {
      console.log("🔔 [App.vue] Evento de Auth:", event)
      
      if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
        // Se o usuário acabou de logar vindo do email (SIGNED_IN), 
        // podemos redirecionar para onde quisermos, ou deixar na home.
        console.log("✅ Usuário logado e sessão recuperada!")
      }
    })
  })
</script>
  
<template>
  <div class="app-layout">
    <TopToolbar />
    <router-view />
  </div>
</template>
  
<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}
</style>