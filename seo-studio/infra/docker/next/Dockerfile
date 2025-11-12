# infra/docker/next/Dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package.json and package-lock.json
COPY ./seo-studio/apps/next/package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the Next.js application code
COPY ./seo-studio/apps/next .

# Expose the port the app runs on
EXPOSE 3000

# Start the app
CMD ["npm", "run", "dev"]
