import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import EditorView from './views/EditorView.vue'
import LoginView from './views/LoginView.vue' 
import BuyCreditsView from './views/BuyCreditsView.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/editor', component: EditorView },
  { path: '/login', component: LoginView },
  { path: '/buy-credits', component: BuyCreditsView } 
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router