import { createRouter, createWebHistory } from 'vue-router'
import MixView from './views/MixView.vue'
import ResultsView from './views/ResultsView.vue'
import SettingsView from './views/SettingsView.vue'
import DemoView from './views/DemoView.vue'
import AboutView from './views/AboutView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'mix', component: MixView },
    { path: '/results', name: 'results', component: ResultsView },
    { path: '/settings', name: 'settings', component: SettingsView },
    { path: '/demo', name: 'demo', component: DemoView },
    { path: '/about', name: 'about', component: AboutView },
  ],
})

export default router
