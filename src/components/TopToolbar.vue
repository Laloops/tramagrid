<script setup>
  // Futuramente entra lógica de usuário aqui
  </script>
  
  <template>
    <header class="header">
      <div class="brand">
        <h1 class="logo-text">Trama<span class="highlight">Grid</span></h1>
      </div>
      
      <div class="user-area">
        <div class="credits-pill">💎 0 Créditos</div>
        <div class="user-avatar">👤</div>
      </div>
    </header>
  </template>
  
  <style scoped>
  .header {
    background: #2c3e50;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    color: white;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    z-index: 10;
  }
  
  .logo-text {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
    color: #ecf0f1;
    letter-spacing: -1px;
  }
  
  .highlight {
    color: #e67e22; /* Laranja cobre */
  }
  
  .user-area {
    display: flex;
    align-items: center;
    gap: 15px;
  }
  
  .credits-pill {
    background: rgba(0,0,0,0.3);
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    color: #f1c40f; /* Dourado */
    border: 1px solid rgba(241, 196, 15, 0.3);
  }
  
  .user-avatar {
    background: #444;
    width: 35px;
    height: 35px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    border: 2px solid #555;
  }
  </style>