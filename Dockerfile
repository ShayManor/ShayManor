FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY src/ ./static/

ENV PORT 8000
EXPOSE 8000
ENTRYPOINT ["sh", "-c", "gunicorn main:app --bind 0.0.0.0:$PORT"]

