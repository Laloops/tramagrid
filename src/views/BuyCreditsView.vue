<script setup>
    import { useRouter } from 'vue-router'
    const router = useRouter()
    
    function handleBuy(amount) {
        alert(`Integração de pagamento em breve!\nVocê escolheu ${amount} créditos.`)
        // Futuro: Redirecionar para Stripe/MercadoPago
    }
    </script>
    
    <template>
      <div class="buy-container">
        <h1>Precisa de mais gráficos?</h1>
        <p class="subtitle">Escolha um pacote e continue criando.</p>
    
        <div class="cards-grid">
          <div class="card">
            <div class="amount">5</div>
            <div class="label">Créditos</div>
            <div class="price">R$ 15,00</div>
            <button @click="handleBuy(5)">Comprar</button>
          </div>
    
          <div class="card popular">
            <div class="badge">MAIS POPULAR</div>
            <div class="amount">15</div>
            <div class="label">Créditos</div>
            <div class="price">R$ 35,00</div>
            <button @click="handleBuy(15)">Comprar</button>
          </div>
    
          <div class="card">
            <div class="amount">50</div>
            <div class="label">Créditos</div>
            <div class="price">R$ 90,00</div>
            <button @click="handleBuy(50)">Comprar</button>
          </div>
        </div>
    
        <button @click="router.push('/editor')" class="btn-back">Voltar para o Editor</button>
      </div>
    </template>
    
    <style scoped>
    .buy-container { height: 100vh; background: #121212; color: white; display: flex; flex-direction: column; align-items: center; justify-content: center; }
    h1 { color: #e67e22; margin-bottom: 10px; }
    .subtitle { color: #aaa; margin-bottom: 40px; }
    
    .cards-grid { display: flex; gap: 20px; align-items: center; }
    .card { background: #252526; padding: 30px; border-radius: 12px; border: 1px solid #333; text-align: center; width: 200px; transition: 0.3s; position: relative; }
    .card:hover { transform: translateY(-5px); border-color: #e67e22; }
    
    .card.popular { transform: scale(1.1); border-color: #e67e22; box-shadow: 0 0 20px rgba(230, 126, 34, 0.2); z-index: 2; }
    .badge { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #e67e22; font-size: 0.7rem; padding: 4px 8px; border-radius: 10px; font-weight: bold; }
    
    .amount { font-size: 3rem; font-weight: 800; color: white; line-height: 1; }
    .label { color: #888; text-transform: uppercase; font-size: 0.8rem; margin-bottom: 20px; letter-spacing: 2px; }
    .price { font-size: 1.5rem; color: #2ecc71; margin-bottom: 20px; font-weight: bold; }
    
    button { background: white; color: black; border: none; padding: 10px 20px; border-radius: 20px; font-weight: bold; cursor: pointer; width: 100%; transition: 0.2s; }
    .popular button { background: #e67e22; color: white; }
    button:hover { opacity: 0.9; transform: scale(1.05); }
    
    .btn-back { background: transparent; color: #666; width: auto; margin-top: 40px; }
    .btn-back:hover { color: white; background: transparent; transform: none; text-decoration: underline; }
    </style>