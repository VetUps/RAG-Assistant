import { createRouter, createWebHistory } from 'vue-router'

import index from '../Views/HomeView.vue' 
import info_team from '../Views/InfoTeamView.vue'

const routes = [
  {
    path: '/',
    name: 'Index',
    component: index  
  },
  {
    path: "/info",
    name: "Info_team",
    component: info_team
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router