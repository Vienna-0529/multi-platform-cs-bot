FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir nanobot-ai

COPY . .

RUN mkdir -p /app/data /app/memory

CMD ["nanobot"]
