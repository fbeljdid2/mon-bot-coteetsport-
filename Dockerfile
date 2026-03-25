# 1. Utiliser Python
FROM python:3.9-slim

# 2. Installer les dépendances système pour le navigateur
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    librandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. Créer un dossier pour le bot
WORKDIR /app

# 4. Copier tes fichiers
COPY . .

# 5. Installer les bibliothèques Python
RUN pip install --no-cache-dir -r requirements.txt

# 6. Installer le navigateur Chrome pour le bot
RUN playwright install chromium

# 7. Lancer le bot
CMD ["python", "app.py"]
