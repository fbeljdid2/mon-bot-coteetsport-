FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
 wget gnupg2 libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
 libgbm1 libasound2 libxshmfence1 libx11-xcb1 libxcomposite1 \
 libxdamage1 libxrandr2 libpango-1.0-0 libcairo2 libcups2 \
 libxss1 libgtk-3-0 fonts-liberation \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium
COPY . .
CMD gunicorn app:app --bind 0.0.0.0:$PORT
