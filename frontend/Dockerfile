# Dockerfile для Frontend
FROM node:18-alpine AS base

# Встановлення системних залежностей
RUN apk add --no-cache libc6-compat curl

# Встановлення залежностей
FROM base AS deps
WORKDIR /app

# Копіювання package files
COPY package.json package-lock.json* ./

# Встановлення залежностей для збірки (handle absence of package-lock.json)
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Збірка додатку
FROM base AS builder
WORKDIR /app

# Копіювання залежностей з попереднього етапу
COPY --from=deps /app/node_modules ./node_modules

# Копіювання всіх файлів проекту
COPY . .

# Відключення телеметрії Next.js
ENV NEXT_TELEMETRY_DISABLED 1

# Збірка Next.js додатку
RUN npm run build

# Production образ
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Створення користувача
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Копіювання public директорії
COPY --from=builder /app/public ./public

# Копіювання збірки Next.js
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Створення директорії для логів
RUN mkdir -p /app/logs && chown nextjs:nodejs /app/logs

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

CMD ["node", "server.js"]
