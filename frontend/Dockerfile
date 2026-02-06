# Multi-stage Dockerfile for React/Vite frontend
# Stage 1: Build
FROM node:20-slim AS builder

# Accept build arguments for Vite environment variables
ARG VITE_API_URL
ARG VITE_COMMIT_SHA
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_COMMIT_SHA=${VITE_COMMIT_SHA}

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source code
COPY . .

# Build the app (Vite will use VITE_API_URL during build)
RUN npm run build

# Stage 2: Production
FROM node:20-slim

WORKDIR /app

# Install serve to run the static files
RUN npm install -g serve

# Copy built assets from builder
COPY --from=builder /app/dist ./dist

# Expose port (Railway sets PORT env var)
EXPOSE 3000

# Serve the static files
CMD ["sh", "-c", "serve dist -s -l ${PORT:-3000}"]
