import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base relativa para que funcione en cualquier host estático (Vercel/Netlify/Pages)
export default defineConfig({
  plugins: [react()],
  base: './',
})
