# Dockerfile для Frontend
FROM node:18-alpine AS base

# Встановлення залежностей тільки при зміні package.json
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Копіювання package.json та package-lock.json
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# Збірка додатку
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Відключення телеметрії Next.js
ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# Production образ
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Копіювання файлів збірки
COPY --from=builder /app/public ./public

# Автоматичне використання output trace для зменшення розміру образу
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

CMD ["node", "server.js"]
