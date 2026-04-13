FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

COPY app.py .

CMD sh -c "gunicorn app:app --bind 0.0.0.0:${PORT:-8080} --timeout 180 --workers 1"
