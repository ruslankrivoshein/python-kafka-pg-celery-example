FROM python:3.9-alpine

RUN apk update && \
    apk add --virtual .build-deps gcc \
                                  musl-dev \
                                  postgresql-dev

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN apk del .build-deps
