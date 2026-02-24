# Build stage
FROM oven/bun:latest AS builder

WORKDIR /app

# Copy config files
COPY package.json ./
COPY vite.config.js ./
COPY postcss.config.js ./
COPY tailwind.config.js ./
COPY tsconfig.json ./
COPY svelte.config.js ./

# Install dependencies with Bun
RUN bun install

# Copy source
COPY src ./src
COPY static ./static

# Build
RUN bun run build

# Production stage
FROM oven/bun:latest

WORKDIR /app

# Copy built assets
COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./

# Install production dependencies
RUN bun install --production

# Expose port
EXPOSE 3000

ENV PORT=3000
ENV HOST=0.0.0.0

# Start
CMD ["bun", "./build/index.js"]
