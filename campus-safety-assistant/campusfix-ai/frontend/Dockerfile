FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
# Note: In a production setup, we might copy a custom nginx config here,
# but for now we'll just use the default and let the root nginx container do the routing,
# or we can just expose port 80 and access it directly.
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
