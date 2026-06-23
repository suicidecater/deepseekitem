// src/main.ts
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { pinia } from './stores'
import './assets/styles/reset.css'
import './assets/styles/variables.css'
import './assets/styles/global.css'
import './assets/styles/transitions.css'

const app = createApp(App)
app.use(pinia)
app.use(router)
app.mount('#app')
