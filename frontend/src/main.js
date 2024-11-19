import './assets/main.css';
import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';
const app = createApp(App);
// Install Pinia and Router
app.use(createPinia());
app.use(router);
// Mount the app to the DOM
app.mount('#app');
//# sourceMappingURL=main.js.map