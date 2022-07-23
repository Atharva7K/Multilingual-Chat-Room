# syntax=docker/dockerfile:1

FROM python:3.9.7-alpine

WORKDIR /python-docker

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt


COPY . .

CMD ["python", "server.py"]
