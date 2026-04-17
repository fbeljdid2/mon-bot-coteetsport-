FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Playwright inclut déjà Chromium + toutes les dépendances système

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installer les navigateurs Playwright (Chromium uniquement)
RUN playwright install chromium

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
