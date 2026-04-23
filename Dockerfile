FROM python:3.12-slim

WORKDIR /app

COPY server.py .
COPY urban-terror-maps.html .
COPY votes.json .
COPY imgs/ ./imgs/

EXPOSE 8777

CMD ["python3", "server.py", "8777"]
