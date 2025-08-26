FROM node:20-alpine

WORKDIR /usr/src/app

# Instala deps a partir dos manifests
COPY package*.json ./
RUN npm ci

# Copia o restante do código
COPY . .

# Porta do dev server (CRA usa 3000; Vite costuma usar 5173)
EXPOSE 3000

# CRA: "npm start" — Vite: "npm run dev"
CMD ["npm", "start"]

