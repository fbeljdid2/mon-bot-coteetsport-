FROM python:3.9-slim

# Installation des outils nécessaires
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

# Installation des bibliothèques
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium --with-deps

# Commande exacte pour lancer le bot
CMD ["python", "app.py"]
