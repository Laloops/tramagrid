<script setup>
  import TopToolbar from './components/TopToolbar.vue'
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