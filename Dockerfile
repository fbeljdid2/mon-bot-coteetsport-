# Utiliser l'image Python officielle
FROM python:3.11-slim-bookworm

# Installer les dépendances système nécessaires pour Playwright
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatspi0 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# INSTALLER LES NAVIGATEURS PLAYWRIGHT
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

# Lancer votre application (ajoutez le port Railway)
CMD ["python", "app.py"]
