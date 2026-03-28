FROM python:3.11-slim

# Installation des dépendances système pour Chromium
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxext6 libxfixes3 \
    libxrandr2 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installation de Chromium uniquement pour gagner de la place
RUN playwright install --with-deps chromium

COPY . .

CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app", "--timeout", "120"]
