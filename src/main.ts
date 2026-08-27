import { createApp } from 'vue'
import App from './App.vue'
import './styles.css'

declare global {
  interface Window {
    _AMapSecurityConfig?: { securityJsCode?: string }
  }
}

if (import.meta.env.VITE_AMAP_SECURITY_CODE) {
  window._AMapSecurityConfig = {
    securityJsCode: import.meta.env.VITE_AMAP_SECURITY_CODE,
  }
  console.log('[Main] 已在应用入口注入 window._AMapSecurityConfig')
}

createApp(App).mount('#app')

