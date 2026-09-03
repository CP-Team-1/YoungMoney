FROM node:22-alpine AS build

WORKDIR /app

COPY package*.json ./

ENV CYPRESS_INSTALL_BINARY=0

RUN npm ci --no-audit --no-fund

COPY . .

RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html