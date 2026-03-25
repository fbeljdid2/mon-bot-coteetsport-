# On utilise Python
FROM python:3.9-slim

# On installe Google Chrome et les outils pour le faire fonctionner sur un serveur
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    chromium \
    chromium-driver \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# On prépare le dossier de travail
WORKDIR /app
COPY . .

# On installe tes bibliothèques (Flask, Selenium...)
RUN pip install --no-cache-dir -r requirements.txt

# On lance le bot
CMD ["python", "main.py"]
