# Multi-stage Dockerfile for synth-lab frontend
# Stage 1: Build assets
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build production assets
RUN npm run build

# Stage 2: Serve built assets
FROM node:20-alpine

WORKDIR /app

# Copy built assets from builder
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/vite.config.ts ./

# Install all dependencies (Vite is needed for preview mode)
RUN npm ci

# Expose port
EXPOSE 8080

# Serve using Vite preview mode with proxy support
CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "8080"]
