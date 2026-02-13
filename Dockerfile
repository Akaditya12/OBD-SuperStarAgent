# ============================================================
#  OBD SuperStar Agent — Combined Dockerfile for Railway
#  Runs both backend (FastAPI) and frontend (Next.js) in one container
# ============================================================

# ── Stage 1: Build the Next.js frontend ──
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --prefer-offline
COPY frontend/ .

ARG BACKEND_URL=http://localhost:8000
ENV BACKEND_URL=$BACKEND_URL

RUN npm run build

# ── Stage 2: Final image with Python + Node ──
FROM python:3.11-slim

# Install Node.js for running the Next.js standalone server
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy sample products and docs
COPY sample_products/ ./sample_products/

# Copy built frontend (standalone output)
COPY --from=frontend-builder /app/frontend/.next/standalone ./frontend-standalone/
COPY --from=frontend-builder /app/frontend/.next/static ./frontend-standalone/.next/static
COPY --from=frontend-builder /app/frontend/public ./frontend-standalone/public

# Create outputs directory
RUN mkdir -p /app/backend/outputs

# Copy the startup script
COPY railway-start.sh ./railway-start.sh
RUN chmod +x railway-start.sh

EXPOSE 8000 3000

CMD ["./railway-start.sh"]
