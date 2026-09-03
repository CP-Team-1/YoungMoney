FROM python:3.13-slim

WORKDIR /app

RUN pip install --upgrade pip

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Default CMD is the production server. docker-compose.yml overrides this
# with `manage.py runserver` for local dev (live reload); the prod compose
# override (docker-compose.prod.yml) leaves this default in place.
CMD ["gunicorn", "youngmoney.wsgi:application", "--bind", "0.0.0.0:8000"]