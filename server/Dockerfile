FROM python:3.13-slim

WORKDIR /app

RUN pip install --upgrade pip

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# For local development:
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# For production environment
# CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000"]