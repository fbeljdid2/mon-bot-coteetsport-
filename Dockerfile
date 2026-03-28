# Utilisation d'une image légère
FROM python:3.11-slim

# Éviter les interactions pendant l'installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Installation des dépendances système (Ta liste était parfaite)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg ca-certificates libnss3 libnspr4 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libdrm2 libgbm1 libasound2 \
    libpangocairo-1.0-0 libx11-6 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# INSTALLATION DES NAVIGATEURS (Chromium seulement pour gagner de la place)
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

# Railway utilise le port 8080 par défaut
ENV PORT 8080
EXPOSE 8080

# Lancer avec Gunicorn pour plus de stabilité avec Lovable
# --timeout 120 est crucial car le bot met du temps à cliquer sur MDJS
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "120", "app:app"]
RUN playwright install --with-deps chromium
