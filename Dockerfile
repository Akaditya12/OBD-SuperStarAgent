# ============================================================
#  OBD SuperStar Agent — Combined Dockerfile
#  Runs both backend (FastAPI) and frontend (Next.js)
# ============================================================

# ── Stage 1: Build the Next.js frontend ──
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy package files first for layer caching
COPY frontend/package.json ./
COPY frontend/package-lock.json ./
RUN npm ci

# Copy rest of frontend source and build
COPY frontend/ .
ENV BACKEND_URL=http://localhost:8000
RUN npm run build

# ── Stage 2: Install Python dependencies ──
FROM python:3.11-slim AS python-deps
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 3: Final runtime image ──
FROM python:3.11-slim

# Install Node.js (copy from the official node image instead of NodeSource)
COPY --from=node:20-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:20-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -sf /usr/local/bin/node /usr/local/bin/nodejs

WORKDIR /app

# Copy Python packages from deps stage
COPY --from=python-deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Copy backend code
COPY backend/ ./backend/

# Copy sample products
COPY sample_products/ ./sample_products/

# Copy built frontend (standalone output from Next.js)
COPY --from=frontend-builder /app/frontend/.next/standalone ./frontend-standalone/
COPY --from=frontend-builder /app/frontend/.next/static ./frontend-standalone/.next/static

# Copy public folder
COPY frontend/public/ ./frontend-standalone/public/

# Create outputs directory
RUN mkdir -p /app/backend/outputs

# Copy and prepare startup script
COPY render-start.sh ./render-start.sh
RUN chmod +x render-start.sh

EXPOSE 8000 3000

CMD ["./render-start.sh"]
