FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python -c "from web.db import init_db; init_db()"

EXPOSE 5000
CMD ["sh", "-c", "gunicorn web.app:app --bind 0.0.0.0:${PORT:-5000}"]
