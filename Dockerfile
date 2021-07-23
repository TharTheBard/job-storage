FROM python:3.8-slim-buster

MAINTAINER Stanislav Zoldak szoldak28@gmail.com

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt requirements.txt
RUN apt-get update \
    && apt-get -y install libpq-dev gcc
RUN pip install -r requirements.txt

COPY [".", "."]

ENTRYPOINT ["uwsgi", "--ini", "uwsgi.ini"]

# docker build . -t zoldak/job-storage:1.0