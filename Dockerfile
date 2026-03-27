FROM ://mcr.microsoft.com
WORKDIR /app
COPY package*.json ./
RUN npm install
# Cette ligne est CRUCIALE pour installer les navigateurs dans Railway
RUN npx playwright install --with-deps chromium
COPY . .
CMD ["node", "index.js"]
