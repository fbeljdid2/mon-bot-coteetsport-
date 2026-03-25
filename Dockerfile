FROM ://mcr.microsoft.com

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Port utilisé par Railway
EXPOSE 5000

# Commande de lancement avec Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
