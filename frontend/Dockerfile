# Flutter Web Dockerfile
# This uses a multi-stage build to compile Flutter and serve with nginx

# Stage 1: Build Flutter web app
FROM ghcr.io/cirruslabs/flutter:3.24.5 AS build

WORKDIR /app

# Copy pubspec files and get dependencies
COPY pubspec.* ./
RUN flutter pub get

# Copy the rest of the application
COPY . .

# Build for web (release mode)
RUN flutter build web --release --web-renderer canvaskit

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy built web app to nginx html directory
COPY --from=build /app/build/web /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 8080 (Cloud Run requirement)
EXPOSE 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
