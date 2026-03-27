# Utilisation d'une image légère mais complète
FROM python:3.11-slim

# Éviter les interactions pendant l'installation
ENV DEBIAN_FRONTEND=noninteractive

# Mise à jour et installation des dépendances système pour les navigateurs
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libx11-6 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# INSTALLATION CRUCIALE DES NAVIGATEURS PLAYWRIGHT
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

# Railway détecte automatiquement le port via la variable d'environnement PORT
CMD ["python", "app.py"]
