<script setup>
  import { ref, onMounted } from 'vue'
  import { useRouter, useRoute } from 'vue-router'
  import { supabase } from '../supabase'
  
  const router = useRouter()
  const route = useRoute()
  const loading = ref(false)
  const user = ref(null)
  
  onMounted(async () => {
    if (route.query.success) {
      alert("✅ Pagamento aprovado! Créditos adicionados.")
      router.replace('/buy-credits')
    }
    const { data } = await supabase.auth.getUser()
    user.value = data.user
  })
  
  async function buyPack(quantity) {
    if (!user.value) {
      alert("Faça login ou crie uma conta para continuar.")
      router.push('/login')
      return
    }
  
    loading.value = true
    try {
      const res = await fetch('/api/create-checkout-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity, user_id: user.value.id })
      })
      const data = await res.json()
      if (data.url) window.location.href = data.url
      else alert("Erro ao conectar com o pagamento.")
    } catch (e) {
      console.error(e)
      alert("Erro de conexão.")
    } finally {
      loading.value = false
    }
  }
  </script>
  
  <template>
    <div class="credits-page">
      <div class="content-wrapper">
        
        <header class="page-header">
          <h1>Escolha seu Pacote</h1>
          <p>Sem mensalidades. Seus créditos nunca expiram.</p>
        </header>
  
        <div class="plans-grid">
          
          <div class="plan-card">
            <div class="plan-header">
              <h3>Curioso</h3>
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
  
        <button @click="router.push('/')" class="btn-back">Cancelar e Voltar</button>
      </div>
    </div>
  </template>
  
  <style scoped>
  .credits-page {
    min-height: calc(100vh - 60px); 
    background-color: #121212;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    box-sizing: border-box;
  }
  
  .content-wrapper { width: 100%; max-width: 950px; text-align: center; }
  
  .page-header h1 {
    font-size: 2.2rem; margin: 0 0 10px 0;
    background: linear-gradient(to right, #e67e22, #f1c40f);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  .page-header p { color: #aaa; font-size: 1rem; margin: 0 0 40px 0; }
  
  .plans-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 20px;
    align-items: center; 
  }
  
  /* Cards */
  .plan-card {
    background: #1e1e1e;
    border: 1px solid #333;
    border-radius: 16px;
    padding: 30px 20px;
    display: flex; flex-direction: column;
    position: relative;
    transition: transform 0.3s;
  }
  .plan-card:hover { transform: translateY(-5px); border-color: #555; }
  
  /* Destaque */
  .plan-card.popular {
    border: 2px solid #e67e22;
    background: linear-gradient(180deg, rgba(230,126,34,0.08) 0%, #1e1e1e 100%);
    transform: scale(1.08);
    z-index: 2;
    box-shadow: 0 10px 40px rgba(0,0,0,0.5);
  }
  .plan-card.popular:hover { transform: scale(1.1) translateY(-5px); }
  
  .badge {
    position: absolute; top: -12px; left: 50%; transform: translateX(-50%);
    background: #e67e22; color: white; padding: 4px 12px;
    border-radius: 12px; font-size: 0.7rem; font-weight: bold;
    letter-spacing: 1px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);
  }
  
  .plan-header h3 { color: #888; font-size: 0.85rem; letter-spacing: 2px; margin: 0; text-transform: uppercase; }
  .price { display: block; font-size: 2rem; font-weight: 700; color: white; margin: 15px 0; }
  
  .plan-body { flex-grow: 1; margin-bottom: 20px; }
  .credit-count { font-size: 1.2rem; font-weight: bold; color: #e67e22; margin-bottom: 5px; }
  .desc { font-size: 0.85rem; color: #aaa; margin: 0; min-height: 40px; }
  .divider { height: 1px; background: #333; margin: 15px 0; }
  .unit-price { font-size: 0.9rem; color: #666; font-weight: 600; }
  .unit-price.highlight { color: #2ecc71; }
  
  button {
    background: transparent; color: white; border: 1px solid #555;
    padding: 14px; border-radius: 8px; font-weight: bold; cursor: pointer;
    transition: 0.2s; width: 100%; font-size: 0.95rem;
  }
  button:hover:not(:disabled) { border-color: white; background: rgba(255,255,255,0.05); }
  .btn-highlight { background: #e67e22; color: white; border: none; }
  .btn-highlight:hover:not(:disabled) { background: #d35400; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(230,126,34,0.3); }
  button:disabled { opacity: 0.5; cursor: wait; }
  
  .btn-back { background: transparent; color: #666; border: none; font-size: 0.9rem; margin-top: 30px; width: auto; padding: 0; text-decoration: underline; }
  .btn-back:hover { color: white; background: transparent; }
  </style>