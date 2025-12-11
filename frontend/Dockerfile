# Flutter Web Dockerfile
# Multi-stage build optimized for minimal image size
# Stage 1: Build stage - compile Flutter app
FROM ghcr.io/cirruslabs/flutter:3.24.5 AS builder

WORKDIR /build

# Copy only pubspec files first (better layer caching)
COPY pubspec.yaml pubspec.lock* ./

# Get dependencies
RUN flutter pub get --no-example

# Copy remaining source files (respects .dockerignore)
COPY lib/ ./lib/
COPY assets/ ./assets/
COPY web/ ./web/

# Build optimized web release
RUN flutter build web --release --web-renderer canvaskit --dart-define=FLUTTER_WEB_USE_SKIA=true

# Stage 2: Runtime stage - minimal nginx serving
FROM nginx:alpine

WORKDIR /usr/share/nginx/html

# Copy only the built web app (remove builder stage entirely)
COPY --from=builder /build/build/web .

# Copy nginx configuration for SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8080/index.html || exit 1

# Expose Cloud Run port
EXPOSE 8080

# Start nginx with appropriate signal handling
STOPSIGNAL SIGTERM
CMD ["nginx", "-g", "daemon off;"]
