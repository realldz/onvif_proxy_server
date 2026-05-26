FROM python:3.12-alpine

WORKDIR /app

COPY src/ /app/src/
COPY config.example.json /app/config.example.json

EXPOSE 5000/tcp
EXPOSE 3702/udp

ENV PYTHONPATH=/app

CMD ["python", "-m", "src.server", "-c", "/app/config.json"]
