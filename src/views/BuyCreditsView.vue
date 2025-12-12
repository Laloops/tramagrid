<script setup>
  import { ref, onMounted } from 'vue'
  import { useRouter, useRoute } from 'vue-router'
  import { supabase } from '../supabase'
  import { showToast } from '../toast.js' // <--- Importando nosso Toast
  
  const router = useRouter()
  const route = useRoute()
  const loading = ref(false)
  const user = ref(null)
  
  onMounted(async () => {
    // Se voltou do Stripe com sucesso
    if (route.query.success) {
      showToast("Pagamento aprovado! Créditos adicionados.", "success")
      router.replace('/buy-credits') // Limpa a URL
    }
  
    const { data } = await supabase.auth.getUser()
    user.value = data.user
  })
  
  async function buyPack(quantity) {
    if (!user.value) {
      showToast("Faça login para comprar créditos!", "warning")
      router.push('/login')
      return
    }
  
    loading.value = true
    try {
      const res = await fetch('/api/create-checkout-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          quantity: quantity, 
          user_id: user.value.id 
        })
      })
  
      const data = await res.json()
      if (data.url) {
        window.location.href = data.url
      } else {
        showToast("Erro ao iniciar pagamento.", "error")
      }
    } catch (e) {
      console.error(e)
      showToast("Erro de conexão com o servidor.", "error")
    } finally {
      loading.value = false
    }
  }
  </script>
  
  <template>
    <div class="credits-page">
      <div class="content-wrapper">
        
        <header class="page-header">
          <h1>Invista na sua Arte</h1>
          <p>Gere gráficos profissionais em segundos.</p>
        </header>
  
        <div class="plans-grid">
          
          <div class="plan-card">
            <div class="plan-header">
              <h3>Iniciante</h3>
              <span class="price">R$ 9,90</span>
            </div>
            <div class="plan-body">
              <div class="credit-count">2 Créditos</div>
              <p class="desc">Para testar e criar seus primeiros gráficos.</p>
              <div class="divider"></div>
              <span class="unit-price">R$ 4,95 / gráfico</span>
            </div>
            <button @click="buyPack(2)" :disabled="loading">Comprar</button>
          </div>
  
          <div class="plan-card popular">
            <div class="badge">RECOMENDADO</div>
            <div class="plan-header">
              <h3>Artesão</h3>
              <span class="price">R$ 29,90</span>
            </div>
            <div class="plan-body">
              <div class="credit-count">10 Créditos</div>
              <p class="desc">Perfeito para quem cria regularmente.</p>
              <div class="divider"></div>
              <span class="unit-price highlight">R$ 2,99 / gráfico</span>
            </div>
            <button class="btn-highlight" @click="buyPack(10)" :disabled="loading">Comprar</button>
          </div>
  
          <div class="plan-card">
            <div class="plan-header">
              <h3>Ateliê</h3>
              <span class="price">R$ 89,90</span>
            </div>
            <div class="plan-body">
              <div class="credit-count">50 Créditos</div>
              <p class="desc">Volume profissional com máximo desconto.</p>
              <div class="divider"></div>
              <span class="unit-price">R$ 1,79 / gráfico</span>
            </div>
            <button @click="buyPack(50)" :disabled="loading">Comprar</button>
          </div>
  
        </div>
  
        <button @click="router.push('/')" class="btn-back">← Voltar</button>
      </div>
    </div>
  </template>
  
  <style scoped>
  /* Container Principal: Centraliza e ocupa a altura disponível */
  .credits-page {
    /* Desconta os 60px do header para centralizar exatamente no meio da área visível */
    min-height: calc(100vh - 60px); 
    background-color: #121212;
    color: white;
    display: flex;
    align-items: center; /* Centraliza verticalmente */
    justify-content: center;
    padding: 20px; /* Padding externo pequeno */
    box-sizing: border-box;
  }
  
  .content-wrapper {
    width: 100%;
    max-width: 900px; /* Largura máxima controlada para não esticar demais */
    text-align: center;
  }
  
  /* Header mais compacto */
  .page-header h1 {
    font-size: 2rem; 
    margin: 0 0 5px 0;
    background: linear-gradient(to right, #e67e22, #f1c40f);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  
  .page-header p {
    color: #aaa;
    font-size: 1rem;
    margin: 0 0 30px 0; /* Menos margem */
  }
  
  /* Grid ajustado */
  .plans-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); /* Cards mais estreitos */
    gap: 20px;
    margin-bottom: 20px;
    align-items: stretch; 
  }
  
  /* Cartões Compactos */
  .plan-card {
    background: #1e1e1e;
    border: 1px solid #333;
    border-radius: 16px;
    padding: 25px 20px; /* Padding interno reduzido */
    display: flex;
    flex-direction: column;
    position: relative;
    transition: transform 0.3s, box-shadow 0.3s;
  }
  
  .plan-card:hover {
    transform: translateY(-5px);
    border-color: #555;
    box-shadow: 0 10px 25px rgba(0,0,0,0.4);
  }
  
  .plan-card.popular {
    border: 2px solid #e67e22;
    background: linear-gradient(180deg, rgba(230,126,34,0.08) 0%, #1e1e1e 100%);
    transform: scale(1.05);
    box-shadow: 0 8px 30px rgba(230, 126, 34, 0.15);
    z-index: 2;
  }
  
  .plan-card.popular:hover {
    transform: scale(1.08) translateY(-5px);
  }
  
  .badge {
    position: absolute;
    top: -12px;
    left: 50%;
    transform: translateX(-50%);
    background: #e67e22;
    color: white;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: bold;
    letter-spacing: 0.5px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
  }
  
  .plan-header h3 {
    color: #888;
    font-size: 0.8rem;
    letter-spacing: 1px;
    margin: 0;
    text-transform: uppercase;
  }
  
  .price {
    display: block;
    font-size: 1.8rem; /* Preço menor */
    font-weight: 700;
    color: white;
    margin: 10px 0;
  }
  
  .plan-body {
    flex-grow: 1;
    margin-bottom: 15px;
  }
  
  .credit-count {
    font-size: 1.1rem;
    font-weight: bold;
    color: #e67e22;
    margin-bottom: 5px;
  }
  
  .desc {
    font-size: 0.8rem;
    color: #aaa;
    margin: 0;
    min-height: 35px; /* Altura mínima para alinhar */
  }
  
  .divider { height: 1px; background: #333; margin: 12px 0; }
  
  .unit-price { font-size: 0.85rem; color: #666; font-weight: 600; }
  .unit-price.highlight { color: #2ecc71; }
  
  button {
    background: transparent;
    color: white;
    border: 1px solid #555;
    padding: 12px;
    border-radius: 8px;
    font-weight: bold;
    cursor: pointer;
    transition: 0.2s;
    width: 100%;
    font-size: 0.9rem;
  }
  
  button:hover:not(:disabled) {
    border-color: white;
    background: rgba(255,255,255,0.05);
  }
  
  .btn-highlight {
    background: #e67e22;
    color: white;
    border: none;
    box-shadow: 0 4px 10px rgba(230, 126, 34, 0.3);
  }
  
  .btn-highlight:hover:not(:disabled) {
    background: #d35400;
    transform: translateY(-2px);
  }
  
  button:disabled { opacity: 0.5; cursor: wait; }
  
  .btn-back {
    background: transparent;
    color: #666;
    border: none;
    font-size: 0.9rem;
    margin-top: 10px;
    padding: 8px 20px;
  }
  .btn-back:hover { color: white; text-decoration: underline; }
  </style>