FROM node:20-alpine

RUN npm install -g pnpm@9

WORKDIR /app

# Copy workspace manifests first (layer cache for deps)
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./
COPY shared/package.json ./shared/
COPY frontend/package.json ./frontend/

RUN pnpm install --frozen-lockfile

# Source is mounted as a volume in dev — no COPY needed at runtime
WORKDIR /app/frontend

EXPOSE 3000
CMD ["pnpm", "dev", "--hostname", "0.0.0.0"]
