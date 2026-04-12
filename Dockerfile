FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installer le navigateur Chromium et ses dépendances système
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]
