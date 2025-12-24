# finwise_scribe/frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy dependency definitions
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the port defined in vite.config.ts
EXPOSE 3000

# Start Vite in development mode
# We use --host to ensure Docker maps the port correctly to your machine
CMD ["npm", "run", "dev", "--", "--host"]