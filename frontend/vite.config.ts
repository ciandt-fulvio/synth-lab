import { defineConfig } from "vite";
import dyadComponentTagger from "@dyad-sh/react-vite-component-tagger";
import react from "@vitejs/plugin-react-swc";
import path from "path";

export default defineConfig(() => {
  // Use Docker network hostname if available, otherwise localhost
  const backendHost = process.env.VITE_BACKEND_HOST || 'localhost';
  const backendPort = process.env.VITE_API_PORT || "8000";
  const backendUrl = `http://${backendHost}:${backendPort}`;

  const proxyConfig = {
    '/api': {
      target: backendUrl,
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    },
    '/static': {
      target: backendUrl,
      changeOrigin: true
    }
  };

  const port = parseInt(process.env.VITE_PORT || "8080");

  return {
    server: {
      // Bind to all interfaces for Docker access
      host: "0.0.0.0",
      port: port,
      proxy: proxyConfig,
      // HMR configuration for Docker
      hmr: {
        // Use same port as exposed by Docker
        clientPort: port,
        // Host for browser WebSocket connection
        host: "localhost",
      },
      // File watching for Docker volumes
      watch: {
        usePolling: true,
        interval: 100,
      },
    },
    preview: {
      host: "0.0.0.0",
      port: port,
      proxy: proxyConfig
    },
    plugins: [dyadComponentTagger(), react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
  };
});
