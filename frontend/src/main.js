import { createApp } from 'vue';
import { createRouter, createWebHistory } from 'vue-router';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';

import App from './App.vue';

import HomePage from './components/DashboardPage.vue'; 
import ForecastBuilder from './components/ForecastBuilder.vue' 

const routes = [
  { path: '/', component: HomePage }, 
    {
    path: '/builder', // 2. Defina o caminho para a nova página
    name: 'ForecastBuilder',
    component: ForecastBuilder
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

const app = createApp(App);
app.use(router);
app.mount('#app');