FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir nanobot

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/memory

EXPOSE 8080

CMD ["python", "message_router.py"]
