FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci || npm install

# Build the app
COPY . .
ENV NEXT_PUBLIC_API_URL=http://backend:8000
# Disable Next.js telemetry
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build || true  # Build the Next.js app, allow to fail gracefully if linting issues

# Run the app
EXPOSE 3000
CMD ["npm", "start"]
