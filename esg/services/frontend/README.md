# ESG Intelligence Platform - Frontend

Vue 3 frontend application for the ESG Intelligence Platform with TypeScript, Pinia, and Tailwind CSS.

## Tech Stack

- **Vue 3** with Composition API and `<script setup>`
- **TypeScript** for type safety
- **Bun** for fast package management and builds
- **Vite** for development and production builds
- **Vue Router** for client-side routing
- **Pinia** for state management
- **Tailwind CSS** for styling
- **Vitest** for unit testing

## Project Structure

```
src/
├── components/     # Reusable Vue components
├── composables/    # Composition API composables
├── stores/         # Pinia stores for state management
├── views/          # Page-level components
├── types/          # TypeScript type definitions
├── assets/         # Static assets and styles
├── router/         # Vue Router configuration
├── App.vue         # Root component
└── main.ts         # Application entry point
```

## Development

### Prerequisites

- Bun installed: https://bun.sh/

### Setup

```bash
# Install dependencies
bun install

# Copy environment variables
cp .env.example .env

# Start development server
bun run dev
```

The application will be available at http://localhost:5173

### Available Scripts

```bash
# Development server with hot-reload
bun run dev

# Type-check and build for production
bun run build

# Preview production build
bun run preview

# Run unit tests
bun run test

# Run tests in watch mode
bun run test:watch

# Lint and fix files
bun run lint

# Format code
bun run format
```

## Docker

### Build Docker Image

```bash
docker build -t esg-frontend .
```

### Run Container

```bash
docker run -p 80:80 esg-frontend
```

The application will be available at http://localhost

## Environment Variables

- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)

## Features

- **Company Dashboard**: View company ESG data and indicators
- **Score Visualization**: Transparent ESG score breakdown
- **Source Citations**: Click-through to PDF sources
- **Company Comparison**: Side-by-side comparison of multiple companies
- **Responsive Design**: Works on desktop and tablet devices

## Architecture

The frontend follows Vue 3 best practices:

- Composition API with `<script setup>` syntax
- TypeScript for type safety
- Pinia for centralized state management
- Composables for reusable logic
- Lazy-loaded routes for code splitting
- Tailwind CSS for utility-first styling

## API Integration

The frontend communicates with the FastAPI backend through the `/api` proxy configured in Vite and nginx.

## Production Deployment

The production build uses a multi-stage Docker build:

1. **Build stage**: Uses Bun to install dependencies and build the application
2. **Production stage**: Uses nginx to serve static files with optimized configuration

The nginx configuration includes:

- Gzip compression
- Static asset caching
- API proxy to backend
- SPA fallback routing
- Security headers
